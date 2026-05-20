import json
import os
import re
import time
import urllib.error
import urllib.request
from groq import Groq
from dotenv import load_dotenv
from services.api.logic.sanitizer import sanitizeAndValidateCode, CodeValidationError
load_dotenv()
MODEL_NAMES = {
    "groq": "qwen/qwen3-32b",
    "nvidia": "google/gemma-2-2b-it",
}
NVIDIA_CHAT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MANIM_PROMPT_TEMPLATE = """
You are a Manim Community Edition v0.18.0 expert whose only job is to produce
safe, minimal, and runnable Manim Python code. Follow these rules exactly.

Output rules:
- Return ONLY a single Python source file as raw code (no markdown, no prose).
- The file must define exactly one class that inherits from `manim.Scene`.
- Do NOT include multiple classes that are used as helpers which return None.
- All factory/insert functions must return the created Manim mobject (never `None`).
- Avoid complex custom data structures; prefer simple lists/tuples and clear names.
- Do not access the filesystem, network, or environment variables.

Code style and safety:
- Use only `from manim import *` or `import manim` for imports; avoid third-party
    imports unless absolutely necessary.
- Keep the scene short and deterministic: total run time <= 10 seconds.
- Use explicit sizes/positions; avoid randomization or external assets.
- Keep the scene minimal: no more than 6 top-level mobjects created.
- Use only supported Manim constructor arguments. For example, `Triangle()`
    does not accept `side_length`; scale the object after creating it instead.
- Keep object references in local variables; do not use scene lookup helpers
    like `self.get_mobject(...)` or `Scene.get_mobject(...)`.
- Do not access mobjects by numeric index or string lookup from the scene.
  Store each mobject in a variable and reuse that variable directly.
- Avoid using `self.play` inside deeply nested helper functions; calls to
    `self.play` should be inside `construct()` or clearly documented inline.
- Do NOT pass bound methods to `self.play` (e.g., `mobj.set_color`);
    use `mobj.animate.set_color(...)` or `ApplyMethod` instead.

Failure-resilience:
- Ensure functions that create or return mobjects always return a Mobject
    (e.g., `return circle`), and validate before returning.
- If constructing a connection/line between two mobjects, assume both
    inputs are valid mobjects and handle missing operands safely.

Formatting:
- Provide type hints where simple and useful. Keep code runnable under Python 3.11.
- Keep the overall file under ~200 lines.

Now generate a runnable Manim scene that implements the user request below.
IMPORTANT: Wrap the COMPLETE Python source file between these exact markers
so it can be reliably extracted by the pipeline:

###CODE_START###
<your python file here>
###CODE_END###

Return NOTHING outside these markers.

User Prompt: "{user_prompt}"
"""

def createGroqClient() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Please set it in your environment.")
    return Groq(api_key=api_key)


