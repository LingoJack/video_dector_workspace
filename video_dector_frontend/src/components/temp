<template>
  <div class="container">
    <h1>实时图片流和缺陷检测</h1>
    <div class="control-panel">
      <label for="videoSource">选择视频设备:</label>
      <select id="videoSource" v-model="selectedDeviceId" @change="startScreenCapture">
        <option v-for="device in videoDevices" :key="device.deviceId" :value="device.deviceId">
          {{ device.label || `摄像头 ${device.deviceId}` }}
        </option>
      </select>
    </div>
    <div id="screenVideo" class="video-container">
      <video id="video" autoplay></video>
      <div id="overlay"></div>
    </div>
    <!-- 隐藏的 canvas 用于抓取帧 -->
    <canvas id="captureCanvas" style="display: none;"></canvas>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue';
import { io } from 'socket.io-client';

const host = 'http://localhost:5000';
const socket = io(host); // 创建 WebSocket 连接
const selectedDeviceId = ref(null);
const videoDevices = ref([]);
const captureInterval = 100; // 设置抓取图片的间隔时间（毫秒）
let intervalId = null; // 用于存储 setInterval 的 ID

// 获取视频输入设备列表
const getVideoDevices = async () => {
  const devices = await navigator.mediaDevices.enumerateDevices();
  videoDevices.value = devices.filter(device => device.kind === 'videoinput');
  if (videoDevices.value.length > 0) {
    selectedDeviceId.value = videoDevices.value[0].deviceId; // 默认选择第一个设备
    startScreenCapture(); // 自动启动屏幕捕获
  }
};

// 启动屏幕捕获或摄像头捕获
const startScreenCapture = async () => {
  try {
    const constraints = {
      video: {
        deviceId: selectedDeviceId.value ? { exact: selectedDeviceId.value } : undefined,
        width: { max: 640 },
        height: { max: 360 },
        frameRate: { max: 15 }
      }
    };
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    const videoElement = document.getElementById('video');
    videoElement.srcObject = stream;
    sendImageToServer(stream);
  } catch (err) {
    console.error("Error: " + err);
  }
};

const sendImageToServer = (stream) => {
  const videoElement = document.getElementById('video');
  const canvas = document.getElementById('captureCanvas');
  const context = canvas.getContext('2d');

  // 定时器函数，用于定期抓取帧并发送
  const captureFrameAndSend = () => {
    if (videoElement.videoWidth && videoElement.videoHeight) {
      canvas.width = videoElement.videoWidth;
      canvas.height = videoElement.videoHeight;
      context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

      // 将 canvas 转换为 Data URL
      const imageDataUrl = canvas.toDataURL('image/jpeg', 0.8); // 0.8 是质量参数

      // 发送图片数据给后端
      socket.emit('image_stream', { image: imageDataUrl });
    }
  };

  // 开始定时抓取帧
  intervalId = setInterval(captureFrameAndSend, captureInterval);
};

// 处理缺陷检测结果
socket.on('defect_result', (data) => {
  updateDefectOverlay(data);
});

const updateDefectOverlay = (data) => {
  const overlayElement = document.getElementById('overlay');
  overlayElement.innerHTML = ''; // 清空之前的框

  // 创建缺陷框
  const box = document.createElement('div');
  box.className = 'defect-box';
  box.style.left = `${data.x}px`;
  box.style.top = `${data.y}px`;
  box.style.width = `${data.width}px`;
  box.style.height = `${data.height}px`;

  // 根据 ok 字段设置框的颜色
  if (data.ok) {
    box.style.borderColor = 'green'; // 如果 ok 为 true，设置绿边
    box.style.backgroundColor = 'rgba(0, 255, 0, 0.2)'; // 绿色背景
  } else {
    box.style.borderColor = 'red';   // 如果 ok 为 false，设置红边
    box.style.backgroundColor = 'rgba(255, 0, 0, 0.2)'; // 红色背景
  }

  // 将框添加到 overlay 中
  overlayElement.appendChild(box);
};

// 组件卸载时清理资源
onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
  }
  const videoElement = document.getElementById('video');
  if (videoElement && videoElement.srcObject) {
    const tracks = videoElement.srcObject.getTracks();
    tracks.forEach(track => track.stop());
    videoElement.srcObject = null;
  }
});

// 组件挂载时获取设备列表
onMounted(() => {
  getVideoDevices();
});
</script>

<style scoped>
/* 保持原有的样式不变 */
.defect-box {
  position: absolute;
  border: 2px solid; /* 默认颜色，但会被 JavaScript 覆盖 */
  border-radius: 4px;
}
</style>