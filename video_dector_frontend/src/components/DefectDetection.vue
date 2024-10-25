<template>
  <div class="container">
    <h1>实时视频流和缺陷检测</h1>
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
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { io } from 'socket.io-client';

const host = 'http://localhost:5000';
const socket = io(host); // 创建 WebSocket 连接
const selectedDeviceId = ref(null);
const videoDevices = ref([]);

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
    sendStreamToServer(stream);
  } catch (err) {
    console.error("Error: " + err);
  }
};

const sendStreamToServer = (stream) => {
  const mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
      const reader = new FileReader();
      reader.onloadend = () => {
        // 发送视频流数据给后端
        socket.emit('video_stream', { frame: reader.result });
      };
      reader.readAsDataURL(event.data); // 将 Blob 转为 Data URL
    }
  };
  mediaRecorder.start(1000); // 每1秒发送一次数据
};

// 处理缺陷检测结果
socket.on('defect_result', (data) => {
  updateDefectOverlay(data);
});

const updateDefectOverlay = (data) => {
  const overlayElement = document.getElementById('overlay');
  overlayElement.innerHTML = ''; // 清空之前的框
  if (data.defect) {
    const box = document.createElement('div');
    box.className = 'defect-box';
    box.style.left = `${data.defect.x}px`;
    box.style.top = `${data.defect.y}px`;
    box.style.width = `${data.defect.width}px`;
    box.style.height = `${data.defect.height}px`;
    overlayElement.appendChild(box);
  }
};

// 组件挂载时获取设备列表
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
  border: 2px solid red;
  background-color: rgba(255, 0, 0, 0.2);
  border-radius: 4px;
}
</style>
