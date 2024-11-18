import time
import torch
import numpy as np
from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import non_max_suppression
from yolov5.utils.augmentations import letterbox
import logging

import platform
import pathlib

plt = platform.system()
if plt != 'Windows':
    pathlib.WindowsPath = pathlib.PosixPath

class ObjectDetector:
    def __init__(self, model_path='./model_1.0.pt', conf_thres=0.8, iou_thres=0.8):
        if torch.cuda.is_available():
            logging.info("CUDA available, using cuda:0")
            device = torch.device('cuda:0')
        else:
            logging.info("CUDA not available, using CPU")
            device = torch.device('cpu')
        self.model = DetectMultiBackend(weights=model_path, device=device)
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.stopped = False

    def detect(self, frame) -> list[dict]:
        # print("Detecting...")
        start = time.time()
        # Adjust frame to fit model input requirements
        im = letterbox(frame, 640, stride=32, auto=True)[0]
        im = im.transpose((2, 0, 1))[::-1]
        im = np.ascontiguousarray(im)
        im = self.model.from_numpy(im)
        im = im.half() if self.model.fp16 else im.float()
        im /= 255.0
        if len(im.shape) == 3:
            im = im[None]  # Add batch dimension

        # Perform model prediction
        pred = self.model.forward(im, augment=False, visualize=False)
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres, classes=None, agnostic=False, max_det=1000)

        logging.debug(f"Detection took {time.time() - start} seconds")
        detections = []
        for det in pred:
            if len(det):
                for *xyxy, conf, cls in reversed(det):
                    if conf > self.conf_thres:
                        ok = True if cls == 1 else False
                        x = int(xyxy[0])
                        y = int(xyxy[1])
                        width = int(xyxy[2] - xyxy[0])
                        height = int(xyxy[3] - xyxy[1])
                        detections.append({"x": x, "y": y, "width": width, "height": height, "conf": float(conf), "ok": ok})
        return detections
