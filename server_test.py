from flask import Flask
import sounddevice as sd
import scipy.io.wavfile as wav
import whisper
import openai
from gtts import gTTS
import os
import tempfile
from playsound import playsound
import threading

app = Flask(__name__)
model = whisper.load_model("base")
openai.api_key = "sk-proj-..."  # <-- Thay bằng key của bạn

def speak(text):
    if not text or text.strip() == "":
        return
    try:
        filename = "response.mp3"
        tts = gTTS(text=text, lang='vi')
        tts.save(filename)
        playsound(filename)
        os.remove(filename)
    except Exception as e:
        print("🔊 Lỗi khi phát âm:", e)

def listen_forever():
    samplerate = 16000
    duration = 3
    print("🎧 Đang lắng nghe... Nói 'ê cu' để tương tác.")

    while True:
        try:
            recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
            sd.wait()

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
                wav.write(temp.name, samplerate, recording)
                result = model.transcribe(temp.name, language="vi")
                os.remove(temp.name)

            text = result["text"].lower().strip()
            if not text or len(text) < 2:
                print("🤫 Không nghe rõ...")
                continue

            print(f"🗣️ Nghe được: {text}")

            if "ê cu" in text:
                if "bật đèn" in text:
                    response = "Đèn đã được bật"
                    print("💡", response)
                    speak(response)
                elif "tắt đèn" in text:
                    response = "Đèn đã được tắt"
                    print("💡", response)
                    speak(response)
                else:
                    chat_response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Bạn là trợ lý thân thiện."},
                            {"role": "user", "content": text}
                        ]
                    )
                    reply = chat_response["choices"][0]["message"]["content"]
                    print("🤖 ChatGPT:", reply)
                    speak(reply)

        except Exception as e:
            print("❌ Lỗi khi xử lý:", str(e))

@app.route("/test", methods=["GET"])
def test_audio():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
        record_audio(temp.name)
        try:
            result = model.transcribe(temp.name, language="vi")
            os.remove(temp.name)

            text = result["text"].lower().strip()
            if len(text) < 3:
                msg = "Không nghe rõ, vui lòng nói lại."
                print("⚠️", msg)
                speak(msg)
                return msg, 400

            print("🗣️ Nghe được từ /test:", text)

            if "bật đèn" in text:
                speak("Đèn đã được bật")
                return "on"
            elif "tắt đèn" in text:
                speak("Đèn đã được tắt")
                return "off"

            chat_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Bạn là trợ lý thân thiện."},
                    {"role": "user", "content": text}
                ]
            )
            reply = chat_response["choices"][0]["message"]["content"]
            speak(reply)
            return reply

        except Exception as e:
            print("❌ Lỗi khi xử lý ở /test:", str(e))
            speak("Không nghe rõ, vui lòng nói lại.")
            return "Lỗi xử lý", 500

def record_audio(filename, duration=2, samplerate=16000):
    print("🎤 Thu âm trong 2s...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='int16')
    sd.wait()
    wav.write(filename, samplerate, recording)
    print("✅ Đã thu xong")

if __name__ == "__main__":
    listener_thread = threading.Thread(target=listen_forever, daemon=True)
    listener_thread.start()
    app.run(host="0.0.0.0", port=5000)
