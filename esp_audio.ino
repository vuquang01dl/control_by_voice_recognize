#include <WiFi.h>
#include <HTTPClient.h>
#include <AudioFileSourceICYStream.h>
#include <AudioFileSourceBuffer.h>
#include <AudioGeneratorWAV.h>
#include <AudioOutputI2S.h>

const char* ssid = "Vu Kien";
const char* password = "";
const char* audio_url = "http://192.168.1.16:5000/audio";  // Flask server trả về file WAV

AudioGeneratorWAV *wav;
AudioFileSourceICYStream *file;
AudioOutputI2S *out;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\n✅ Đã kết nối WiFi");

  file = new AudioFileSourceICYStream(audio_url);
  out = new AudioOutputI2S(0, 1);  // DAC tích hợp, chân 25
  out->SetOutputModeMono(true);
  out->SetGain(1.0);
  wav = new AudioGeneratorWAV();

  wav->begin(file, out);
}

void loop() {
  if (wav->isRunning()) {
    if (!wav->loop()) wav->stop();
  } else {
    delay(1000);  // Chờ sẵn server phát file mới
  }
}
