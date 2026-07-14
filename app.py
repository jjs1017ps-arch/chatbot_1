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

                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        # 💡 [내가 바꿀 수 있는 부분]: 챗봇의 성격이나 말투 수정 가능
                        system_instruction="너는 유네스코 동아리의 친절한 가이드 챗봇이야. 세계유산과 문화 다양성에 대해 청소년의 눈높이에 맞춰 쉽고 친절하게 설명해줘."
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
