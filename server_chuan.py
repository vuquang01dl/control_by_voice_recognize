from flask import Flask, request, send_file
from openai import OpenAI
import numpy as np
from scipy.io.wavfile import write
from gtts import gTTS
import speech_recognition as sr
import os

app = Flask(__name__)

# OpenRouter AI
client = OpenAI(
    api_key="sk-or-your-api-key",
    base_url="https://openrouter.ai/api/v1"
)

TEMP_WAV = "voice_input.wav"
TTS_MP3 = "response.mp3"
TTS_WAV = "response.wav"

buffer = bytearray()
chunk_count = 0
CHUNKS_REQUIRED = 10
recognizer = sr.Recognizer()

@app.route("/audio", methods=["POST"])
def receive_audio():
    global buffer, chunk_count
    buffer.extend(request.data)
    chunk_count += 1

    if chunk_count >= CHUNKS_REQUIRED:
        audio_np = np.frombuffer(buffer, dtype=np.int16)
        write(TEMP_WAV, 16000, audio_np)

        try:
            with sr.AudioFile(TEMP_WAV) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio, language="vi-VN")
                print(f"🗣️ Văn bản: {text}")

                response = client.chat.completions.create(
                    model="mistralai/mistral-7b-instruct",
                    messages=[
                        {"role": "system", "content": "Bạn là trợ lý AI hỗ trợ tiếng Việt."},
                        {"role": "user", "content": text}
                    ]
                )
                reply = response.choices[0].message.content.strip()
                print(f"🤖 AI: {reply}")

                tts = gTTS(text=reply, lang="vi")
                tts.save(TTS_MP3)
                os.system(f"ffmpeg -y -i {TTS_MP3} -ar 16000 -ac 1 -c:a pcm_s16le {TTS_WAV}")
                print("✅ Đã tạo response.wav cho ESP")

        except Exception as e:
            print("❌ Lỗi:", e)

        buffer.clear()
        chunk_count = 0

    return "OK"

@app.route("/audio", methods=["GET"])
def serve_audio():
    if os.path.exists(TTS_WAV):
        return send_file(TTS_WAV, mimetype="audio/wav")
    return "❌ Chưa có phản hồi AI", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
