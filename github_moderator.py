import os
import sys
import requests
import json
from openai import OpenAI

def get_issue_details():
    """Extract context from GitHub Action environment."""
    event_path = os.getenv('GITHUB_EVENT_PATH')
    with open(event_path, 'r', encoding='utf-8') as f:
        event_data = json.load(f)
    
    issue = event_data.get('issue', event_data.get('pull_request'))
    if not issue:
        print("No issue or pull request found in event.")
        sys.exit(0)
    
    return {
        'number': issue['number'],
        'title': issue.get('title', 'No Title'),
        'body': issue.get('body', 'No Description'),
        'user': issue['user']['login'],
        'url': issue['comments_url']
    }

def generate_ai_response(details):
    """Generate a professional, literary response using OpenAI."""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    system_prompt = (
        "You are 'Antigravity Support', a highly professional, literary, and polite assistant "
        "for the 'Universal AI Orchestrator' project by TymurJan. "
        "Your task is to respond to GitHub Issues or Pull Requests. "
        "Style: Professional, helpful, slightly futuristic, and respectful. "
        "If the user asks a question, answer it based on the project goal (AI Governance). "
        "If it's a bug report, thank them and say the team will investigate. "
        "If it's a feature request, express interest and say it will be reviewed. "
        "Respond in the language of the user (English or Ukrainian)."
    )
    
    user_prompt = f"User @{details['user']} wrote:\nTitle: {details['title']}\nBody: {details['body']}"
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

def post_comment(url, body):
    """Post the AI response back to GitHub."""
    token = os.getenv('GH_TOKEN')
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {'body': body}
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print("Successfully posted comment.")
    else:
        print(f"Failed to post comment: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    try:
        details = get_issue_details()
        print(f"Processing Issue #{details['number']} from @{details['user']}...")
        
        reply = generate_ai_response(details)
        print("Generated AI response.")
        
        post_comment(details['url'], reply)
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)
 Greenland
