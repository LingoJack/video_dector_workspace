# import os
import av.error
from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import base64
import cv2
import numpy as np

from object import ObjectDetector
# import threading
# import concurrent.futures
import av
import io
# import time


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")
CORS(app, origins=["http://localhost:5173"])
detector = ObjectDetector()
# get_frame = 0

@app.route('/')
def index():
    return "WebSocket server is running!"


@socketio.on('video_stream')
def handle_video_stream(data: dict):
    # 获取视频流的帧数据
    frame_data = data['frame']

    # 将 Base64 数据转换为 NumPy 数组
    try:
        _header, encoded = frame_data.split(';base64,')
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error) as e:
        print(f"Base64 decoding error: {e}")
        return
    
    try:
        with av.open(io.BytesIO(data)) as container:
            for frame in container.decode(0):
                image = cv2.cvtColor(np.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                # print("detecting")
                boxes = detector.detect(image)
                if boxes is not None:
                    emit('defect_result', {'defect': boxes})
    except av.error.InvalidDataError as e:
        print(f"Invalid data error: {e}")
        # emit('error', {'message': 'Invalid video data'})
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # emit('error', {'message': 'An unexpected error occurred'})


@socketio.on('image_stream')
def image_stream(data: dict):
    # 获取图片的 Base64 数据
    image_data = data['image']

    # 将 Base64 数据转换为 NumPy 数组
    _header, encoded = image_data.split(';base64,')
    data = base64.b64decode(encoded)
    nparr = np.frombuffer(data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # global get_frame
    # get_frame += 1 
    # if get_frame == 15:
    #     # 保存当前帧到指定路径
    #     cv2.imwrite('./test_image.jpeg', frame)

    # 进行缺陷检测
    # start = time.time()
    boxes = detector.detect(frame)
    if boxes is not None:
        # print(f"Detection time: {time.time() - start}")
        # print(boxes)
        emit('defect_result', {'defect': boxes})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
