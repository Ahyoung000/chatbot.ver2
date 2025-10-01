# 교과서재 (敎科書齋) - AI 교과과정 연계 도서 추천 챗봇
'교과서재'는 선생님들께서 담당하시는 수업의 학년, 학기, 과목에 맞는 교육과정 키워드를 기반으로, 알라딘 API와 Gemini 2.5 Flash AI를 활용하여 윤독도서를 추천해주는 Streamlit 웹 애플리케이션입니다.

🚀 시작하기
이 프로젝트를 Codespace에서 실행하고 외부로 공유하기 위한 안내입니다.

1. 초기 설정
가. API 키 준비

프로젝트를 실행하려면 알라딘과 Google Gemini API 키가 필요합니다.

프로젝트의 루트 디렉토리(app.py가 있는 곳)에 .env 파일을 생성합니다.

아래 형식에 맞게 발급받은 API 키를 파일에 입력하고 저장합니다.

ALADIN_TTB_KEY="여기에_발급받은_알라딘_TTBKey를_입력하세요"
GEMINI_API_KEY="여기에_발급받은_Gemini_API_Key를_입력하세요"

나. 파이썬 라이브러리 설치

터미널을 열고 아래 명령어를 실행하여 필요한 모든 파이썬 라이브러리를 설치합니다.

pip install -r requirements.txt

2. 챗봇 실행하기 (로컬)
모든 설정이 완료되면, 터미널에서 아래 명령어를 입력하여 Streamlit 챗봇을 실행합니다.

streamlit run app.py

🚇 Cloudflare Tunnel로 외부 공유하기
로컬에서 실행 중인 챗봇을 다른 사람에게 공유하려면 Cloudflare Tunnel을 사용해야 합니다.

1. Cloudflare Tunnel 설치 (최초 1회)
아직 cloudflared가 설치되지 않았다면, 터미널에 아래 명령어를 순서대로 입력하여 설치합니다.

# 패키지 다운로드
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# 패키지 설치
sudo dpkg -i cloudflared-linux-amd64.deb

2. Cloudflare 계정 인증 (최초 1회)
설치 후, 아래 명령어를 실행하여 Codespace와 나의 Cloudflare 계정을 연결합니다.

cloudflared tunnel login

터미널에 나타나는 안내에 따라 웹 브라우저에서 로그인을 완료하고 "Authorize" 버튼을 클릭하세요.

3. 터널 실행하여 공유하기
중요: 챗봇 공유를 위해서는 2개의 터미널을 동시에 사용해야 합니다.

가. 1번 터미널: 챗봇 실행

먼저 챗봇 서버를 켭니다.

streamlit run app.py

나. 2번 터미널: 터널 실행

새로운 터미널을 열고 아래 명령어를 실행하여 외부 접속 URL을 생성합니다.

cloudflared tunnel --url http://localhost:8501

명령어 실행 후, 터미널에 나타나는 .trycloudflare.com으로 끝나는 주소를 복사하여 다른 사람에게 공유하면 됩니다.

⚠️ 주의: 공유가 유지되려면 1번과 2번 터미널이 모두 켜져 있어야 합니다.