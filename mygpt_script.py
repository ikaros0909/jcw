import time
import openai
import os
import requests
from dotenv import load_dotenv
from functools import wraps
import threading
import errno
import chardet

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
REPO_NAME = os.getenv('GITHUB_REPOSITORY', 'owner/repo').split('/')[-1]
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

MAX_RETRIES = 3
TIMEOUT_SECONDS = 300

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout():
            raise TimeoutError(error_message)
        
        def wrapper(*args, **kwargs):
            timer = threading.Timer(seconds, _handle_timeout)
            timer.start()
            try:
                result = func(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        
        return wraps(func)(wrapper)
    
    return decorator

def retry_with_backoff(max_retries=MAX_RETRIES, initial_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (openai.error.RateLimitError, requests.exceptions.RequestException) as e:
                    print(f"Error: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
            raise Exception(f"Failed to complete the operation after {max_retries} attempts.")
        return wrapper
    return decorator

@timeout(TIMEOUT_SECONDS)
@retry_with_backoff()
def analyze_code(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            code = file.read()
    except UnicodeDecodeError:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            print(f"{file_path} 파일의 인코딩을 감지했습니다: {encoding}")
            code = raw_data.decode(encoding)
    
    print(f"{file_path} 파일의 코드를 분석 중입니다.")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 코드 리뷰어입니다."},
            {"role": "user", "content": f"다음 코드를 분석하고 상세한 리뷰를 제공해 주세요:\n{code}"}
        ],
        max_tokens=500,
        timeout=15  # 타임아웃 설정 (초)
    )
    result = response.choices[0].message['content'].strip()
    
    # 모델 결과 검증
    if "Error" in result or not result:
        raise ValueError("Invalid analysis result")
    
    return result

@timeout(TIMEOUT_SECONDS)
@retry_with_backoff()
def generate_witty_comment():
    print("재치 있는 코멘트를 생성 중입니다...")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 재치 있는 댓글 작성자입니다."},
            {"role": "user", "content": "코딩에 대한 재치 있는 코멘트를 작성해 주세요:"}
        ],
        max_tokens=60,
        timeout=15  # 타임아웃 설정 (초)
    )
    result = response.choices[0].message['content'].strip()
    
    # 모델 결과 검증
    if "Error" in result or not result:
        raise ValueError("Invalid comment result")
    
    return result

@timeout(TIMEOUT_SECONDS)
@retry_with_backoff()
def get_changed_files(pr_number):
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/files"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    print(f"요청 URL: {url}")
    response = requests.get(url, headers=headers, timeout=15)  # 타임아웃 설정 (초)
    print(f"응답 상태 코드: {response.status_code}")
    if response.status_code == 200:
        files = response.json()
        return [file['filename'] for file in files]
    else:
        print(f"변경된 파일 목록을 가져오는 데 실패했습니다: {response.status_code}")
        print(response.json())
        raise ValueError("Failed to get changed files")

@timeout(TIMEOUT_SECONDS)
@retry_with_backoff()
def post_comment_to_pr(pr_number, comment):
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "body": comment
    }
    response = requests.post(url, json=data, headers=headers, timeout=15)  # 타임아웃 설정 (초)
    print(f"PR #{pr_number}에 코멘트를 게시합니다")
    print(f"요청 URL: {url}")
    print(f"요청 헤더: {headers}")
    print(f"요청 데이터: {data}")
    print(f"응답 상태 코드: {response.status_code}")
    if response.status_code == 201:
        print("코멘트가 성공적으로 게시되었습니다")
    else:
        print(f"코멘트 게시 실패: {response.status_code}")
        print(response.json())
        raise ValueError("Failed to post comment")

if __name__ == "__main__":
    try:
        # 환경 변수 출력 (디버깅용)
        print(f"GITHUB_REPOSITORY_OWNER: {REPO_OWNER}")
        print(f"GITHUB_REPOSITORY: {REPO_NAME}")
        print(f"GITHUB_REF: {os.getenv('GITHUB_REF')}")

        # PR 번호 가져오기
        pr_number = os.getenv('GITHUB_REF').split('/')[-2]
        print(f"추출된 PR 번호: {pr_number}")

        # 변경된 파일 목록 가져오기
        changed_files = get_changed_files(pr_number)
        comments = []

        # 각 파일에 대해 코드 분석 수행
        for file_path in changed_files:
            code_analysis = analyze_code(file_path)
            witty_comment = generate_witty_comment()
            comments.append(f"### `{file_path}` 파일 분석\n\n{code_analysis}\n\n**재치 있는 코멘트**: {witty_comment}")

        # 분석 결과 PR에 코멘트로 추가
        if comments:
            full_comment = "\n\n".join(comments)
            post_comment_to_pr(pr_number, full_comment)
    except TimeoutError as e:
        print(f"프로세스가 타임아웃되었습니다: {e}")
    except Exception as e:
        print(f"메인 프로세스에서 예상치 못한 오류 발생: {e}")
