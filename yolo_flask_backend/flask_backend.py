# import os
from time import sleep
from flask import Flask, request
from flask_socketio import SocketIO
from flask_cors import CORS
import base64
import cv2
import numpy as np
import os
import logging

from object import ObjectDetector

from queue import Queue
import concurrent.futures
import threading
import av
import io


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173", max_connections=10)
CORS(app, origins=["http://localhost:5173"])
detector = ObjectDetector(model_path='./model_1.0.pt')
executor = concurrent.futures.ThreadPoolExecutor(max_workers=(os.cpu_count()/2 or 4))

queues: dict = {}
max_connections = 20


@socketio.on('connect')
def handle_connect():
    logging.debug(f"Client {request.sid} connected")
    if len(queues) <= max_connections:
        queues[request.sid] = Queue(maxsize=30)
        threading.Thread(target=sub_detect_thread, args=(request.sid,)).start()
    else:
        logging.warning("Exceeded maximum connections")
        socketio.emit('error', {'message': 'Exceeded maximum connections'}, to=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    logging.debug(f"Client {request.sid} disconnected")
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

    queues[request.sid].put(frame)

@socketio.on('video_stream')
def video_stream(data: dict):
    # 获取视频流的帧数据
    frame_data = data['frame']

    # 将 Base64 数据转换为 NumPy 数组
    _header, encoded = frame_data.split(';base64,')
    data = base64.b64decode(encoded, validate=True)
    
    try:
        with av.open(io.BytesIO(data)) as container:
            for frame in container.decode(0):
                image = cv2.cvtColor(np.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                queues[request.sid].put(image)
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        logging.error(error_msg)
        socketio.emit('error', {'message': error_msg}, to=request.sid)

def detect_and_emit(sid, frame):
    boxes = detector.detect(frame)
    socketio.emit('defect_result', {'defect': boxes}, to=sid)

def detect_with_timeout(sid, frame, timeout):
    future = executor.submit(detect_and_emit, sid, frame)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        logging.warning(f"Detection timed out for client {sid}")
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
