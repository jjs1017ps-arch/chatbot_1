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
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "default_secret_key"

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

                # 메모리 유지 및 가독성을 위한 최신 대화 기록 슬라이싱 (인사말 제외 최대 6개 변환)
                recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
                
                contents_payload = []
                for chat in recent_history:
                    # 첫 환영 인사는 대화 맥락 혼선을 방지하기 위해 AI 전송 페이로드에서 제외
                    if "파주 삼릉' 방탈출 부스에 온 걸 환영해" in chat['text']:
                        continue
                    
                    role_name = "user" if chat['sender'] == 'user' else "model"
                    contents_payload.append(
                        types.Content(
                            role=role_name, 
                            parts=[types.Part.from_text(text=chat['text'])]
                        )
                    )

                # 구글 제미나이 3.1 라이트 호출
                response = client.models.generate_content(
                    model='gemini-3.1-flash-lite',
                    contents=contents_payload,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "너는 유네스코 세계유산 '파주 삼릉(공릉, 순릉, 영릉)' 방탈출 부스의 힌트 가이드봇이야.\n\n"
                            "1. 일상적인 인사나 대화는 친절하게 최대 '5문장 이내'로 자유롭게 대답해줘.\n"
                            "2. [힌트 마스킹 규칙]: 유저가 특정 퀴즈 문장을 물어보거나 단서를 요구할 때, '유저가 입력한 질문 문장 원문'에서 핵심 명사 딱 하나만 글자 일부를 '○'로 가려서 첫 줄에 그대로 출력해야 해.\n"
                            "   - 예시: 유저가 '공릉은 누구 무덤이야?' 라고 묻는다면 -> 첫 줄은 반드시 '공○은 누구 무덤이야?' 로 출력할 것.\n"
                            "   - 예시: 유저가 '삼릉이 뭐야' 라고 묻는다면 -> 첫 줄은 반드시 '○릉이 뭐야' 로 출력할 것.\n"
                            "   - 절대 너의 설명 문장이나 정답 해설 단어를 '삼○' 등으로 어설프게 마스킹하지 말고, 오직 '유저의 질문 텍스트'만 첫 줄에서 변형해.\n"
                            "   - 그 바로 아래 한 줄을 띄우고(줄바꿈), 유산에 얽힌 역사적 추가 도움 힌트/가이드 설명을 친절하게 덧붙여줘.\n"
                            "3. [정답 오픈 규칙]: 하지만 유저가 단서 유추에 실패하여 '정답을 직접 알려달라'고 강력하게 요구하거나 정답 유도 질문을 명시적으로 할 때는 가리지 말고 '정답'을 직접 아주 친절하게 알려주어야 해.\n"
                            "4. 어떤 경우에도 답변 전체의 길이는 가독성을 위해 '최대 5문장'을 절대로 넘기지 마."
                        ),
                        max_output_tokens=500, 
                        temperature=0.4 # 일관된 규칙 준수를 위해 온도를 살짝 낮춤
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
