from playwithDataset import loadAndInspectSample
from codeFormatting import FormatCode # Import our function

rawCodeSample = loadAndInspectSample()

cleanedCode = FormatCode(rawCodeSample)


with open("formatting_results.txt", "w") as f:
    f.write("--- BEFORE FORMATTING ---\n")
    f.write(rawCodeSample)
    f.write("\n-------------------------\n\n")
    f.write("--- AFTER FORMATTING ---\n")
    f.write(cleanedCode)
    f.write("\n------------------------")
