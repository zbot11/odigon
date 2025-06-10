import os
import requests
from dotenv import load_dotenv

load_dotenv()

def find_website(company_name, city, state):
    """
    Query Perplexity API to find company website only
    """
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
    PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prompt = f"""Search the internet for the company {company_name} located in {city}, {state}.
Find their official website URL.

IMPORTANT: Respond with ONLY the website URL. Nothing else. If no website is found, respond with NONE."""
    
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
        content = result['choices'][0]['message']['content'].strip()
        
        # Clean up the response
        if content.upper() == "NONE" or not content:
            return None
        else:
            # Remove any extra text, just get the URL
            # Sometimes the response might have extra words
            words = content.split()
            for word in words:
                if word.startswith('http://') or word.startswith('https://') or 'www.' in word:
                    return word
            # If no http/www found, assume the whole response is the URL
            if len(content) < 100:  # URLs shouldn't be too long
                return content
        
        return None
    
    except requests.exceptions.RequestException as e:
        print(f"Error finding website for {company_name}: {e}")
        return None

# Test the function
if __name__ == "__main__":
    # Test with a sample company
    test_website = find_website("Ashley Furniture", "Arcadia", "Wisconsin")
    print(f"Website found: {test_website}")