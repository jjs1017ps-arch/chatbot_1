```python
import sys
import subprocess


# ============================================================
# 1. 필요한 패키지 자동 설치
# ============================================================

def auto_install_packages():
    required_packages = {
        "flask": "flask",
        "python-dotenv": "dotenv",
        "google-genai": "google.genai",
    }

    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"📦 {package_name} 설치 중...")
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                package_name
            ])


auto_install_packages()


# ============================================================
# 2. 라이브러리 불러오기
# ============================================================

import os

from flask import Flask, render_template, request, session
from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# 3. 환경변수 및 Flask 설정
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY") or "default_secret_key"

client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


# ============================================================
# 4. Gemini 시스템 프롬프트
# ============================================================

SYSTEM_INSTRUCTION = """
너는 파주 삼릉 방탈출 부스의 힌트 가이드봇이야.
아래 규칙을 반드시 준수해.

[1. 기본 대화]
일상적인 인사나 정답 요청에는 친절하게 5문장 이내로 대답해.

[2. 출력 형식]
마스킹한 유저의 질문 문장을 첫 줄에 쓰고,
한 줄 띄운 뒤 역사적 힌트 가이드 설명을 덧붙여.

새로 작성하는 가이드 설명 문장은 일반 텍스트로만 작성해.

[3. 정답 공개]
유저가 "정답을 알려줘", "답이 뭐야?"라고 명시적으로 요구하면
정답을 숨기지 말고 그대로 친절하게 알려줘.

단, 사용자가 정말 모르겠다고 하거나 여러 번 질문하면
힌트를 단계적으로 제공해.

[4. 문제 번호]
문제는 총 10개가 있어.

유저의 질문에 문제 번호가 포함되어 있다면
해당 문제의 힌트를 알려줘.

힌트는 한 번에 전부 공개하지 말고,
질문할 때마다 다음 순서로 단계적으로 공개해.

1번째 질문 → 1번째 힌트
2번째 질문 → 2번째 힌트
3번째 질문 → 3번째 힌트

[5. 문제 및 힌트]

1번 문제
정답: 왕릉
1번째 힌트:
한 나라의 국왕과 왕비, 황제와 황후의 무덤.

2번째 힌트:
왕족을 뜻하는 '왕'과 무덤을 뜻하는 '릉'을 더해.

3번째 힌트:
아이참, 이렇게 큰 힌트를 줬는데 모르겠단 말이야!?
정답은 왕릉이야.

2번 문제
1번째 힌트:
지도에서 ㅇㄹ을 찾아봐.

2번째 힌트:
지도를 봤는데도 모르겠단 말이야?
중간을 봐봐.

[6. 답변 길이]
모든 답변은 줄바꿈을 포함하여 최대 4~5문장 이내로 작성해.

[7. 중요]
사용자가 단순히 대화하는 경우에는 자연스럽게 대답하고,
방탈출 문제와 관련된 질문이라면 위의 힌트 규칙을 우선적으로 적용해.
"""


# ============================================================
# 5. 메인 페이지
# ============================================================

@app.route("/", methods=["GET", "POST"])
def home():

    # --------------------------------------------------------
    # 대화 기록이 없으면 기본 환영 메시지 추가
    # --------------------------------------------------------

    if "history" not in session:
        session["history"] = [
            {
                "sender": "bot",
                "text": (
                    "🌳 안녕! 유네스코 세계유산 '파주 삼릉' "
                    "방탈출 부스에 온 걸 환영해! "
                    "단서가 필요하거나 퀴즈를 풀다가 막히면 "
                    "언제든 나에게 질문해줘! 😊✨"
                ),
            }
        ]

    chat_history = session["history"]


    # ========================================================
    # POST 요청 처리
    # ========================================================

    if request.method == "POST":

        user_message = request.form.get("message", "").strip()

        if user_message:

            # ------------------------------------------------
            # 유저 메시지 저장
            # ------------------------------------------------

            chat_history.append({
                "sender": "user",
                "text": user_message
            })

            try:

                # ------------------------------------------------
                # 접속 IP 출력
                # ------------------------------------------------

                user_ip = request.remote_addr

                print(
                    f"\n🛸 [SAMNEUNG_QUEST] "
                    f"IP: {user_ip} | Q: {user_message}"
                )


                # ------------------------------------------------
                # 최근 대화 6개만 사용
                # ------------------------------------------------

                recent_history = (
                    chat_history[-6:]
                    if len(chat_history) > 6
                    else chat_history
                )


                # ------------------------------------------------
                # Gemini에 전달할 대화 내용 생성
                # ------------------------------------------------

                contents_payload = []

                for chat in recent_history:

                    # 기본 환영 메시지는 Gemini에게 전달하지 않음
                    if "파주 삼릉' 방탈출 부스에 온 걸 환영해" in chat["text"]:
                        continue

                    role_name = (
                        "user"
                        if chat["sender"] == "user"
                        else "model"
                    )

                    contents_payload.append(
                        types.Content(
                            role=role_name,
                            parts=[
                                types.Part.from_text(
                                    text=chat["text"]
                                )
                            ]
                        )
                    )


                # ====================================================
                # Gemini API 호출
                # ====================================================

                response = client.models.generate_content(

                    model="gemini-3.1-flash-lite",

                    contents=contents_payload,

                    config=types.GenerateContentConfig(

                        system_instruction=SYSTEM_INSTRUCTION,

                        max_output_tokens=500,

                        temperature=0.4,
                    ),
                )


                # ------------------------------------------------
                # AI 답변 저장
                # ------------------------------------------------

                bot_reply = response.text

                chat_history.append({
                    "sender": "bot",
                    "text": bot_reply
                })


                print(
                    f"✨ [QUEST_SUCCESS] "
                    f"🤖 Ans: {bot_reply}\n"
                )


            # ====================================================
            # 오류 처리
            # ====================================================

            except Exception as e:

                print(
                    "\n❌ [SYSTEM_ERROR] "
                    "──────────────────────────────────"
                )

                print(f"⚠️ Details : {str(e)}")

                print(
                    "──────────────────────────────────────────────\n"
                )

                chat_history.append({
                    "sender": "bot",
                    "text": f"API 통신 오류가 발생했습니다: {str(e)}"
                })


            # ------------------------------------------------
            # 세션 저장
            # ------------------------------------------------

            session["history"] = chat_history
            session.modified = True


    # ========================================================
    # HTML 페이지 출력
    # ========================================================

    return render_template(
        "index.html",
        history=chat_history
    )


# ============================================================
# 6. 서버 실행
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
```
