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
    # 사용자의 독립된 세션 대화 기록 저장소 유무 체크 및 초기화
    if 'history' not in session:
        # 방 개설과 동시에 자연스러운 챗봇의 첫 스타팅 인사를 주머니에 넣어줍니다.
        session['history'] = [
            {
                'sender': 'bot', 
                'text': "🌍 안녕! 반가워~! 나는 유네스코 동아리 부스의 가이드야. 축제 게임 퀴즈를 풀다가 막히는 부분이 생기거나 힌트가 필요하면 나에게 언제든 물어봐! 😊✨"
            }
        ]
    
    chat_history = session['history']
    
    # 클라이언트로부터 POST 요청(메시지 전송)이 인입된 경우
    if request.method == 'POST':
        user_message = request.form.get('message', '').strip()
        
        if user_message:
            chat_history.append({'sender': 'user', 'text': user_message})
            
            try:
                user_ip = request.remote_addr  
                
                # 서버 로그 기록
                print(f"\n🛸 [INCOMING_REQUEST - GEMINI] ──────────────────────")
                print(f"📡 IP-Address : {user_ip}")
                print(f"💬 User_Query : {user_message}")
                print(f"⏳ Status     : Generating Gemini AI response...")
                print(f"───────────────────────────────────────────────────")

                # Google GenAI 모델 추론 요청 발송 (황금 밸런스 힌트 지침 적용)
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "너는 유네스코 동아리 부스의 친절한 가이드이자, 방탈출 게임의 힌트 제공자야. "
                            "1. 평소 인삿말이나 가벼운 대화, 유네스코에 대한 기본 질문은 친구처럼 친절하고 다정하게 받아줘. "
                            "2. 하지만 유저가 게임의 '정답'이나 '힌트'를 대놓고 요구하면, 절대로 정답을 바로 말하지 마. "
                            "은유적인 단서나 수수께끼만 짤막하게 던져서 유저가 스스로 추리하게 유도해. "
                            "3. 답변이 너무 길어지면 안 되므로, 모든 답변은 친절하되 무조건 '최대 2~3문장 이내'로 핵심만 짤막하게 대답해줘."
                        ),
                        max_output_tokens=250, 
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

    # 렌더링 엔진을 통해 템플릿 파일로 데이터 바인딩 후 클라이언트로 스트리밍 응답
    return render_template('index.html', history=chat_history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
