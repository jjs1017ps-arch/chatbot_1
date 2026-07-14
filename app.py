import sys
import subprocess

# 라이브러리 부재 시 자동 탐색 및 설치 스크립트
def auto_install_packages():
    required_packages = {"flask": "flask", "python-dotenv": "dotenv", "google-genai": "google.genai"}
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

auto_install_packages()

import os
from flask import Flask, render_template, request, session
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

@app.route('/', methods=['GET', 'POST'])
def home():
    if 'history' not in session:
        session['history'] = []
    chat_history = session['history']

    if request.method == 'POST':
        user_message = request.form.get('message', '').strip()
        if user_message:
            chat_history.append({'sender': 'user', 'text': user_message})
            try:
                user_ip = request.remote_addr # 접속 기기 IP 수집 (내부망이라 완전 안전)

                # ⭐ 힙한 개발자 감성 터미널 로그 인쇄
                print(f"\n🛸 [INCOMING_REQUEST - GEMINI] ──────────────────────")
                print(f"📡 IP-Address : {user_ip}")
                print(f"💬 User_Query : {user_message}")
                print(f"⏳ Status     : Generating Gemini AI response...")
                print(f"───────────────────────────────────────────────────")

                # app.py의 제미나이 호출 부분에 덮어쓰기 하세요!
response = client.models.generate_content(
    model='gemini-3.5-flash',
    contents=user_message,
    config=types.GenerateContentConfig(
        # 1. 일상 대화는 허용하되, 힌트 제공 시 규칙과 글자 수 제한을 엄격히 둡니다.
        system_instruction=(
            "너는 유네스코 동아리 부스의 친절한 가이드이자, 방탈출 게임의 힌트 제공자야. "
            "1. 평소 인삿말이나 가벼운 대화, 유네스코에 대한 기본 질문은 친구처럼 친절하고 다정하게 받아줘. "
            "2. 하지만 유저가 게임의 '정답'이나 '힌트'를 대놓고 요구하면, 절대로 정답을 바로 말하지 마. "
            "은유적인 단서나 수수께끼만 짤막하게 던져서 유저가 스스로 추리하게 유도해해. "
            "3. 답변이 너무 길어지면 안 되므로, 모든 답변은 친절하되 무조건 '최대 2~3문장 이내'로 핵심만 짤막하게 대답해줘."
        ),
        # 2. 글자 수 상한선을 한글 100~120자 내외로 넉넉하면서도 확실하게 제한!
        # 이 설정 덕분에 AI가 신나서 길게 뽑는 걸 막고 응답 속도가 1~2초대로 엄청나게 빨라집니다.
        max_output_tokens=250, 
        # 3. 대화의 자연스러움과 규칙 준수의 균형을 맞추는 적당한 창의력 설정
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
                chat_history.append({'sender': 'bot', 'text': f"제미나이 연결 오류: {str(e)}"})

            session['history'] = chat_history
            session.modified = True
    return render_template('index.html', history=chat_history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
