import os 
import re
import time
import subprocess
import tempfile
from dotenv import load_dotenv
from groq import Groq
import black

load_dotenv()

try:
    groqClient = Groq(api_key=os.getenv("GROQ_API_KEY"))
except Exception as e:
    print(f"CRITICAL ERROR: Failed to configure Groq client. Is your .env file set up correctly?")
    print(f"Error details: {e}")
    exit()

MANIM_PROMPT_TEMPLATE = """
You are a Manim animation expert. Your sole task is to generate a complete, runnable Manim script in a single Python code block.
The script must define a single class that inherits from 'manim.Scene'.
Do not add any comments, explanations, or markdown formatting like ```python.
Only output the raw Python code.

User Prompt: "{user_prompt}"
"""

def extractPythonCode(rawContent: str) -> str | None:
    cleaned = re.sub(r"<think>.*?</think>", "", rawContent, flags=re.DOTALL | re.IGNORECASE)
    fenced = re.findall(r"```(?:python)?(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    candidate = fenced[-1] if fenced else cleaned
    candidate = candidate.strip()
    return candidate or None

def generateManimCode(prompt: str) -> str | None:
    print("1. Generating code from LLM (Groq)...")
    try:
        fullPrompt = MANIM_PROMPT_TEMPLATE.format(user_prompt=prompt)
        chatCompletion = groqClient.chat.completions.create(
            messages=[{"role": "user", "content": fullPrompt}],
            model="qwen/qwen3-32b",
        )
        if not chatCompletion.choices:
            raise ValueError("No choices returned from Groq")

        rawResponse = chatCompletion.choices[0].message.content
        rawCode = extractPythonCode(rawResponse)
        if not rawCode:
            raise ValueError("LLM response did not contain usable code")
        print("  > LLM generation successful.")
        return rawCode
    except Exception as e:
        print(f"  > LLM generation failed: {e}")
        return None

def sanitizeCode(rawCode: str) -> str:
    print("2. Sanitizing code...")
    try:
        formattedCode = black.format_str(rawCode, mode=black.Mode())
        print("  > Code formatting successful.")
        return formattedCode
    except Exception as e:
        print(f"  > Warning: Black formatting failed. Proceeding with raw code. Error: {e}")
        return rawCode

def renderCode(cleanCode: str) -> str | None:
    print("3. Rendering code with Manim...")
    match = re.search(r"class\s+(\w+)\(Scene\):", cleanCode)
    if not match:
        print("  > Error: Could not find a class inheriting from 'Scene' in the code.")
        return None
    sceneName = match.group(1)
    print(f"  > Found Scene class: {sceneName}")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmpScript:
        scriptPath = tmpScript.name
        tmpScript.write(cleanCode)

    print(f"  > Running Manim on temporary script...")
    command = ["manim", scriptPath, sceneName, "-ql"]

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("  > Manim execution successful.")
        
        videoDir = os.path.join("media", "videos", os.path.basename(scriptPath).replace('.py', ''), "480p15")
        outputFile = os.path.join(videoDir, f"{sceneName}.mp4")

        if os.path.exists(outputFile):
            return outputFile
        else:
            print(f"  > Error: Manim ran, but the output file was not found at the expected path.")
            print(f"     Expected path: {outputFile}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"  > Error: Manim rendering failed.")
        print("\n--- MANIM ERROR LOG ---")
        print(e.stderr)
        print("-----------------------\n")
        return None
    finally:
        os.unlink(scriptPath)

if __name__ == "__main__":
    userPrompt = "Draw a circle and then have it transform into a square."
    
    print("-" * 50)
    print(f"Starting Playground Pipeline for prompt: '{userPrompt}'")
    print("-" * 50)
    
    startTime = time.time()
    
    rawCode = generateManimCode(userPrompt)
    if rawCode:
        print("\n[Raw Code from LLM]\n" + rawCode + "\n")
        cleanCode = sanitizeCode(rawCode)
        print("\n[Sanitized Code]\n" + cleanCode + "\n")
        videoPath = renderCode(cleanCode)
        if videoPath:
            endTime = time.time()
            print("\n" + "="*50)
            print("PIPELINE SUCCEEDED!")
            print(f"   Video saved to: {videoPath}")
            print(f"   Total time: {endTime - startTime:.2f} seconds")
            print("="*50)
        else:
            print("\nPIPELINE FAILED at rendering stage.")
    else:
        print("\nPIPELINE FAILED at LLM stage.")
