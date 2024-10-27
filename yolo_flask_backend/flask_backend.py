import os
from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import base64
import cv2

from object import ObjectDetector
import threading


import concurrent.futures
import time


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")
CORS(app, origins=["http://localhost:5173"])
detector = ObjectDetector()


@app.route('/')
def index():
    return "WebSocket server is running!"


@socketio.on('video_stream')
def handle_video_stream(data: dict):
    # 获取视频流的帧数据
    frame_data = data['frame']

    # 将 Base64 数据转换为 NumPy 数组
    _header, encoded = frame_data.split(';base64,')
    data = base64.b64decode(encoded)

    temp_file_path = f'/tmp/temp_video_{int(time.time())}_{threading.get_ident()}.mkv'
    with open(temp_file_path, 'wb') as file:
        file.write(data)
    cap = cv2.VideoCapture(temp_file_path)

    cnt = 0
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                print('Video stream ended')
                break
            cnt += 1

            if frame is not None:
                # if cnt % 5 == 0:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(detector.detect, frame)
                    try:
                        boxes = future.result(timeout=0.1)  # 500ms timeout
                        if boxes is not None:
                            emit('defect_result', {'defect': boxes})
                    except concurrent.futures.TimeoutError:
                        break  # Detection took longer than 500ms, return immediately
    finally:
        cap.release()
        os.remove(temp_file_path)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
