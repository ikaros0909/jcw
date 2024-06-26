import openai
import os
import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 출력 (디버깅용)
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")
print(f"GITHUB_TOKEN: {os.getenv('GITHUB_TOKEN')}")
print(f"GITHUB_REPOSITORY_OWNER: {os.getenv('GITHUB_REPOSITORY_OWNER')}")
print(f"GITHUB_REPOSITORY: {os.getenv('GITHUB_REPOSITORY')}")
print(f"GITHUB_REF: {os.getenv('GITHUB_REF')}")

# OpenAI API 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

# GitHub API 설정
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = os.getenv('GITHUB_REPOSITORY_OWNER')
REPO_NAME = os.getenv('GITHUB_REPOSITORY').split('/')[-1]
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

def analyze_code(file_path):
    with open(file_path, 'r') as file:
        code = file.read()
    
    response = openai.Completion.create(
      model="gpt-4-turbo",
      prompt=f"Analyze the following code and provide a detailed review:\n{code}",
      max_tokens=500
    )
    
    return response.choices[0].text.strip()

def generate_witty_comment():
    response = openai.Completion.create(
      model="gpt-4-turbo",
      prompt="Provide a witty comment about coding:",
      max_tokens=60
    )
    
    return response.choices[0].text.strip()

def get_changed_files(pr_number):
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    print(f"Request URL: {url}")
    response = requests.get(url, headers=headers)
    print(f"Response Status Code: {response.status_code}")
    if response.status_code == 200:
        files = response.json()
        return [file['filename'] for file in files]
    else:
        print(f"Failed to get changed files: {response.status_code}")
        print(response.json())
        return []

def post_comment_to_pr(pr_number, comment):
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "body": comment
    }
    response = requests.post(url, json=data, headers=headers)
    print(f"Posting comment to PR #{pr_number}")
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")
    print(f"Request Data: {data}")
    print(f"Response Status Code: {response.status_code}")
    if response.status_code == 201:
        print("Comment posted successfully")
    else:
        print(f"Failed to post comment: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    # 환경 변수 출력 (디버깅용)
    print(f"GITHUB_REPOSITORY_OWNER: {REPO_OWNER}")
    print(f"GITHUB_REPOSITORY: {REPO_NAME}")
    print(f"GITHUB_REF: {os.getenv('GITHUB_REF')}")

    # PR 번호 가져오기
    pr_number = os.getenv('GITHUB_REF').split('/')[-2]
    print(f"Extracted PR number: {pr_number}")

    # 변경된 파일 목록 가져오기
    changed_files = get_changed_files(pr_number)
    comments = []

    # 각 파일에 대해 코드 분석 수행
    for file_path in changed_files:
        code_analysis = analyze_code(file_path)
        witty_comment = generate_witty_comment()
        comments.append(f"### Analysis of `{file_path}`\n\n{code_analysis}\n\n**Witty Comment**: {witty_comment}")

    # 분석 결과 PR에 코멘트로 추가
    if comments:
        full_comment = "\n\n".join(comments)
        post_comment_to_pr(pr_number, full_comment)
