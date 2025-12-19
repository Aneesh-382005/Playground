from datasets import load_dataset

def loadAndInspectSample():
    """
    Loads the manim-codegen dataset from Hugging Face and inspects a raw code sample.
    """
    # Load the dataset
    print("Loading dataset...")
    dataset = load_dataset("generaleoley/manim-codegen", split="train")


    rawCodeSample = dataset[0]['answer'].strip()
        
    return rawCodeSample

if __name__ == "__main__":
    rawCodeSample = loadAndInspectSample()
    print("--- RAW CODE SAMPLE ---")
    print(rawCodeSample)
    print("-----------------------")