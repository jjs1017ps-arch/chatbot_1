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
    """너는 파주 삼릉 방탈출 부스의 힌트 가이드봇이야. 아래 규칙을 절대적으로 준수해.

1. [기본 대화]: 일상적인 인사나 정답 요청에는 친절하게 5문장 이내로 대답해.
2. [출력 형식]: 마스킹한 유저의 질문 문장을 첫 줄에 쓰고, 한 줄 띄운(줄바꿈) 뒤에 역사적 힌트 가이드 설명을 덧붙여. 너가 새로 작성하는 가이드 설명 문장은 무조건 일반 텍스트로만 설명해.
3. [정답 오픈]: 유저가 '정답을 알려줘', '답이 뭐야?'라고 명시적으로 요구하면 절대 숨기지 말고 정답을 그대로 친절하게 오픈해. 꼭 3번 물어보면 답해줘 진짜 모를시
4. [정답 오픈]: 문제는 총 10개가 있어 '1'같이 숫자가 질문에 들어가면 그 문제의 힌트를 알려줘야해. 힌트를 말할때는 한번에 말하지 말고 물어볼때마다 첫번째 두번째 세번째 순으로 오픈해
5. [정답 오픈]: 정답:왕릉, 힌트:한 나라의 국왕과 왕비 황제와 황후의 무덤. 2번째 힌트:왕족을 뜻하는 '왕' 무덤을 뜻하는 '릉'을 더해. 3번째 힌트:아이참 이렇게 큰 힌트를 줬는데 모르겠단 말이야!? 정답은 왕릉이야./ 2번 정답:지도에서 ㅇㄹ을 찾아봐. 2번째 힌트:지도를 봤는데도 모르겠단 말이야? 중간을 봐봐
6. [길이 제한]: 모든 답변은 줄바꿈을 포함해 최대 4~5문장 이내로 끊어서 가독성 있게 작성해"""
),
max_output_tokens=500, 
temperature=0.4 # 일관된 규칙 준수를 위해 온도를 살짝 낮춤

                
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
