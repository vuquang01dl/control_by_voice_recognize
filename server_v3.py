#kết nối với chatgpt phản hồi lại âm thanh mp3
from flask import Flask, request, send_file
import numpy as np
from scipy.io.wavfile import write
import os
import speech_recognition as sr
from gtts import gTTS
import openai
import time

app = Flask(__name__)
recognizer = sr.Recognizer()

# 🔑 Nhập API key của bạn
openai.api_key = "YOUR_OPENAI_API_KEY"

buffer = bytearray()
chunk_count = 0
CHUNKS_REQUIRED = 10
last_used = "temp2.wav"

@app.route("/audio", methods=["POST"])
def receive_audio():
    global buffer, chunk_count, last_used

    try:
        data = request.data
        buffer.extend(data)
        chunk_count += 1
        print(f"📥 Đã nhận {chunk_count}/{CHUNKS_REQUIRED}")

        if chunk_count >= CHUNKS_REQUIRED:
            new_file = "temp1.wav" if last_used == "temp2.wav" else "temp2.wav"
            old_file = "temp2.wav" if new_file == "temp1.wav" else "temp1.wav"

            if os.path.exists(old_file):
                os.remove(old_file)

            audio_np = np.frombuffer(bytes(buffer), dtype=np.int16)
            write(new_file, 16000, audio_np)
            last_used = new_file
            buffer.clear()
            chunk_count = 0

            # 🧠 Nhận diện giọng nói
            with sr.AudioFile(new_file) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language="vi-VN")
                print("🗣️ Văn bản:", text)

            # 💬 Gửi lên ChatGPT
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Bạn là trợ lý tiếng Việt."},
                    {"role": "user", "content": text}
                ]
            )
            reply = response['choices'][0]['message']['content'].strip()
            print("🤖 ChatGPT:", reply)

            # 🎧 Tạo file .mp3
            tts = gTTS(reply, lang="vi")
            tts.save("response.mp3")
            print("💾 Đã tạo response.mp3")

            return "✅ Đã xử lý và tạo phản hồi"

        return f"⏳ Đã nhận {chunk_count}/{CHUNKS_REQUIRED}"

    except Exception as e:
        print("❌ Lỗi:", e)
        return "Lỗi server", 500

@app.route("/get_response", methods=["GET"])
def get_mp3():
    if os.path.exists("response.mp3"):
        return send_file("response.mp3", mimetype="audio/mpeg")
    else:
        return "Chưa có phản hồi", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
