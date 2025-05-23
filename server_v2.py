#ghi âm thanh và lưu, nhận diện âm thanh ok nhưng chưa gửi lên chatgpt
from flask import Flask, request
import numpy as np
from scipy.io.wavfile import write
import os
import time
import speech_recognition as sr

app = Flask(__name__)

last_used = "temp2.wav"
buffer = bytearray()
chunk_count = 0
CHUNKS_REQUIRED = 10

recognizer = sr.Recognizer()

@app.route("/audio", methods=["POST"])
def receive_audio():
    global buffer, chunk_count, last_used

    try:
        data = request.data
        buffer.extend(data)
        chunk_count += 1

        print(f"📥 Nhận đoạn {chunk_count}/{CHUNKS_REQUIRED} ({len(data)} bytes)")
        print(f"🔁 Lần trước dùng: {last_used}")

        if chunk_count >= CHUNKS_REQUIRED:
            new_file = "temp1.wav" if last_used == "temp2.wav" else "temp2.wav"
            old_file = "temp2.wav" if new_file == "temp1.wav" else "temp1.wav"

            print(f"➡️ Ghi vào: {new_file} | Xóa trước: {old_file}")

            if os.path.exists(old_file):
                try:
                    os.remove(old_file)
                    print(f"🧹 Đã xóa {old_file}")
                except Exception as e:
                    print(f"⚠️ Không thể xóa {old_file}: {e}")
                    return f"Lỗi khi xóa {old_file}", 500

            try:
                safe_buffer = bytes(buffer)
                audio_np = np.frombuffer(safe_buffer, dtype=np.int16)
                write(new_file, 16000, audio_np)
                print(f"💾 Đã ghi {new_file} ({os.path.getsize(new_file)} bytes)")

                last_used = new_file

                # 🎤 Nhận diện bằng SpeechRecognition (Google Web Speech API)
                with sr.AudioFile(new_file) as source:
                    audio_data = recognizer.record(source)
                    text = recognizer.recognize_google(audio_data, language="vi-VN")
                    print("🗣️ Văn bản nhận được:", text)
                    print("-" * 50)

            except sr.UnknownValueError:
                print("🛑 Không nhận diện được giọng nói.")
            except sr.RequestError as e:
                print(f"🌐 Lỗi kết nối Google API: {e}")
            except Exception as e:
                print(f"❌ Lỗi khi xử lý {new_file}: {e}")
                return "Lỗi xử lý âm thanh", 500

            buffer.clear()
            chunk_count = 0

            return f"✅ Đã ghi và xử lý {new_file}"

        return f"Đã nhận {chunk_count}/{CHUNKS_REQUIRED} đoạn"

    except Exception as e:
        print("❌ Lỗi server:", e)
        return "Lỗi server", 500

@app.route("/")
def index():
    return "🎙️ Ghi âm và nhận diện bằng Google Speech Recognition"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
