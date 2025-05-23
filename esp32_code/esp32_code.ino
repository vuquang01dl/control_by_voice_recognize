#include <WiFi.h>
#include <HTTPClient.h>
#include <driver/i2s.h>

#define I2S_WS 25
#define I2S_SD 22
#define I2S_SCK 26

const char* ssid = "Vu Kien";
const char* password = "";
const char* server_url = "http://192.168.1.16:5000/audio";

#define SAMPLE_RATE 16000
#define CHUNK_SIZE 8000      // 1 giây @ 16kHz 16bit mono
#define NUM_CHUNKS 10        // Tổng 10 giây
#define VOLUME_THRESHOLD 500 // Ngưỡng phát hiện tiếng nói

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi connected");

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

void loop() {
  int16_t sample = 0;
  size_t bytes_read;

  // Đọc 1 mẫu
  i2s_read(I2S_NUM_0, &sample, sizeof(sample), &bytes_read, portMAX_DELAY);
  int amplitude = abs(sample);

  if (amplitude > VOLUME_THRESHOLD) {
    Serial.print("🎤 Phát hiện tiếng: ");
    Serial.println(amplitude);

    for (int i = 0; i < NUM_CHUNKS; i++) {
      uint8_t* chunk = (uint8_t*)malloc(CHUNK_SIZE);
      if (!chunk) {
        Serial.println("❌ Không đủ bộ nhớ!");
        return;
      }

      size_t read_bytes = 0;
      i2s_read(I2S_NUM_0, chunk, CHUNK_SIZE, &read_bytes, portMAX_DELAY);

      if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(server_url);
        http.addHeader("Content-Type", "application/octet-stream");
        http.POST(chunk, read_bytes);
        http.end();
      }

      free(chunk);
    }

    Serial.println("✅ Gửi xong 10 đoạn (10 giây)");
    delay(1); // nghỉ sau khi hoàn tất
  }
}
