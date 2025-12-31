import time
from dotenv import load_dotenv

from modules.llm import createGroqClient, generateManimCode
from modules.sanitizer import sanitizeCode
from modules.renderer import renderCode


def main() -> None:
    userPrompt = "Draw a circle and then have it transform into a square."
    print("-" * 50)
    print(f"Starting Playground Pipeline for prompt: '{userPrompt}'")
    print("-" * 50)

    startTime = time.time()

    try:
        groqClient = createGroqClient()
    except Exception as exc:
        print(f"CRITICAL ERROR: Failed to configure Groq client. {exc}")
        return

    try:
        rawResponse = generateManimCode(userPrompt, groqClient)
        print("\n[Raw Response]\n" + rawResponse + "\n")
        cleanCode = sanitizeCode(rawResponse)
        print("\n[Sanitized Code]\n" + cleanCode + "\n")
        videoPath = renderCode(cleanCode)
    except Exception as exc:
        print(f"PIPELINE FAILED: {exc}")
        return

    endTime = time.time()
    print("\n" + "=" * 50)
    print("PIPELINE SUCCEEDED!")
    print(f"   Video saved to: {videoPath}")
    print(f"   Total time: {endTime - startTime:.2f} seconds")
    print("=" * 50)


if __name__ == "__main__":
    load_dotenv()
    main()
