#!/bin/bash

echo "=========================================="
echo "  树莓派视频推流一键启动脚本（Tailscale专用）"
echo "=========================================="

# 1. 检查并启动 4G 网络
echo "[1/4] 检查4G网络..."
if ifconfig ppp0 &>/dev/null; then
    echo "      4G网络已连接"
else
    echo "      启动4G拨号..."
    sudo pkill -9 wvdial pppd
    sudo wvdial &
    sleep 8
fi

# 自动添加 4G 路由（解决上不了外网、Tailscale 连不上）
sleep 2
sudo ip route add default dev ppp0 2>/dev/null
echo "      ✅ 4G 外网路由已配置"

# 2. 关闭旧服务，防止冲突
echo "[2/4] 关闭旧服务..."
sudo pkill -9 mediamtx ffmpeg wvdial
sleep 2

# 3. 启动 MediaMTX
echo "[3/4] 启动 MediaMTX 视频服务器..."
cd /home/ubuntu/mediamtx
sudo ./mediamtx &
sleep 4

# 4. 启动 ffmpeg 推流（超低延迟 4G 稳定版）
echo "[4/4] 启动 ffmpeg 推流..."
ffmpeg -f v4l2 -i /dev/video0 \
  -c:v libx264 \
  -preset ultrafast -tune zerolatency \
  -g 10 -keyint_min 10 -sc_threshold 0 \
  -b:v 300k -maxrate 300k -bufsize 300k \
  -f rtsp rtsp://127.0.0.1:8554/cam

echo "=========================================="
echo "  ✅ 服务启动成功！"
echo "  电脑 YOLO 地址："
echo "  rtsp://$(tailscale ip -4):8554/cam"
echo "=========================================="

wait
