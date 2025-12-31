import re
import black

def extractPythonCode(rawContent: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", rawContent, flags=re.DOTALL | re.IGNORECASE)
    fenced = re.findall(r"```(?:python)?(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    candidate = fenced[-1] if fenced else cleaned
    candidate = candidate.strip()
    if not candidate:
        raise ValueError("LLM response did not contain usable code")
    return candidate


def ensureManimScene(rawCode: str) -> str:
    hasScene = re.search(r"class\s+\w+\(\s*(?:Scene|manim\.Scene)\s*\):", rawCode)
    hasImport = re.search(r"from\s+manim\s+import|import\s+manim", rawCode)

    code = rawCode
    if not hasScene:
        header = "from manim import *\n\n" if not hasImport else ""
        lines = rawCode.splitlines()
        indented = "\n".join(("        " + ln) if ln.strip() else "" for ln in lines)
        code = f"{header}class GeneratedScene(Scene):\n    def construct(self):\n{indented}\n"
    elif not hasImport:
        code = "from manim import *\n" + rawCode

    return code


def sanitizeCode(rawContent: str) -> str:
    rawCode = extractPythonCode(rawContent)
    wrappedCode = ensureManimScene(rawCode)
    try:
        return black.format_str(wrappedCode, mode=black.Mode())
    except Exception:
        return wrappedCode
