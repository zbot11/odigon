import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def query_perplexity(company_name, website):
    """
    Query Perplexity API for a single company
    """
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
    PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Search the internet for the company {company_name}, website {website} and determine if the company is a home furnishings manufacturer or not. 

A home furnishings manufacturer must meet ALL of these criteria:
- They must MANUFACTURE (not just retail) furniture
- The furniture must be for HOME/RESIDENTIAL use (not commercial, office, or institutional)
- They must make furniture like sofas, chairs, tables, beds, dressers, or other residential furniture
- They are NOT just cabinetry, casework, mattresses only, or building materials

Examples that should be YES: Albany Industries (upholstery), Intermountain Furniture (residential furniture), Bernhardt Design (home furniture)

Examples that should be NO:
- Kitchen/bathroom cabinet makers (like cabinetry companies)
- Office furniture manufacturers
- Retailers who don't manufacture
- Companies that only make mattresses/box springs
- Glass/building material companies
- Commercial/institutional furniture only

IMPORTANT: Respond with ONLY the single word YES or NO. Do not include any explanation."""
    
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
    # Test with a sample company that should be YES
    test_result = query_perplexity("Clarus Glassboards", "https://www.clarus.com")
    print("Test result:", test_result)