import re
import black

class CodeValidationError(Exception):
    pass

def extractPythonCode(rawContent: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", rawContent, flags=re.DOTALL | re.IGNORECASE)
    fenced = re.findall(r"```(?:python)?(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    candidate = fenced[-1] if fenced else cleaned
    candidate = candidate.strip()
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
