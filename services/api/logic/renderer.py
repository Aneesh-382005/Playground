import os
import re
import subprocess
import tempfile
from typing import Optional


def _preflightManimCode(cleanCode: str) -> None:
    if re.search(r"\b(?:self|Scene)\.get_mobject\s*\(", cleanCode):
        raise RuntimeError("Manim preflight failed: scene lookup helpers like get_mobject are not supported. Store mobjects in local variables and reuse them directly.")

    if re.search(r"Triangle\s*\([^\)]*\bside_length\s*=", cleanCode):
        raise RuntimeError("Manim preflight failed: Triangle does not accept side_length. Create Triangle() and scale it afterward if needed.")

    if re.search(r"self\.play\s*\(\s*[^\)]*\bget_mobject\s*\(", cleanCode):
        raise RuntimeError("Manim preflight failed: self.play cannot use scene lookup helpers. Store the mobject in a variable first.")


def renderCode(cleanCode: str) -> Optional[str]:
    _preflightManimCode(cleanCode)

    match = re.search(r"class\s+(\w+)\(\s*(?:Scene|manim\.Scene)\s*\):", cleanCode)
    if not match:
        raise RuntimeError("Could not find a class inheriting from 'Scene' in the code")
    sceneName = match.group(1)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmpScript:
        scriptPath = tmpScript.name
        tmpScript.write(cleanCode)

    command = ["manim", scriptPath, sceneName, "-ql"]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        videoDir = os.path.join("media", "videos", os.path.basename(scriptPath).replace(".py", ""), "480p15")
        outputFile = os.path.join(videoDir, f"{sceneName}.mp4")
        if not os.path.exists(outputFile):
            raise RuntimeError(f"Manim ran, but the output file was not found at {outputFile}")
        return outputFile
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr or "Manim rendering failed") from exc
    finally:
        os.unlink(scriptPath)
