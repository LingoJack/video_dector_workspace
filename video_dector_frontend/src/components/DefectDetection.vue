<template>
  <div class="container">
    <h1>实时图片流和缺陷检测</h1>
    <div class="control-panel">
      <label for="videoSource">选择视频源:</label>
      <select id="videoSource" v-model="selectedSource" @change="startCapture">
        <option value="screen">共享屏幕</option>
        <option v-for="device in videoDevices" :key="device.deviceId" :value="device.deviceId">
          {{ device.label || `摄像头 ${device.deviceId}` }}
        </option>
      </select>
    </div>
    <div id="screenVideo" class="video-container">
      <video id="video" autoplay playsinline></video>
      <div id="overlay"></div>
    </div>
    <!-- 隐藏的 canvas 用于抓取帧 -->
    <canvas id="captureCanvas" style="display: none;"></canvas>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import { io } from 'socket.io-client';

const host = 'http://127.0.0.1:5000';
const socket = io(host);
const selectedSource = ref("screen");
const selectedDeviceId = ref(null);
const videoDevices = ref([]);
const captureInterval = 100; // 捕获帧的间隔（毫秒）
let intervalId = null;
let mediaStream = null;

// 获取视频设备列表
const getVideoDevices = async () => {
  const devices = await navigator.mediaDevices.enumerateDevices();
  videoDevices.value = devices.filter(device => device.kind === 'videoinput');
  if (videoDevices.value.length > 0) {
    selectedDeviceId.value = videoDevices.value[0].deviceId;
  }
};

// 启动视频捕获
const startCapture = async () => {
  stopCapture(); // 停止当前的视频捕获
  if (selectedSource.value === "screen") {
    await startScreenShare();
  } else {
    await startCameraCapture();
  }
};

// 共享屏幕捕获
const startScreenShare = async () => {
  try {
    mediaStream = await navigator.mediaDevices.getDisplayMedia({
      video: { width: { max: 640 }, height: { max: 360 }, frameRate: { max: 15 } }
    });
    handleStream(mediaStream);
  } catch (err) {
    console.error("屏幕共享错误:", err);
  }
};

// 摄像头捕获
const startCameraCapture = async () => {
  try {
    const constraints = {
      video: {
        deviceId: selectedDeviceId.value ? { exact: selectedDeviceId.value } : undefined,
        width: { max: 640 },
        height: { max: 360 },
        frameRate: { max: 15 }
      }
    };
    mediaStream = await navigator.mediaDevices.getUserMedia(constraints);
    handleStream(mediaStream);
  } catch (err) {
    console.error("摄像头捕获错误:", err);
  }
};

// 处理视频流
const handleStream = (stream) => {
  const videoElement = document.getElementById('video');
  videoElement.srcObject = stream;
  sendImageToServer(stream);
};

// 发送视频帧到服务器
const sendImageToServer = (stream) => {
  const videoElement = document.getElementById('video');
  const canvas = document.getElementById('captureCanvas');
  const context = canvas.getContext('2d');

  const captureFrameAndSend = () => {
    if (videoElement.videoWidth && videoElement.videoHeight) {
      canvas.width = videoElement.videoWidth;
      canvas.height = videoElement.videoHeight;
      context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

      const imageDataUrl = canvas.toDataURL('image/jpeg', 0.8);
      socket.emit('image_stream', { image: imageDataUrl });
    }
  };

  intervalId = setInterval(captureFrameAndSend, captureInterval);
};

// 更新缺陷检测的结果显示
socket.on('defect_result', (data) => {
  updateDefectOverlay(data);
});

// 修改后的 updateDefectOverlay 函数，支持多组缺陷数据
const updateDefectOverlay = (data) => {
  const overlayElement = document.getElementById('overlay');
  overlayElement.innerHTML = ''; // 清除上一次的检测框

  // 检查 data.defects 是否存在且为数组
  if (data.defects && Array.isArray(data.defects)) {
    data.defects.forEach(defect => {
      const box = document.createElement('div');
      box.className = 'defect-box';
      box.style.position = 'absolute';
      box.style.left = `${defect.x}px`;
      box.style.top = `${defect.y}px`;
      box.style.width = `${defect.width}px`;
      box.style.height = `${defect.height}px`;

      // 根据缺陷状态设置边框颜色
      box.style.border = defect.ok ? '2px solid green' : '2px solid red';

      overlayElement.appendChild(box);
    });
  } else {
    console.warn('缺陷数据格式不正确:', data);
  }
};

// 停止视频捕获
const stopCapture = () => {
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = null;
  }
  if (mediaStream) {
    const tracks = mediaStream.getTracks();
    tracks.forEach(track => track.stop()); // 停止所有媒体轨道
    mediaStream = null; // 释放媒体流引用
  }
};

// 组件卸载时清理资源
onUnmounted(() => {
  stopCapture(); // 清理资源
});

// 组件挂载时获取视频设备
onMounted(() => {
  getVideoDevices();
});
</script>

<style scoped>
.container {
  font-family: Arial, sans-serif;
  max-width: 800px;
  margin: auto;
  padding: 20px;
  text-align: center;
  background-color: #f9f9f9;
  border-radius: 8px;
  box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
}

h1 {
  font-size: 24px;
  color: #333;
  margin-bottom: 20px;
}

.control-panel {
  margin-bottom: 20px;
}

label {
  font-size: 16px;
  color: #555;
}

select {
  padding: 8px;
  font-size: 14px;
  margin-left: 10px;
  border-radius: 4px;
  border: 1px solid #ccc;
}

.video-container {
  position: relative;
  width: 100%;
  max-width: 640px;
  margin: auto;
  border: 2px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

video {
  width: 100%;
  height: auto;
  border-radius: 8px;
}

#overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.defect-box {
  position: absolute;
  border: 2px solid;
  border-radius: 4px;
}
</style>
