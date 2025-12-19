# Goal: Test our new format_code function from the sanitizer module.
from playwithDataset import loadAndInspectSample
from codeFormatting import FormatCode # Import our function

# 1. Load the dataset
rawCodeSample = loadAndInspectSample()

# 2. Print the raw code
print("--- BEFORE FORMATTING ---")
print(rawCodeSample)
print("-------------------------\n")

# 3. Format the code using our sanitizer
cleanedCode = FormatCode(rawCodeSample)

# 4. Print the cleaned code
print("--- AFTER FORMATTING ---")
print(cleanedCode)
print("------------------------")
