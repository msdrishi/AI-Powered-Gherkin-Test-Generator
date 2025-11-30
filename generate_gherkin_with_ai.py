import json
import os
from groq import Groq
from dotenv import load_dotenv

def safe_print(message):
    """Print with safe encoding for Windows console"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Remove emojis and special characters for Windows console
        print(message.encode('ascii', 'ignore').decode('ascii'))

def load_prompt_template():
    """Load the AI prompt template from markdown file"""
    prompt_file = "Gherkin_Prompt.md"
    
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Error: {prompt_file} not found. Please create the prompt file.")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read()

def generate_gherkin_with_groq(json_file_path):
    """Generate Gherkin scenarios using Groq AI"""
    
    load_dotenv()
    
    # Load credentials from .env
    api_key = os.getenv("GROQ_API_KEY")
    model_name = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
    max_tokens = int(os.getenv("MAX_TOKENS", "8000"))
    
    if not api_key:
        safe_print("Error: GROQ_API_KEY not found in .env file")
        return None
    
    # Load scan results
    with open(json_file_path, 'r', encoding='utf-8') as f:
        scan_data = json.load(f)
    
    # Load system prompt from markdown file
    try:
        system_prompt = load_prompt_template()
    except FileNotFoundError as e:
        safe_print(str(e))
        return None
    
    # Prepare user message with JSON data
    user_message = f"""
Based on the following JSON scan results, generate Gherkin test scenarios:

{json.dumps(scan_data, indent=2)}

Generate the Gherkin feature file now.
"""
    
    safe_print("Generating Gherkin scenarios...")
    
    try:
        client = Groq(api_key=api_key)
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            model=model_name,
            temperature=0.1,
            max_tokens=max_tokens,
            top_p=0.85,
        )
        
        gherkin_content = response.choices[0].message.content.strip()
        
        # Minimal cleanup
        if "Feature:" in gherkin_content and not gherkin_content.startswith("Feature:"):
            gherkin_content = gherkin_content[gherkin_content.find("Feature:"):]
        
        # Save to file
        with open('ai_generated_scenarios.feature', 'w', encoding='utf-8') as f:
            f.write(gherkin_content)
        
        safe_print("Scenarios generated: ai_generated_scenarios.feature")
        
        return gherkin_content
        
    except Exception as e:
        safe_print(f"Error: {e}")
        return None


if __name__ == "__main__":
    generate_gherkin_with_groq("scan_results.json")