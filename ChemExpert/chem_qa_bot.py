import pandas as pd
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables (allows loading AP_KEY from a .env file)
load_dotenv()

def get_api_key():
    """Retrieves API key from environment or user input."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OpenAI API Key not found in .env file.")
        api_key = input("Please enter your OpenAI API Key: ").strip()
    return api_key

def ask_chatgpt(client, question):
    """Sends a question to ChatGPT and returns the answer."""
    if not question or pd.isna(question):
        return ""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Using a cost-effective model
            messages=[
                {"role": "system", "content": "You are a friendly and knowledgeable Egyptian chemistry teacher. Answer questions in **Egyptian Colloquial Arabic (اللهجة المصرية العامية)**. Your tone should be brotherly and supportive (like an older brother), but professional and serious about the scientific content (avoid excessive joking). Explain concepts clearly and simply."},
                {"role": "user", "content": str(question)}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    # 1. Setup
    api_key = get_api_key()
    if not api_key:
        print("No API Key provided. Exiting.")
        return
    
    client = OpenAI(api_key=api_key)
    
    input_file = 'chemistry_questions.xlsx'
    output_file = input_file # Overwrite the same file as requested

    # 2. Check for input file
    if not os.path.exists(input_file):
        print(f"❌ '{input_file}' not found.")
        print("Creating a sample file for you...")
        data = {
            'Question': [
                "What is the chemical formula for Sulfuric Acid?",
                "Explain the difference between ionic and covalent bonds.",
                "What happens when you mix Sodium with Water?"
            ]
        }
        df = pd.DataFrame(data)
        df.to_excel(input_file, index=False)
        print(f"✅ Created '{input_file}'. You can run the script again to process it, or edit it to add more questions.")
        return

    # 3. Read Data
    print(f"Reading '{input_file}'...")
    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    if 'Question' not in df.columns:
        print("❌ Error: The Excel file must have a column named 'Question'.")
        print(f"Found columns: {list(df.columns)}")
        return

    # 4. Process Questions
    print("Starting to answer questions... (Press Ctrl+C to stop)")
    
    # Create Answer column if it doesn't exist
    if 'Answer' not in df.columns:
        df['Answer'] = ""

    total = len(df)
    for index, row in df.iterrows():
        question = row['Question']
        existing_answer = row['Answer']
        
        # Skip if already answered
        if existing_answer and not pd.isna(existing_answer) and str(existing_answer).strip() != "":
             print(f"[{index+1}/{total}] Skipped (Already answered)")
             continue

        print(f"[{index+1}/{total}] Q: {question}")
        answer = ask_chatgpt(client, question)
        print(f"   -> A: {answer[:100]}..." if len(answer) > 100 else f"   -> A: {answer}")
        
        df.at[index, 'Answer'] = answer

    # 5. Save Results
    try:
        df.to_excel(output_file, index=False)
        print(f"\n✅ Success! Answers saved to '{output_file}'")
    except PermissionError:
        print(f"\n❌ Error: Could not save to '{output_file}'. Is the file open in Excel?")
        print("Tip: Close the Excel file and run the script again.")
        # Try saving to a backup file
        backup_file = "chemistry_questions_backup.xlsx"
        df.to_excel(backup_file, index=False)
        print(f"Saved to '{backup_file}' instead.")
    except Exception as e:
        print(f"\n❌ Error saving file: {e}")

if __name__ == "__main__":
    main()
