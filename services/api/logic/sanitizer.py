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
    importsModule = re.search(r"\bimport\s+manim\b", rawCode)
    importsFrom = re.search(r"\bfrom\s+manim\s+import\b", rawCode)
    usesManimPrefix = "manim." in rawCode

    needModuleImport = usesManimPrefix and not importsModule
    needStarImport = not (importsModule or importsFrom)

    codeBody = rawCode
    if not hasScene:
        lines = rawCode.splitlines()
        indented = "\n".join(("        " + ln) if ln.strip() else "" for ln in lines)
        codeBody = f"class GeneratedScene(Scene):\n    def construct(self):\n{indented}\n"

    prelude: list[str] = []
    if needModuleImport:
        prelude.append("import manim")
    if needStarImport:
        prelude.append("from manim import *")

    return ("\n".join(prelude) + "\n\n" if prelude else "") + codeBody


def sanitizeCode(rawContent: str) -> str:
    rawCode = extractPythonCode(rawContent)
    wrappedCode = ensureManimScene(rawCode)
    try:
        return black.format_str(wrappedCode, mode=black.Mode())
    except Exception:
        return wrappedCode
