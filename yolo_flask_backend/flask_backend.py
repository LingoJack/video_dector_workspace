# import os
from time import sleep
from flask import Flask, request
from flask_socketio import SocketIO
from flask_cors import CORS
import base64
import cv2
import numpy as np

from object import ObjectDetector

from queue import Queue
import concurrent.futures
import threading
# import av
# import io
# import time


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173", max_connections=10)
CORS(app, origins=["http://localhost:5173"])
detector = ObjectDetector()
executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)

queues: dict = {}
max_connections = 20


@socketio.on('connect')
def handle_connect():
    print("Client connected")
    if len(queues) <= max_connections:
        queues[request.sid] = Queue(maxsize=30)
        threading.Thread(target=sub_detect_thread, args=(request.sid,)).start()
    else:
        print("Exceeded maximum connections")
        socketio.emit('error', {'message': 'Exceeded maximum connections'}, to=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")
    del queues[request.sid]


@socketio.on('image_stream')
def image_stream(data: dict):
    # 获取图片的 Base64 数据
    image_data = data['image']

    # 将 Base64 数据转换为 NumPy 数组
    _header, encoded = image_data.split(';base64,')
    data = base64.b64decode(encoded)
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # 进行缺陷检测
    queues[request.sid].put(frame)

def detect_and_emit(sid, frame):
    boxes = detector.detect(frame)
    if boxes is not None:
        socketio.emit('defect_result', {'defect': boxes}, to=sid)
    else:
        socketio.emit('error', {'message': 'No defects detected'}, to=sid)

def detect_with_timeout(sid, frame, timeout):
    future = executor.submit(detect_and_emit, sid, frame)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        print("Detection took too long, skipping...")
        return None

def sub_detect_thread(sid: str):
    while True:
        sleep(0.05)
        queue: Queue = queues[sid]
        if queue is None:
            break
        detect_with_timeout(sid, queue.get(), 0.5)
        


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)


# class Handler(Namespace):
#     def on_connect(self):
#         self.image_queue = Queue(maxsize=15)
#         self.unfinished = True
#         def detection_thread():
#             while self.unfinished:
#                 if not self.image_queue.empty():
#                     frame, id = self.image_queue.get()
#                     boxes = detector.detect(frame)
#                     if boxes is not None:
#                         self.emit('defect_result', {'defect': boxes}, namespace='/', to=id)
#         self.thread = socketio.start_background_task(detection_thread)
#     def on_disconnect(self):
#         self.unfinished = False
#         print("Client disconnected")
#         self.thread.join()
#     def on_image_stream(self, data):
#         image_data = data['image']
#         # 将 Base64 数据转换为 NumPy 数组
#         _header, encoded = image_data.split(';base64,')
#         image_payload = base64.b64decode(encoded)
#         nparr = np.frombuffer(image_payload, np.uint8)
#         frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#         if frame is not None:
#             if not self.image_queue.full():
#                 self.image_queue.put((frame, request.sid))
#             else:
#                 print("Exeeded maximum queue size")
#                 self.image_queue.get()



# @app.route('/')
# def index():
#     return "WebSocket server is running!"


# @socketio.on('video_stream')
# def handle_video_stream(data: dict):
#     # 获取视频流的帧数据
#     frame_data = data['frame']

#     # 将 Base64 数据转换为 NumPy 数组
#     try:
#         _header, encoded = frame_data.split(';base64,')
#         data = base64.b64decode(encoded, validate=True)
#     except (ValueError, base64.binascii.Error) as e:
#         print(f"Base64 decoding error: {e}")
#         return
    
#     try:
#         with av.open(io.BytesIO(data)) as container:
#             for frame in container.decode(0):
#                 image = cv2.cvtColor(np.array(frame.to_image()), cv2.COLOR_RGB2BGR)
#                 # print("detecting")
#                 boxes = detector.detect(image)
#                 if boxes is not None:
#                     emit('defect_result', {'defect': boxes})
#     except av.error.InvalidDataError as e:
#         print(f"Invalid data error: {e}")
#         # emit('error', {'message': 'Invalid video data'})
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         # emit('error', {'message': 'An unexpected error occurred'})


# @socketio.on('image_stream')
# def image_stream(data: dict):
#     # 获取图片的 Base64 数据
#     image_data = data['image']

#     # 将 Base64 数据转换为 NumPy 数组
#     _header, encoded = image_data.split(';base64,')
#     data = base64.b64decode(encoded)
#     nparr = np.frombuffer(data, np.uint8)
#     frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)


#     # 进行缺陷检测
#     start = time.time()
#     boxes = detector.detect(frame)
#     if boxes is not None:
#         print(f"Detection time: {time.time() - start}")
#         # print(boxes)
#         emit('defect_result', {'defect': boxes})
