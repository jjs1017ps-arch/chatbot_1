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

                # Google GenAI 모델 추론 요청 발송 (200자 내외 대화형 설정)
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "너는 유네스코 동아리 부스의 다정하고 똑똑한 가이드야. "
                            "사용자와 친구처럼 자연스럽고 친절하게 일상적인 대화를 나눠줘. "
                            "단, 사용자가 지루하지 않도록 모든 답변은 장황한 설명 없이 "
                            "핵심만 담아 무조건 '3문장 이내'로 짤막하고 명확하게 대답해야 해."
                        ),
                        # 💡 한글 기준 약 150~200자 내외에서 답변이 강제로 끊기도록 제한합니다.
                        # 이 설정 덕분에 AI가 길게 생각하지 않아 응답 속도가 1~2초대로 대폭 단축됩니다!
                        max_output_tokens=300, 
                        temperature=0.7 
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
