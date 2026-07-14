import sys
import subprocess

# ─────────────────────────────────────────────────────────────
# 1. 의존성 패키지 자동 설치 로직
# ─────────────────────────────────────────────────────────────
def auto_install_packages():
    required_packages = {
        "flask": "flask",
        "python-dotenv": "dotenv",
        "google-genai": "google.genai"
    }
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

auto_install_packages()

# ─────────────────────────────────────────────────────────────
# 2. 웹 서버 및 AI 인스턴스 초기화
# ─────────────────────────────────────────────────────────────
import os
from flask import Flask, render_template, request, session, make_response
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# ─────────────────────────────────────────────────────────────
# 3. 비즈니스 로직 (2~3줄 숏폼 대화 세팅)
# ─────────────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'history' not in session:
        session['history'] = [
            {
                'sender': 'bot', 
                'text': "🌍 안녕! 유네스코 동아리 가이드야. 궁금한 점이 있다면 무엇이든 편하게 물어봐! 😊✨"
            }
        ]
    
    chat_history = session['history']
    
    if request.method == 'POST':
        user_message = request.form.get('message', '').strip()
        
        if user_message:
            chat_history.append({'sender': 'user', 'text': user_message})
            
            try:
                user_ip = request.remote_addr  
                
                print(f"\n🛸 [INCOMING_REQUEST - GEMINI 3.1 LITE] ─────────────")
                print(f"📡 IP-Address : {user_ip}")
                print(f"💬 User_Query : {user_message}")
                print(f"⏳ Status     : Generating Gemini AI response...")
                print(f"───────────────────────────────────────────────────")

                # 최신 대화 기록 4개 슬라이싱 (토큰 아끼기)
                recent_history = chat_history[-5:] if len(chat_history) > 5 else chat_history
                
                contents_payload = []
                for chat in recent_history:
                    role_name = "user" if chat['sender'] == 'user' else "model"
                    contents_payload.append(types.Content(role=role_name, parts=[types.Part.from_text(text=chat['text'])]))

                # 구글 제미나이 3.1 라이트 호출
                response = client.models.generate_content(
                    model='gemini-3.1-flash-lite',
                    contents=contents_payload,
                    config=types.GenerateContentConfig(
                        # ⚠️ 설명충 기질을 완벽하게 압수하는 초강력 인스트럭션 주입
                        system_instruction=(
                            "너는 유네스코 동아리 부스의 친절한 가이드야. "
                            "모든 답변은 완벽한 한국어로 작성하고, 가독성을 위해 무조건 '2~3문장 이내'로 핵심만 극도로 짧게 대답해줘. "
                            "인사말이나 배경 설명을 길게 늘어놓지 말고, 묻는 말에 대한 직관적인 핵심 정답만 한두 줄로 요약해. "
                            "카카오톡 하듯이 부드럽고 다정하게 말하되, 문장이 절대로 길어지면 안 돼."
                        ),
                        # 💡 글자 상한선 그릇을 200으로 확 줄여서 물리적으로 길게 나오는 것을 원천 봉쇄!
                        # 글자 수가 줄어들면 연산 속도가 비약적으로 빨라집니다!
                        max_output_tokens=200, 
                        temperature=0.6 
                    )
                )
                
                bot_reply = response.text
                chat_history.append({'sender': 'bot', 'text': bot_reply})
                
                print(f"✨ [RESPONSE_SUCCESS] ──────────────────────────────")
                print(f"🤖 Gemini Ans : {bot_reply}")
                print(f"🔒 Session    : Room Secured.")
                print(f"───────────────────────────────────────────────────\n")
                
            except Exception as e:
                print(f"\n❌ [SYSTEM_ERROR] ──────────────────────────────────")
                print(f"⚠️ Details    : {str(e)}")
                print(f"───────────────────────────────────────────────────\n")
                chat_history.append({'sender': 'bot', 'text': f"API 통신 오류가 발생했습니다: {str(e)}"})
            
            session['history'] = chat_history
            session.modified = True

    return render_template('index.html', history=chat_history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
import sys
import subprocess

# ─────────────────────────────────────────────────────────────
# 1. 의존성 패키지 자동 설치 로직 (Auto-Dependency Installer)
# ─────────────────────────────────────────────────────────────
def auto_install_packages():
    """런타임 환경에 필수 라이브러리가 부재할 경우 자동 설치 프로세스를 수행합니다."""
    required_packages = {
        "flask": "flask",
        "python-dotenv": "dotenv",
        "google-genai": "google.genai"
    }
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

auto_install_packages()

# ─────────────────────────────────────────────────────────────
# 2. 메인 웹 서버 및 AI 모델 인스턴스 초기화
# ─────────────────────────────────────────────────────────────
import os
from flask import Flask, render_template, request, session, make_response
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# ─────────────────────────────────────────────────────────────
# 3. HTTP 라우팅 및 챗봇 인터랙션 비즈니스 로직
# ─────────────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def home():
    """기본 엔드포인트 핸들러: 세션 관리 및 비동기적 폼 데이터 처리"""
    if 'history' not in session:
        session['history'] = [
            {
                'sender': 'bot', 
                'text': "🌍 안녕! 반가워~! 나는 유네스코 동아리 부스의 똑똑한 가이드야. 세계유산이나 문화 다양성에 대해 궁금한 점이 있다면 무엇이든 편하게 물어봐! 😊✨"
            }
        ]
    
    chat_history = session['history']
    
    if request.method == 'POST':
        user_message = request.form.get('message', '').strip()
        
        if user_message:
            chat_history.append({'sender': 'user', 'text': user_message})
            
            try:
                user_ip = request.remote_addr  
                
                print(f"\n🛸 [INCOMING_REQUEST - GEMINI] ──────────────────────")
                print(f"📡 IP-Address : {user_ip}")
                print(f"💬 User_Query : {user_message}")
                print(f"⏳ Status     : Generating Gemini AI response...")
                print(f"───────────────────────────────────────────────────")

                # Google GenAI 모델 추론 요청 발송 (풍부하고 다정한 황금 분량 세팅)
                response = client.models.generate_content(
                    model='gemini-3.1-flash-lite',
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "너는 유네스코 동아리 부스의 다정하고 박식한 고등학교 가이드야. "
                            "사용자의 질문에 성의 있고 친절하게 대화식으로 답변해줘. "
                            "답변을 할 때는 핵심 정보와 흥미로운 비유를 포함하여 "
                            "한글 기준 보통 '4~5문장 내외'로 풍부하고 정성스럽게 구성해줘. "
                            "절대로 로봇처럼 한두 단어로 단답형 처리를 하거나, 반대로 너무 길어서 "
                            "가독성을 해치는 백과사전식 장문 폭탄을 던지지는 마."
                        ),
                        # 💡 글자 수 제한을 600토큰(한글 약 300~400자)으로 넉넉하게 확장합니다!
                        # 이 수치가 너무 낮으면 AI가 말을 하려다 중간에 뚝 끊겨 버립니다.
                        max_output_tokens=600, 
                        # 0.8로 설정하여 답변의 흐름을 훨씬 풍부하고 자연스럽게 유도합니다.
                        temperature=0.8 
                    )
                )
                
                bot_reply = response.text
                chat_history.append({'sender': 'bot', 'text': bot_reply})
                
                print(f"✨ [RESPONSE_SUCCESS] ──────────────────────────────")
                print(f"🤖 Gemini Ans : {bot_reply}")
                print(f"🔒 Session    : Room Secured.")
                print(f"───────────────────────────────────────────────────\n")
                
            except Exception as e:
                print(f"\n❌ [SYSTEM_ERROR] ──────────────────────────────────")
                print(f"⚠️ Details    : {str(e)}")
                print(f"───────────────────────────────────────────────────\n")
                chat_history.append({'sender': 'bot', 'text': f"API 통신 오류가 발생했습니다: {str(e)}"})
            
            session['history'] = chat_history
            session.modified = True

    return render_template('index.html', history=chat_history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
