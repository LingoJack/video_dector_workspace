import asyncio
import websockets
import numpy as np
import cv2
import json
import base64
from object import ObjectDetector

async def video_stream(websocket: websockets.WebSocketServerProtocol, detector: ObjectDetector):
    print("Client connected")
    while True:
        try:
            data = await websocket.recv()
            frame_data = json.loads(data)
            base64_frame = frame_data['frame'].split(',')[1]
            np_data = np.frombuffer(base64.b64decode(base64_frame), dtype=np.uint8)
            frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
            if frame is not None:
                boxes = detector.detect(frame)
                print(boxes)
                await websocket.send(json.dumps({"defect": boxes}))
        except websockets.exceptions.ConnectionClosed:
            break
        except json.JSONDecodeError:
            await websocket.send(json.dumps({"error": "Invalid JSON"}))
        except Exception as e:
            await websocket.send(json.dumps({"error": str(e)}))

async def main():
    detector = ObjectDetector(conf_thres=0.25, iou_thres=0.45)

    async def handler(ws, path):
        print("request")
        if path == "/video_stream":
            await video_stream(ws, detector)
        else:
            await ws.close()

    async with websockets.serve(handler, "localhost", 5000):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
    