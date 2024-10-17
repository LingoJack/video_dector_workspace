<template>
  <div>
    <h1>实时视频流和缺陷检测</h1>
    <div id="screenVideo">
      <video id="video" autoplay></video>
      <div id="overlay"></div>
    </div>
  </div>
</template>

<script setup>
import {onMounted, ref} from 'vue';
import {io} from 'socket.io-client';

const host = 'http://localhost:5000';
const socket = io(host); // 创建 WebSocket 连接

const startScreenCapture = async () => {
  try {
    const stream = await navigator.mediaDevices.getDisplayMedia({video: true});
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
        // 这里发送视频流数据给后端
        socket.emit('video_stream', {frame: reader.result});
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
    box.style.position = 'absolute';
    box.style.border = '2px solid red';
    // 假设返回的坐标为 { x: 100, y: 200, width: 50, height: 50 }
    box.style.left = `${data.defect.x}px`;
    box.style.top = `${data.defect.y}px`;
    box.style.width = `${data.defect.width}px`;
    box.style.height = `${data.defect.height}px`;
    overlayElement.appendChild(box);
  }
};

// 组件挂载时启动屏幕捕获
onMounted(() => {
  startScreenCapture();
});
</script>

<style scoped>
#screenVideo {
  position: relative;
  width: 640px;
  height: 360px;
  border: 1px solid #000;
}

#overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* Prevent mouse events on overlay */
}

.defect-box {
  position: absolute;
  border: 2px solid red;
  pointer-events: none; /* Prevent mouse events on boxes */
}
</style>
