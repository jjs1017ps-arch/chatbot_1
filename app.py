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
# 3. 비즈니스 로직 (삼릉 마스킹 + 정답 허용 조건 추가)
# ─────────────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'history' not in session:
        session['history'] = [
            {
                'sender': 'bot', 
                'text': "🌳 안녕! 유네스코 세계유산 '파주 삼릉' 방탈출 부스에 온 걸 환영해! 단서가 필요하거나 퀴즈를 풀다가 막히면 언제든 나에게 질문해줘! 😊✨"
            }
        ]
    
    chat_history = session['history']
    
    if request.method == 'POST':
        user_message = request.form.get('message', '').strip()
        
        if user_message:
            chat_history.append({'sender': 'user', 'text': user_message})
            
            try:
                user_ip = request.remote_addr  
                print(f"\n🛸 [SAMNEUNG_QUEST] IP: {user_ip} | Q: {user_message}")

                # 최신 대화 기록 슬라이싱 (토큰 아끼기)
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
                        # 💡 [정답 오픈 규칙 허용] 지침을 업데이트했습니다.
                        system_instruction=(
                            "너는 유네스코 세계유산 '파주 삼릉(공릉, 순릉, 영릉)' 방탈출 부스의 힌트 가이드봇이야. "
                            "1. 일상적인 인사나 대화는 친절하게 최대 '5문장 이내'로 자유롭게 나눠줘. "
                            "2. [힌트 마스킹 규칙]: 유저가 특정 퀴즈 문장을 복사해서 붙여넣거나, 단순히 '이거 뭐임?'이라며 단서를 요구할 때는 절대로 정답 단어를 통째로 다 보여주면 안 돼. "
                            "유저가 물어본 핵심 단어의 일부분을 반드시 '○' 기호로 가려서 노출하고(예: 삼릉 -> ○릉 / 문화유산 -> 문화○산), 그 바로 아래 줄바꿈을 한 뒤 유산에 얽힌 역사적 추가 도움 가이드 설명을 덧붙여줘. "
                            "3. [정답 오픈 규칙]: 하지만 유저가 단서 유추에 실패하여 '정답을 직접 알려달라'고 강력하게 요구하거나 정답 유도 질문을 명시적으로 할 때는, 숨기지 말고 정답을 친절하게 직접 알려주어야 해. "
                            "4. 어떤 경우에도 답변 전체의 길이는 가독성을 위해 '최대 5문장'을 절대로 넘기지 마."
                        ),
                        max_output_tokens=500, 
                        temperature=0.6 
                    )
                )
                
                bot_reply = response.text
                chat_history.append({'sender': 'bot', 'text': bot_reply})
                print(f"✨ [QUEST_SUCCESS] 🤖 Ans: {bot_reply}\n")
                
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
