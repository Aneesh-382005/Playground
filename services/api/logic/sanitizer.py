import re
import black

class CodeValidationError(Exception):
    pass

def extractPythonCode(rawContent: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", rawContent, flags=re.DOTALL | re.IGNORECASE)

    # 1) Preferred: explicit markers. Ask model to return the full file BETWEEN these markers.
    marker = re.search(r"###\s*CODE_START\s*###(.*?)###\s*CODE_END\s*###", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if marker:
        candidate = marker.group(1).strip()
        if not candidate:
            raise CodeValidationError("LLM response contained code markers but no code between them.")
        return candidate

    # 2) Next, look for fenced code blocks (prefer the longest block)
    fenced = re.findall(r"```(?:python)?(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidates = [f.strip() for f in fenced if f.strip()]
        if candidates:
            candidate = max(candidates, key=len)
            return candidate

    # 3) Try to find a class inheriting from Scene and return from there to the end
    class_match = re.search(r"(class\s+\w+\s*\(\s*(?:Scene|manim\.Scene)\s*\):[\s\S]*)", cleaned)
    if class_match:
        candidate = class_match.group(1).strip()
        if candidate:
            return candidate

    # 4) Fallback: use the whole cleaned response
    candidate = cleaned.strip()
    if not candidate:
        raise CodeValidationError("LLM response did not contain any usable code.")
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

def lintCode(codeString: str):
    try:
        compile(codeString, "<string>", "exec")
    except SyntaxError as e:
        raise CodeValidationError(f"Code failed syntax check: {e.msg} on line {e.lineno}")

def sanitizeAndValidateCode(rawLlmContent: str) -> str:
    try:
        rawCode = extractPythonCode(rawLlmContent)
        wrappedCode = ensureManimScene(rawCode)
        
        formattedCode = black.format_str(wrappedCode, mode=black.Mode())
        lintCode(formattedCode)
        return formattedCode

    except black.NothingChanged:
        lintCode(wrappedCode)
        return wrappedCode
    
    except (CodeValidationError, Exception) as e:
        print(f"Validation failed: {e}")
        raise e
