# Linux WifiKEY 🔑

> **轻量级 Linux Wi-Fi 硬件扫描与万能钥匙免密直解服务**  
> 支持物理网卡硬件级信号捕获、纯 Python 逆向解密引擎、iOS / Android 自适应极简 Web 界面与一键后台常驻。

---

## ✨ 核心特性

- 📡 **硬件级 Wi-Fi 实时雷达**：
  - 自动识别并调用 Linux 无线网卡（支持外置 USB 高增益无线网卡）；
  - 自动解析周边 2.4G / 5G 热点的 SSID、BSSID、信号强弱（dBm）及加密套件；
  - 完美支持中文字符编码（如 `水电维修部`、`永惠超市` 等中文热点无乱码）。
- 🔐 **纯 Python 逆向通信引擎**：
  - 完整复刻“WiFi万能钥匙”加密通信协议（`AES-256-CBC/PKCS7` 动态会话密钥握手）；
  - 内置 WGS84 经纬度转百度 BD-09 坐标算法，支持多热点批量可用性匹配；
  - **直接解密并输出明文密码**，打破商业 App 对用户屏蔽密码的限制。
- 📱 **专为移动端（iPhone / iPad / 安卓）设计的轻量 Web UI**：
  - 遵循 iOS 17 / Material Design 毛玻璃极简审美，丝滑无广告；
  - 密码一键解密展示与快捷复制，支持有多个候选密码时自由挑选；
  - 适配 Safari Web App（PWA），可直接“添加到主屏幕”作为独立免签应用使用。
- 🎯 **支持现场热点手动查密**：
  - 如果目标 Wi-Fi 仅在手机附近、超出服务器物理网卡探测范围，可直接在网页端输入 Wi-Fi 名称进行云端直查。
- ⚡ **零笨重依赖**：
  - 纯标准库 + `cryptography`，无需额外安装复杂的 Web 框架，极速低耗。

---

## 🛠️ 快速安装与部署

### 方式一：一键自动安装（推荐，自动注册系统服务）

适用于 Debian / Ubuntu / CentOS / Arch Linux 等主流发行版：

```bash
git clone https://github.com/NeyoGHub/Linux-WifiKEY.git
cd Linux-WifiKEY
sudo bash install.sh
```

脚本将自动完成：
1. 安装底层依赖（`python3-cryptography`、`iw` 等）；
2. 部署到 `/opt/linux-wifikey`；
3. 配置免密执行无线扫描权限；
4. 注册并启动开机自启的后台服务 `linux-wifikey.service`（默认监听 `8888` 端口）。

---

### 方式二：手动直接运行

如果你只需要临时测试或调试：

```bash
# 1. 安装依赖
pip3 install -r requirements.txt

# 2. 直接启动服务
python3 app.py --port 8888

# 指定特定无线网卡（默认自动检测）
python3 app.py --port 8888 --iface wlan0
```

---

## 📲 在手机端访问与使用

1. 打开手机浏览器（支持 iPhone Safari、Chrome、微信内置浏览器等）；
2. 访问：`http://<你的服务器IP>:8888`（若配合 Tailscale 组网，输入 Tailscale 节点 IP 即可全球直连）；
3. **iPhone 体验小技巧**：在 Safari 底部点击「分享」按钮，选择 **「添加到主屏幕」**，即可生成桌面独立快捷图标，全屏无边框打开！

---

## 🔌 RESTful API 接口说明

服务内置了标准 JSON 接口，方便第三方应用或自动化脚本接入：

| 接口 | 方法 | 说明 | 请求示例 / 载荷 |
|---|---|---|---|
| `/` | `GET` | 移动端交互式 Web 控制台 | - |
| `/api/status` | `GET` | 查看当前调用的无线网卡状态 | `{"interface": "wlan0"}` |
| `/api/scan` | `GET` | 触发硬件扫描并批量校验密码共享状态 | 返回排序后的热点数组与 `has_password` 标记 |
| `/api/query_password`| `POST`| 解密指定热点的明文密码 | `{"target": {...}, "nearby": [...]}` |
| `/api/manual_query` | `POST`| 手动输入热点名称直接查密 | `{"ssid": "Target-WiFi", "bssid": "可选"}` |

---

## 🗑️ 服务卸载

如需彻底移除后台服务与文件，执行：

```bash
sudo bash uninstall.sh
```

---

## ⚠️ 免责声明 (Disclaimer)

本项目仅用于技术研究、网络协议分析、兼容性测试及合法环境下的网络诊断。请勿用于未经授权访问他人私有网络、批量抓取数据或其他违反法律法规的行为。项目作者不对任何非法使用承担责任。

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 许可开源。
