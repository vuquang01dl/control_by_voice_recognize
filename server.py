from flask import Flask, request
import whisper
import openai
from gtts import gTTS
import os
import time

app = Flask(__name__)
model = whisper.load_model("base")
openai.api_key = "YOUR_OPENAI_API_KEY"

@app.route("/audio", methods=["POST"])
def receive_audio():
    with open("temp.wav", "wb") as f:
        f.write(request.data)

    try:
        result = model.transcribe("temp.wav", language="vi")
        text = result["text"].lower()
        print("Giọng nói:", text)

        # Xử lý lệnh bật tắt đèn
        if "bật đèn" in text:
            speak("Đèn đã được bật")
            return "on"
        elif "tắt đèn" in text:
            speak("Đèn đã được tắt")
            return "off"

        # Gửi text đến ChatGPT
        chat_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý thân thiện."},
                {"role": "user", "content": text}
            ]
        )
        reply = chat_response["choices"][0]["message"]["content"]
        print("ChatGPT:", reply)

        speak(reply)
        return reply

    except Exception as e:
        print("Lỗi xử lý:", e)
        return "Lỗi xử lý", 500

def speak(text):
    try:
        tts = gTTS(text=text, lang='vi')
        filename = "response.mp3"
        tts.save(filename)
        os.system(f"start {filename}" if os.name == 'nt' else f"mpg123 {filename}")
    except Exception as e:
        print("Lỗi phát âm thanh:", e)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)