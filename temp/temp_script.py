import asyncio
import websockets
import cv2

IP = "10.134.10.29"

async def start_stream():
    ws = await websockets.connect(f"ws://{IP}/ws")

    await ws.send("STREAM:1")
    print("Stream enabled")

    cap = cv2.VideoCapture(f"http://{IP}:82/stream")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("frame error")
            break

        cv2.imshow("ESP32", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    await ws.send("STREAM:0")
    await ws.close()

asyncio.run(start_stream())