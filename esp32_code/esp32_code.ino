# === PHẦN 1: Sơ đồ nối dây mic INMP441 với ESP32 ===
# Mic INMP441 --- ESP32
# VCC           --- 3V3
# GND           --- GND
# WS (LRCL)     --- GPIO25
# SCK (BCLK)    --- GPIO26
# SD (DOUT)     --- GPIO22
# L/R           --- GND
# LED           --- GPIO5 (dùng điều khiển đèn bật/tắt)

# === PHẦN 2: Code ESP32 (Arduino IDE) thu âm và điều khiển đèn ===
# Dùng thư viện: WiFi, HTTPClient, I2S

#include <WiFi.h>
#include <HTTPClient.h>
#include <driver/i2s.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* server_url = "http://YOUR_PC_IP:5000/audio"; // Server nhận âm thanh

#define I2S_WS 25
#define I2S_SD 22
#define I2S_SCK 26
#define LED_PIN 5

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 1024,
    .use_apll = false
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK,
    .ws_io_num = I2S_WS,
    .data_in_num = I2S_SD,
    .data_out_num = I2S_PIN_NO_CHANGE
  };

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
}

void loop() {
  uint8_t audio_buffer[16000]; // 1 giây audio
  size_t bytes_read;
  i2s_read(I2S_NUM_0, &audio_buffer, sizeof(audio_buffer), &bytes_read, portMAX_DELAY);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(server_url);
    http.addHeader("Content-Type", "application/octet-stream");
    int httpResponseCode = http.POST(audio_buffer, bytes_read);
    String response = http.getString();
    Serial.println(response);
    http.end();

    // Điều khiển đèn theo phản hồi
    if (response == "on") {
      digitalWrite(LED_PIN, HIGH);
    } else if (response == "off") {
      digitalWrite(LED_PIN, LOW);
    }
  }

  delay(1000); // gửi mỗi 1 giây
}
