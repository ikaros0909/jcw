import openai
import os
import requests
import json

# OpenAI API 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

# GIT API 설정
GIT_API_URL = "https://api.GITHUB.com"
REPO_OWNER = os.getenv('GITHUB_REPOSITORY_OWNER')
REPO_NAME = os.getenv('GITHUB_REPOSITORY').split('/')[-1]
GIT_TOKEN = os.getenv('GIT_TOKEN')

def analyze_code(file_path):
    with open(file_path, 'r') as file:
        code = file.read()
    
    response = openai.Completion.create(
      model="gpt-3.5-turbo-instruct", #text-davinci-004
      prompt=f"Analyze the following code and provide a detailed review in Korean.:\n{code}",
      max_tokens=500
    )
    
    return response.choices[0].text.strip()

def get_changed_files(pr_number):
    url = f"{GIT_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"token {GIT_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        files = response.json()
        return [file['filename'] for file in files]
    else:
        print(f"Failed to get changed files: {response.status_code}")
        print(response.json())
        return []

def post_comment_to_pr(pr_number, comment):
    url = f"{GIT_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GIT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "body": comment
    }
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        print("Comment posted successfully")
    else:
        print(f"Failed to post comment: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    pr_number = os.getenv('GITHUB_REF').split('/')[-1]  # PR 번호 가져오기

    changed_files = get_changed_files(pr_number)
    comments = []

    for file_path in changed_files:
        code_analysis = analyze_code(file_path)
        comments.append(f"### Analysis of `{file_path}`\n\n{code_analysis}")

    if comments:
        full_comment = "\n\n".join(comments)
        post_comment_to_pr(pr_number, full_comment)
