import os
import re
import time
from groq import Groq
from dotenv import load_dotenv
from services.api.logic.sanitizer import sanitizeAndValidateCode, CodeValidationError
load_dotenv()
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

User Prompt: "{user_prompt}"
"""

def createGroqClient() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Please set it in your environment.")
    return Groq(api_key=api_key)


def generateManimCode(prompt: str, groqClient: Groq) -> str:
    full_prompt = MANIM_PROMPT_TEMPLATE.format(user_prompt=prompt)

    def call_groq(prompt_text: str):
        return groqClient.chat.completions.create(
            messages=[{"role": "user", "content": prompt_text}],
            model="qwen/qwen3-32b",
        )

    resp = call_groq(full_prompt)
    if not resp.choices:
        raise RuntimeError("No choices returned from Groq")
    message = resp.choices[0].message.content or ""

    # Strip any LLM internal tags that sometimes appear
    cleaned = re.sub(r"<think>.*?</think>", "", message, flags=re.DOTALL | re.IGNORECASE).strip()

    # First, try to sanitize and validate the LLM output immediately
    try:
        validated = sanitizeAndValidateCode(cleaned)
        return validated
    except Exception as first_exc:
        # Attempt a single automated retry: ask the model to return only corrected code
        retry_prompt = (
            full_prompt
            + "\n\nThe previous response could not be parsed or validated."
            + f"\nError: {str(first_exc)}\n"
            + "Please return ONLY a corrected, runnable Manim Python source file (no markdown or explanation)."
            + " Return the complete file as raw Python code."
            + "\nPrevious response:\n" + cleaned
        )

        resp2 = call_groq(retry_prompt)
        if not resp2.choices:
            raise RuntimeError("No choices returned from Groq on retry")
        message2 = resp2.choices[0].message.content or ""
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
