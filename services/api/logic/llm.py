import os
from groq import Groq

MANIM_PROMPT_TEMPLATE = """
You are a Manim animation expert. Your sole task is to generate a complete, runnable Manim script in a single Python code block.
The script must define a single class that inherits from 'manim.Scene'.
Do not add any comments, explanations, or markdown formatting like ```python.
Only output the raw Python code.

User Prompt: "{user_prompt}"
"""

def createGroqClient() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing. Please set it in your environment.")
    return Groq(api_key=api_key)


def generateManimCode(prompt: str, groqClient: Groq) -> str:
    full_prompt = MANIM_PROMPT_TEMPLATE.format(user_prompt=prompt)
    chat_completion = groqClient.chat.completions.create(
        messages=[{"role": "user", "content": full_prompt}],
        model="qwen/qwen3-32b",
    )
    if not chat_completion.choices:
        raise RuntimeError("No choices returned from Groq")
    message = chat_completion.choices[0].message.content
    if not message:
        raise RuntimeError("Groq returned an empty message")
    return message.strip()
