import atexit
import os
from flask import Flask
from flask_socketio import SocketIO, emit
from flask_cors import CORS
# import asyncio
import base64
import cv2
# import numpy as np
# import imageio

from object import ObjectDetector
# import queue
# import threading


import concurrent.futures
# import time


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")
CORS(app, origins=["http://localhost:5173"])

@app.route('/')
def index():
    return "WebSocket server is running!"

detector = ObjectDetector()


# @socketio.on('video_stream')
# def handle_video_stream(data: dict):
#     # 获取视频流的帧数据
#     frame_data = data['frame']

#     # 将 Base64 数据转换为 NumPy 数组
#     _header, encoded = frame_data.split(';base64,')
#     data = base64.b64decode(encoded)

#     temp_file_path = f'/tmp/temp_video_{int(time.time())}_{threading.get_ident()}.mkv'
#     with open(temp_file_path, 'wb') as file:
#         file.write(data)
#     cap = cv2.VideoCapture(temp_file_path)

#     cnt = 0
#     try:
#         while cap.isOpened():
#             ret, frame = cap.read()
            
#             if not ret:
#                 print('Video stream ended')
#                 break
#             cnt += 1

#             if frame is not None:
#                 # if cnt % 5 == 0:
#                 with concurrent.futures.ThreadPoolExecutor() as executor:
#                     future = executor.submit(detector.detect, frame)
#                     try:
#                         boxes = future.result(timeout=0.1)  # 500ms timeout
#                         if boxes is not None:
#                             emit('defect_result', {'defect': boxes})
#                     except concurrent.futures.TimeoutError:
#                         break  # Detection took longer than 500ms, return immediately
#     finally:
#         cap.release()
#         os.remove(temp_file_path)


one_tmp_file = "/tmp/temp_video.mkv"
@socketio.on('video_stream')
def handle_video_stream(data: dict):
    # 获取视频流的帧数据
    frame_data = data['frame']

    # 将 Base64 数据转换为 NumPy 数组
    _header, encoded = frame_data.split(';base64,')
    data = base64.b64decode(encoded)
    with open(one_tmp_file, 'wb') as file:
        file.write(data)
    
    cap2 = cv2.VideoCapture(one_tmp_file)

    cnt = 0
    try:
        while cap2.isOpened():
            ret, frame = cap2.read()
            
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
        cap2.release()
    #     os.remove(temp_file_path)


if __name__ == '__main__':
    # # 启动工作线程
    # thread = threading.Thread(target=worker)
    # thread.start()
    socketio.run(app, host='0.0.0.0', port=5000)

@atexit.register
def cleanup():
    # cap2.release()
    os.remove(one_tmp_file)

# def call_once(func):
#     called = False

#     def wrapper(*args, **kwargs):
#         nonlocal called
#         if not called:
#             called = True
#             return func(*args, **kwargs)
#     return wrapper


# @call_once
# def initialize_detector():
#     global detector
#     detector.initialize()

    
# @call_once
# def get_a_photo(np_array):
#     # 将 NumPy 数组保存为图像文件
#     output_image_path = './output_image.jpg'
#     cv2.imwrite(output_image_path, np_array)


# # 在适当的位置添加任务到队列
# def process_video(data, emit):
#     temp_file_path = f'/tmp/temp_video_{int(time.time())}_{threading.get_ident()}.mp4'
#     with open(temp_file_path, 'wb') as file:
#         file.write(data)
#     cap = cv2.VideoCapture(temp_file_path)
    
#     cnt = 0
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             break
#         cnt += 1
#         if frame is not None and cnt % 5 == 0:
#             add_task_to_queue(detect_and_emit, frame, emit)

#     cap.release()
    
    
# def detect_and_emit(frame, emit):
#     def detect_with_timeout(frame):
#         return detector.detect(frame)

#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         future = executor.submit(detect_with_timeout, frame)
#         try:
#             boxes = future.result(timeout=0.5)  # 500ms timeout
#             if boxes is not None:
#                 emit('defect_result', {'defect': boxes})
#         except concurrent.futures.TimeoutError:
#             return  # Detection took longer than 500ms, return immediately


# # 创建一个队列来存储任务
# task_queue = queue.Queue()


# def add_task_to_queue(func, *args):
#     if task_queue.qsize() > 5:
#         task_queue.get()  # Remove the first task from the queue
#     task_queue.put((func, args))


# def worker():
#     while True:
#         task = task_queue.get()
#         if task is None:
#             break
#         func, args = task
#         func(*args)
#         task_queue.task_done()


# # 在程序结束时确保工作线程正确退出
# @atexit.register
# def cleanup():
#     task_queue.put(None)
#     thread.join()