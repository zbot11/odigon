import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def query_perplexity(company_name, website, prompt_template):
    """
    Query Perplexity API for a single company
    
    Args:
        company_name: Name of the company
        website: Company website URL
        prompt_template: Template string with {company_name} and {website} placeholders
    """
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
    PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Format the prompt with company details
    prompt = prompt_template.format(company_name=company_name, website=website)
    
    data = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        answer = result['choices'][0]['message']['content'].strip()
        
        # Extract just YES or NO from the response
        if "YES" in answer.upper():
            return "YES"
        elif "NO" in answer.upper():
            return "NO"
        else:
            return answer  # Return whatever was sent if neither YES nor NO found
    
    except requests.exceptions.RequestException as e:
        print(f"Error querying Perplexity for {company_name}: {e}")
        return None

# Test the function
if __name__ == "__main__":
    from config import PROMPTS
    
    # Test with a sample company
    test_result = query_perplexity(
        "Clarus Glassboards", 
        "https://www.clarus.com",
        PROMPTS['default']
    )
    print("Test result:", test_result)