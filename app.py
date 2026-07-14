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
                    model='gemini-2.5-flash',
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
