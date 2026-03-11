/////////////////////////////////////////////////////////////////
/*
  Broadcasting Your Voice with ESP32-S3 & INMP441
  For More Information: https://youtu.be/qq2FRv0lCPw
  Created by Eric N. (ThatProject)
*/
/////////////////////////////////////////////////////////////////

/*
- Device
ESP32-S3 DevKit-C
https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/hw-reference/esp32s3/user-guide-devkitc-1.html

- Required Library
Arduino ESP32: 2.0.9

Arduino Websockets: 0.5.3
https://github.com/gilmaimon/ArduinoWebsockets
*/

#include <driver/i2s.h>
#include <WiFi.h>
#include <ArduinoWebsockets.h>

// ---- Function Prototypes ----
void connectWiFi();
void connectWSServer();
void micTask(void *parameter);

#define I2S_SD 33
#define I2S_WS 25
#define I2S_SCK 26
#define I2S_PORT I2S_NUM_0

#define bufferCnt 10
#define bufferLen 1024

#define LIGHT_PIN 2
#define AC_PIN 4
#define HEATER_PIN 5
#define FAN_PIN 18

bool lightState = false;
bool acState = false;
bool heaterState = false;
bool fanState = false;

const char *ssid = "OnePlus Nord 3 5G";
const char *password = "12345678";

const char *websocket_server_host = "10.134.10.151";
const uint16_t websocket_server_port = 42069; // <WEBSOCKET_SERVER_PORT>

using namespace websockets;
WebsocketsClient client;
bool isWebSocketConnected;

void onMessageCallback(WebsocketsMessage message)
{
    String msg = message.data();
    Serial.print("Received: ");
    Serial.println(msg);

    if (msg == "light:true")
    {
        Serial.println("Turning Light ON");
        lightState = true;
        digitalWrite(LIGHT_PIN, HIGH);
    }

    else if (msg == "light:false")
    {
        Serial.println("Turning Light OFF");
        lightState = false;
        digitalWrite(LIGHT_PIN, LOW);
    }

    else if (msg == "ac:true")
    {
        Serial.println("Turning AC ON");
        acState = true;
        digitalWrite(AC_PIN, HIGH);
    }

    else if (msg == "ac:false")
    {
        Serial.println("Turning AC OFF");
        acState = false;
        digitalWrite(AC_PIN, LOW);
    }

    else if (msg == "heater:true")
    {
        Serial.println("Turning Heater ON");
        heaterState = true;
        digitalWrite(HEATER_PIN, HIGH);
    }

    else if (msg == "heater:false")
    {
        Serial.println("Turning Heater OFF");
        heaterState = false;
        digitalWrite(HEATER_PIN, LOW);
    }

    else if (msg == "fan:true")
    {
        Serial.println("Turning Fan ON");
        fanState = true;
        digitalWrite(FAN_PIN, HIGH);
    }

    else if (msg == "fan:false")
    {
        Serial.println("Turning Fan OFF");
        fanState = false;
        digitalWrite(FAN_PIN, LOW);
    }
}

void onEventsCallback(WebsocketsEvent event, String data)
{
    if (event == WebsocketsEvent::ConnectionOpened)
    {
        Serial.println("Connnection Opened");
        isWebSocketConnected = true;
    }
    else if (event == WebsocketsEvent::ConnectionClosed)
    {
        Serial.println("Connnection Closed");
        isWebSocketConnected = false;
    }
    else if (event == WebsocketsEvent::GotPing)
    {
        Serial.println("Got a Ping!");
    }
    else if (event == WebsocketsEvent::GotPong)
    {
        Serial.println("Got a Pong!");
    }
}

void i2s_install()
{

    const i2s_config_t i2s_config = {
        .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate = 44100,
        .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
        .channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT,
        .communication_format = I2S_COMM_FORMAT_I2S,
        .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count = 8,
        .dma_buf_len = 256,
        .use_apll = false,
    };

    i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
}

void i2s_setpin()
{
    const i2s_pin_config_t pin_config = {
        .bck_io_num = 26,
        .ws_io_num = 25,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num = 33};

    i2s_set_pin(I2S_PORT, &pin_config);
}

void setup()
{
    Serial.begin(115200);

    connectWiFi();
    connectWSServer();
    xTaskCreatePinnedToCore(micTask, "micTask", 10000, NULL, 1, NULL, 1);

    pinMode(LIGHT_PIN, OUTPUT);
    pinMode(AC_PIN, OUTPUT);
    pinMode(HEATER_PIN, OUTPUT);
    pinMode(FAN_PIN, OUTPUT);
}

void loop()
{
    client.poll();
}

void connectWiFi()
{
    WiFi.begin(ssid, password);

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.println("WiFi connected");
}

void connectWSServer()
{
    client.onEvent(onEventsCallback);

    // For message handling
    client.onMessage(onMessageCallback);

    while (!client.connect(websocket_server_host, websocket_server_port, "/"))
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("Websocket Connected!");
}

int32_t audioBuffer[bufferLen];

void micTask(void *parameter)
{

    i2s_install();
    i2s_setpin();
    i2s_start(I2S_PORT);

    size_t bytesIn = 0;

    while (1)
    {
        esp_err_t result = i2s_read(
            I2S_PORT,
            audioBuffer,
            bufferLen * sizeof(int32_t),
            &bytesIn,
            portMAX_DELAY);

        if (result == ESP_OK && isWebSocketConnected)
        {
            client.sendBinary((const char *)audioBuffer, bytesIn);
        }
    }
}