def generateManimCode(prompt: str, groqClient: Groq | None = None, provider: str = "groq") -> str:
    provider_key = provider.lower().strip()
    model_name = MODEL_NAMES.get(provider_key)
    if not model_name:
        raise ValueError(f"Unsupported provider: {provider}")

    if provider_key == "groq" and groqClient is None:
        groqClient = createGroqClient()

    full_prompt = MANIM_PROMPT_TEMPLATE.format(user_prompt=prompt)

    def extract_message_content(response: object) -> tuple[bool, str]:
        if isinstance(response, dict):
            choices = response.get("choices") or []
            if not choices:
                return False, ""
            message = choices[0].get("message") or {}
            return True, message.get("content") or ""

        choices = getattr(response, "choices", None) or []
        if not choices:
            return False, ""
        return True, choices[0].message.content or ""

    def call_model(prompt_text: str):
        if provider_key == "groq":
            if groqClient is None:
                raise RuntimeError("Groq client is not available.")
            return groqClient.chat.completions.create(
                messages=[{"role": "user", "content": prompt_text}],
                model=model_name,
            )

        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError("NVIDIA_API_KEY is missing. Please set it in your environment.")

        request = urllib.request.Request(
            NVIDIA_CHAT_URL,
            data=json.dumps(
                {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": 0.01,
                    "top_p": 0.1,
                    "max_tokens": 4096,
                    "stream": False,
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"NVIDIA request failed: {exc.code} {error_body}") from exc

        return payload

    resp = call_model(full_prompt)
    has_choices, message = extract_message_content(resp)
    if not has_choices:
        raise RuntimeError(f"No choices returned from {provider_key}")

    # Strip any LLM internal tags that sometimes appear
    cleaned = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL | re.IGNORECASE).strip()

    # First, try to sanitize and validate the LLM output immediately
    try:
        validated = sanitizeAndValidateCode(cleaned)
        return validated
    except Exception as first_exc:
        # Attempt a single automated retry: ask the model to return only corrected code
        # Ask for a focused retry. Include the validation error and request the
        # corrected file strictly between the ###CODE_START### / ###CODE_END### markers.
        retry_prompt = (
            full_prompt
            + "\n\nThe previous response could not be parsed or validated."
            + f"\nValidation error: {str(first_exc)}\n"
            + "Please return ONLY the corrected, runnable Manim Python source file."
            + " Wrap the entire file between the markers exactly as shown:"
            + "\n###CODE_START###\n<python file>\n###CODE_END###\n"
            + "Do NOT include any surrounding prose or markdown."
            + "\nPrevious response:\n" + cleaned
        )

        resp2 = call_model(retry_prompt)
        has_choices2, message2 = extract_message_content(resp2)
        if not has_choices2:
            raise RuntimeError(f"No choices returned from {provider_key} on retry")
        cleaned2 = re.sub(r"<think>.*?</think>", "", message2, flags=re.DOTALL | re.IGNORECASE).strip()

        try:
            validated2 = sanitizeAndValidateCode(cleaned2)
            return validated2
        except Exception as second_exc:
            # Save debug artifacts to media/debug with timestamp for inspection
            debug_dir = os.path.join("media", "debug")
            os.makedirs(debug_dir, exist_ok=True)
            ts = int(time.time())
            raw_path = os.path.join(debug_dir, f"raw_response_{ts}.txt")
            err_path = os.path.join(debug_dir, f"validation_error_{ts}.txt")
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write("--- ORIGINAL RESPONSE ---\n")
                f.write(message)
                f.write("\n\n--- CLEANED FIRST ATTEMPT ---\n")
                f.write(cleaned)
                f.write("\n\n--- RETRY RESPONSE ---\n")
                f.write(message2)
                f.write("\n\n--- CLEANED SECOND ATTEMPT ---\n")
                f.write(cleaned2)

            with open(err_path, "w", encoding="utf-8") as f:
                f.write("First validation error:\n")
                f.write(str(first_exc))
                f.write("\n\nSecond validation error:\n")
                f.write(str(second_exc))

            raise RuntimeError(
                "Failed to produce valid Manim code after retry. "
                f"Debug files: {raw_path}, {err_path}"
            )


def repairManimCode(
    prompt: str,
    previous_code: str,
    render_error: str,
    groqClient: Groq | None = None,
    provider: str = "groq",
) -> str:
    provider_key = provider.lower().strip()
    model_name = MODEL_NAMES.get(provider_key)
    if not model_name:
        raise ValueError(f"Unsupported provider: {provider}")

    if provider_key == "groq" and groqClient is None:
        groqClient = createGroqClient()

    render_hints = []
    lower_error = render_error.lower()
    if "get_mobject" in lower_error:
        render_hints.append(
            "Do not call self.get_mobject or any scene lookup helper. Use the local mobject variables you create."
        )
    if "side_length" in lower_error and "triangle" in lower_error:
        render_hints.append(
            "Triangle does not accept side_length. Create Triangle() and then scale it if needed."
        )
    if "bound method" in lower_error or "set_color" in lower_error:
        render_hints.append(
            "Do not pass bound methods to self.play. Use .animate or ApplyMethod instead."
        )

    repair_prompt = (
        MANIM_PROMPT_TEMPLATE.format(user_prompt=prompt)
        + "\n\nThe previous code rendered with a Manim error."
        + f"\nRender error: {render_error}\n"
        + "Return a corrected full file that avoids the same issue."
        + " Keep the scene minimal and use only supported Manim APIs."
        + ("\nSpecific fixes to apply:\n- " + "\n- ".join(render_hints) if render_hints else "")
        + "\nPrevious code:\n"
        + previous_code
    )

    def extract_message_content(response: object) -> tuple[bool, str]:
        if isinstance(response, dict):
            choices = response.get("choices") or []
            if not choices:
                return False, ""
            message = choices[0].get("message") or {}
            return True, message.get("content") or ""

        choices = getattr(response, "choices", None) or []
        if not choices:
            return False, ""
        return True, choices[0].message.content or ""

    def call_model(prompt_text: str):
        if provider_key == "groq":
            if groqClient is None:
                raise RuntimeError("Groq client is not available.")
            return groqClient.chat.completions.create(
                messages=[{"role": "user", "content": prompt_text}],
                model=model_name,
            )

        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError("NVIDIA_API_KEY is missing. Please set it in your environment.")

        request = urllib.request.Request(
            NVIDIA_CHAT_URL,
            data=json.dumps(
                {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt_text}],
                    "temperature": 0.01,
                    "top_p": 0.1,
                    "max_tokens": 4096,
                    "stream": False,
                }
            ).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"NVIDIA request failed: {exc.code} {error_body}") from exc

        return payload

    resp = call_model(repair_prompt)
    has_choices, message = extract_message_content(resp)
    if not has_choices:
        raise RuntimeError(f"No choices returned from {provider_key} during render fix")

    cleaned = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL | re.IGNORECASE).strip()
    return sanitizeAndValidateCode(cleaned)
