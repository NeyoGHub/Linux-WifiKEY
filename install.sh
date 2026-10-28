#!/bin/bash
set -e

# Linux WifiKEY One-click Installer
echo "========================================="
echo "       Linux WifiKEY 安装向导           "
echo "========================================="

if [ "$EUID" -ne 0 ]; then
  echo "[-] 请使用 root 权限运行此脚本: sudo bash install.sh"
  exit 1
fi

INSTALL_DIR="/opt/linux-wifikey"
SERVICE_NAME="linux-wifikey"

echo "[*] 1. 安装系统依赖..."
if command -v apt-get >/dev/null 2>&1; then
    apt-get update -y
    apt-get install -y python3 python3-pip python3-cryptography iw wireless-tools
elif command -v dnf >/dev/null 2>&1; then
    dnf install -y python3 python3-pip python3-cryptography iw
elif command -v pacman >/dev/null 2>&1; then
    pacman -Sy --noconfirm python python-pip python-cryptography iw
fi

echo "[*] 2. 部署程序文件至 $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r ./* "$INSTALL_DIR/"

echo "[*] 3. 配置网卡扫描免密权限..."
echo "ALL ALL=(ALL) NOPASSWD: /usr/sbin/iw, /usr/bin/iw" > /etc/sudoers.d/linux-wifikey
chmod 0440 /etc/sudoers.d/linux-wifikey

echo "[*] 4. 配置并启动 Systemd 服务..."
cp "$INSTALL_DIR/systemd/linux-wifikey.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl restart $SERVICE_NAME

echo "========================================="
echo "   ✅ Linux WifiKEY 安装完成并在后台运行! "
echo "========================================="
echo "[*] 服务状态: $(systemctl is-active $SERVICE_NAME)"
echo "[*] 监听端口: 8888"
echo "[*] 访问地址: http://<你的服务器IP>:8888"
echo "========================================="
