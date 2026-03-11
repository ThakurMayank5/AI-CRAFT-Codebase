import asyncio
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import whisper
import websockets
from scipy.signal import resample

# ── Config ──────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 42069
ESP_SAMPLE_RATE = 44100   # what the ESP32 I2S sends
WHISPER_SAMPLE_RATE = 16000  # what Whisper expects
SAMPLE_WIDTH = 4          # 32-bit PCM from ESP32
TRANSCRIBE_INTERVAL = 5   # seconds

# ── Globals ─────────────────────────────────────────────────────
model = None
esp_connection = None
audio_buffer = bytearray()
buffer_lock = asyncio.Lock()
executor = ThreadPoolExecutor(max_workers=2)


def transcribe_audio(pcm_data: bytes) -> str:
    """Convert 32-bit PCM from ESP32, resample 44100→16000, transcribe."""
    # ESP32 sends int32 I2S data (INMP441 24-bit in 32-bit frame)
    audio_np = np.frombuffer(pcm_data, dtype=np.int32).astype(np.float32) / 2147483648.0

    # Resample from 44100 Hz to 16000 Hz for Whisper
    num_samples_16k = int(len(audio_np) * WHISPER_SAMPLE_RATE / ESP_SAMPLE_RATE)
    audio_16k = resample(audio_np, num_samples_16k).astype(np.float32)

    result = model.transcribe(audio_16k, language="en")
    return result["text"]


async def transcription_loop():
    global audio_buffer
    loop = asyncio.get_event_loop()

    while True:
        await asyncio.sleep(TRANSCRIBE_INTERVAL)

        async with buffer_lock:
            if len(audio_buffer) < ESP_SAMPLE_RATE * SAMPLE_WIDTH:
                continue
            chunk = bytes(audio_buffer)
            audio_buffer = bytearray()

        try:
            text = await loop.run_in_executor(executor, transcribe_audio, chunk)
            text = text.strip()
            if text:
                print(f"[Whisper] {text}")
        except Exception as e:
            print(f"[Whisper Error] {e}")


async def esp_handler(ws):
    global esp_connection, audio_buffer

    esp_connection = ws
    print(f"[ESP32] Connected (id={id(ws)})")

    try:
        async for message in ws:
            if isinstance(message, bytes):
                async with buffer_lock:
                    audio_buffer.extend(message)
    except websockets.exceptions.ConnectionClosed:
        print("[ESP32] Disconnected")
    finally:
        if esp_connection is ws:
            esp_connection = None
            print("[ESP32] Connection cleared")


async def controller_handler(ws):
    print(f"[Controller] Connected  |  ESP32 = {'yes' if esp_connection else 'no'}")

    try:
        async for message in ws:
            print(f"[Controller] {message}")
            if esp_connection is not None:
                try:
                    await esp_connection.send(message)
                except websockets.exceptions.ConnectionClosed:
                    await ws.send("error: ESP32 disconnected")
            else:
                await ws.send("error: no ESP32 connected")
    except websockets.exceptions.ConnectionClosed:
        print("[Controller] Disconnected")


async def handler(ws):
    path = "/"
    if hasattr(ws, "request") and ws.request is not None:
        path = ws.request.path
    elif hasattr(ws, "path"):
        path = ws.path

    print(f"[Server] New connection on: {path}")

    if path == "/controller":
        await controller_handler(ws)
    else:
        await esp_handler(ws)


async def main():
    global model
    print("Loading Whisper model…")
    model = whisper.load_model("base")
    print(f"WebSocket server listening on :{PORT}")

    asyncio.create_task(transcription_loop())

    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
