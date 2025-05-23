#include <WiFi.h>
#include <HTTPClient.h>
#include <driver/i2s.h>
#include <AudioFileSourceICYStream.h>
#include <AudioGeneratorWAV.h>
#include <AudioOutputI2S.h>

#define I2S_WS 33    // WS (LRCL)
#define I2S_SD 32    // SD (DOUT)
#define I2S_SCK 27   // SCK (BCLK)
#define DAC_PIN 25   // phát ra loa

const char* ssid = "Vu Kien";
const char* password = "";
const char* server_url = "http://192.168.1.16:5000/audio";

#define SAMPLE_RATE 16000
#define CHUNK_SIZE 8000
#define NUM_CHUNKS 10
#define VOLUME_THRESHOLD 500

AudioGeneratorWAV *wav;
AudioFileSourceICYStream *file;
AudioOutputI2S *out;

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\n✅ WiFi connected");

  // Setup I2S (MIC)
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk = 0
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num = I2S_SD
  };

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
}

void play_response() {
  file = new AudioFileSourceICYStream(server_url);
  out = new AudioOutputI2S(0, 1); // Use DAC, GPIO25
  out->SetOutputModeMono(true);
  out->SetGain(1.0);
  wav = new AudioGeneratorWAV();
  wav->begin(file, out);
  while (wav->isRunning()) wav->loop();
  wav->stop();
  delete wav;
  delete out;
  delete file;
}

void loop() {
  int16_t sample = 0;
  size_t bytes_read;
  i2s_read(I2S_NUM_0, &sample, sizeof(sample), &bytes_read, portMAX_DELAY);
  if (abs(sample) > VOLUME_THRESHOLD) {
    Serial.println("🎤 Phát hiện tiếng – bắt đầu ghi...");
    for (int i = 0; i < NUM_CHUNKS; i++) {
      uint8_t* chunk = (uint8_t*)malloc(CHUNK_SIZE);
      size_t read_bytes = 0;
      i2s_read(I2S_NUM_0, chunk, CHUNK_SIZE, &read_bytes, portMAX_DELAY);
      HTTPClient http;
      http.begin(server_url);
      http.addHeader("Content-Type", "application/octet-stream");
      http.POST(chunk, read_bytes);
      http.end();
      free(chunk);
      delay(10);
    }
    Serial.println("✅ Đã gửi đủ 10 đoạn – chờ phản hồi...");
    delay(1000);
    play_response();
  }
}
