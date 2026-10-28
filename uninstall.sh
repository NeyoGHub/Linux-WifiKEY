#!/bin/bash
set -e

echo "========================================="
echo "       Linux WifiKEY 卸载脚本           "
echo "========================================="

if [ "$EUID" -ne 0 ]; then
  echo "[-] 请使用 root 权限运行此脚本: sudo bash uninstall.sh"
  exit 1
fi

SERVICE_NAME="linux-wifikey"
INSTALL_DIR="/opt/linux-wifikey"

echo "[*] 停止并移除服务..."
systemctl stop $SERVICE_NAME || true
systemctl disable $SERVICE_NAME || true
rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload

echo "[*] 移除免密权限配置..."
rm -f /etc/sudoers.d/linux-wifikey

echo "[*] 清理安装文件..."
rm -rf "$INSTALL_DIR"

echo "========================================="
echo "   ✅ Linux WifiKEY 已成功卸载!         "
echo "========================================="
