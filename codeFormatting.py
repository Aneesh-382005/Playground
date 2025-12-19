
from playwithDataset import loadAndInspectSample
import black

def FormatCode(codeString: str) -> str:
    """
    Takes a raw Python code string and formats it using Black.

    Args:
        codeString: A string containing Python code.

    Returns:
        A formatted code string. Returns the original string if formatting fails.
    """
    try:
        mode = black.Mode()
        formattedCode = black.format_str(codeString, mode=mode)
        return formattedCode
    except black.NothingChanged:
        return codeString
    except Exception as e:
        print(f"Error formatting code: {e}")
        return codeString  # Return original
