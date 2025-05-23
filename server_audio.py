from openai import OpenAI
from gtts import gTTS
import os

# 🧠 Cấu hình OpenRouter API
client = OpenAI(
    api_key="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",  # Đổi nếu cần
    base_url="https://openrouter.ai/api/v1"
)

output_count = 1

while True:
    user_input = input("👤 Bạn: ")
    if user_input.strip().lower() in ["exit", "quit"]:
        break

    print("🤖 Gửi tới OpenRouter...")
    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý AI hỗ trợ người dùng bằng tiếng Việt."},
                {"role": "user", "content": user_input}
            ]
        )
        reply = response.choices[0].message.content.strip()
        print("💬 AI:", reply)

        # Tạo file tên riêng
        mp3_filename = f"output_{output_count:02}.mp3"
        txt_filename = f"output_{output_count:02}.txt"

        print(f"🔊 Đang lưu giọng nói vào {mp3_filename}...")
        tts = gTTS(text=reply, lang="vi")
        tts.save(mp3_filename)

        # Lưu nội dung văn bản
        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write(f"Bạn: {user_input}\n\nAI: {reply}")

        print(f"✅ Đã lưu file: {mp3_filename} và {txt_filename}\n")
        output_count += 1

    except Exception as e:
        print("❌ Lỗi khi gọi OpenRouter:", e)
