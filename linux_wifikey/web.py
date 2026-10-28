"""Web server and UI for Linux WifiKEY."""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

from .core import ProtocolClient
from .scanner import detect_wifi_interface, scan_networks

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Linux WifiKEY">
    <title>Linux WifiKEY - 随身Wi-Fi查密助手</title>
    <style>
        :root {
            --primary: #007AFF;
            --primary-bg: #EBF4FF;
            --success: #34C759;
            --success-bg: #E8F9EE;
            --bg: #F2F2F7;
            --card: #FFFFFF;
            --text: #1C1C1E;
            --text-sec: #8E8E93;
            --border: #E5E5EA;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --primary: #0A84FF;
                --primary-bg: #142845;
                --success: #30D158;
                --success-bg: #12381F;
                --bg: #000000;
                --card: #1C1C1E;
                --text: #F2F2F7;
                --text-sec: #98989D;
                --border: #2C2C2E;
            }
        }
        * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "PingFang SC", "Helvetica Neue", sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px 16px 80px;
        }
        .header {
            text-align: center;
            padding: 24px 0 16px;
        }
        .logo-icon {
            display: inline-block;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #007AFF, #0044CC);
            border-radius: 16px;
            box-shadow: 0 8px 20px rgba(0, 122, 255, 0.3);
            position: relative;
            margin-bottom: 12px;
        }
        .logo-icon svg {
            width: 36px;
            height: 36px;
            fill: white;
            position: absolute;
            top: 12px;
            left: 12px;
        }
        h1 {
            font-size: 24px;
            margin: 0;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        .subtitle {
            font-size: 13px;
            color: var(--text-sec);
            margin-top: 4px;
        }
        .status-pill {
            display: inline-block;
            margin-top: 8px;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-family: ui-monospace, Menlo, monospace;
            background: var(--card);
            border: 1px solid var(--border);
            color: var(--text-sec);
        }
        .scan-bar {
            margin: 16px 0;
        }
        .btn-scan {
            width: 100%;
            padding: 14px;
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: 14px;
            font-size: 17px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0, 122, 255, 0.25);
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        .btn-scan:active {
            transform: scale(0.98);
            opacity: 0.9;
        }
        .btn-scan:disabled {
            background-color: var(--text-sec);
            opacity: 0.6;
        }
        .card-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .wifi-card {
            background: var(--card);
            border-radius: 16px;
            padding: 16px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .wifi-card.has-pwd {
            border: 1.5px solid var(--success);
            background: linear-gradient(180deg, var(--card) 0%, var(--success-bg) 100%);
        }
        .wifi-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .wifi-title {
            font-size: 17px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
            word-break: break-all;
        }
        .badge {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 8px;
            font-weight: 600;
            white-space: nowrap;
        }
        .badge-shared {
            background-color: var(--success);
            color: white;
        }
        .badge-none {
            background-color: var(--border);
            color: var(--text-sec);
        }
        .wifi-info {
            font-size: 12px;
            color: var(--text-sec);
            display: flex;
            gap: 12px;
            font-family: ui-monospace, Menlo, Consolas, monospace;
        }
        .pwd-box {
            background: var(--card);
            border-radius: 12px;
            padding: 12px;
            border: 1px dashed var(--success);
            display: none;
            flex-direction: column;
            gap: 8px;
        }
        .pwd-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .pwd-val {
            font-size: 20px;
            font-weight: 700;
            color: var(--primary);
            letter-spacing: 0.5px;
            user-select: all;
            -webkit-user-select: all;
        }
        .btn-copy {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
        }
        .btn-action {
            width: 100%;
            padding: 10px;
            border-radius: 10px;
            border: none;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
        }
        .btn-check-pwd {
            background: var(--success);
            color: white;
        }
        .manual-section {
            margin-top: 24px;
            background: var(--card);
            border-radius: 16px;
            padding: 16px;
            border: 1px solid var(--border);
        }
        .manual-title {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .input-row {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        input {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid var(--border);
            background: var(--bg);
            color: var(--text);
            font-size: 15px;
        }
        .toast {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.85);
            color: white;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 14px;
            display: none;
            z-index: 999;
            box-shadow: 0 4px 14px rgba(0,0,0,0.3);
        }
        .empty-state {
            text-align: center;
            padding: 40px 16px;
            color: var(--text-sec);
            font-size: 14px;
        }
        .spinner {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-icon">
            <svg viewBox="0 0 24 24"><path d="M12 4C7.31 4 3.07 5.9 0 8.98L12 21 24 8.98C20.93 5.9 16.69 4 12 4zm0 3.5c3.78 0 7.21 1.54 9.69 4.02L12 19.22 2.31 11.52C4.79 9.04 8.22 7.5 12 7.5z"/></svg>
        </div>
        <h1>Linux WifiKEY</h1>
        <div class="subtitle">轻量级 Wi-Fi 硬件扫描与万能钥匙解密服务</div>
        <div class="status-pill" id="ifacePill">网卡: 正在检测...</div>
    </div>

    <div class="scan-bar">
        <button id="btnScan" class="btn-scan" onclick="startScan()">
            <span id="scanText">🔍 一键扫描周边 Wi-Fi</span>
        </button>
    </div>

    <div id="wifiList" class="card-list">
        <div class="empty-state">点击上方按钮，开始扫描服务器周边的 Wi-Fi</div>
    </div>

    <div class="manual-section">
        <div class="manual-title">🎯 手动指定网络查询（手机现场 Wi-Fi）</div>
        <div class="input-row">
            <input type="text" id="manualSsid" placeholder="输入周围的 Wi-Fi 名称 (SSID)">
            <input type="text" id="manualBssid" placeholder="可选: MAC地址 (BSSID, 如 aa:bb:cc:dd:ee:ff)">
            <button class="btn-scan" style="margin-top:4px;" onclick="manualQuery()">直接查询该密码</button>
        </div>
        <div id="manualResult" style="margin-top:12px; display:none;"></div>
    </div>

    <div id="toast" class="toast">已复制密码</div>

    <script>
        let currentNetworks = [];

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.display = 'block';
            setTimeout(() => { t.style.display = 'none'; }, 2000);
        }

        async function updateStatus() {
            try {
                const resp = await fetch('/api/status');
                const data = await resp.json();
                const pill = document.getElementById('ifacePill');
                if (data.interface) {
                    pill.innerText = '网卡: ' + data.interface;
                } else {
                    pill.innerText = '网卡: 未检测到无线网卡 (支持手动查密)';
                }
            } catch (e) {}
        }

        async function startScan() {
            const btn = document.getElementById('btnScan');
            const scanText = document.getElementById('scanText');
            btn.disabled = true;
            scanText.innerHTML = '<span class="spinner"></span> 正在扫描网卡并匹配数据库...';

            try {
                const resp = await fetch('/api/scan');
                const data = await resp.json();
                if (data.error) throw new Error(data.error);

                currentNetworks = data.networks;
                renderList(currentNetworks);
            } catch (err) {
                alert('扫描失败: ' + err.message);
            } finally {
                btn.disabled = false;
                scanText.innerText = '🔄 重新扫描周边 Wi-Fi';
            }
        }

        function renderList(list) {
            const container = document.getElementById('wifiList');
            if (!list || list.length === 0) {
                container.innerHTML = '<div class="empty-state">附近暂未扫描到无线信号（或未插无线网卡）</div>';
                return;
            }

            container.innerHTML = list.map((item, idx) => {
                const hasPwd = item.has_password;
                return `
                    <div class="wifi-card ${hasPwd ? 'has-pwd' : ''}" id="card-${idx}">
                        <div class="wifi-top">
                            <div class="wifi-title">
                                <span>${hasPwd ? '🔑 ' : '📶 '}${item.ssid}</span>
                            </div>
                            <span class="badge ${hasPwd ? 'badge-shared' : 'badge-none'}">
                                ${hasPwd ? '有共享密码' : '未收录'}
                            </span>
                        </div>
                        <div class="wifi-info">
                            <span>信号: ${item.level} dBm</span>
                            <span>${item.capabilities || 'WPA2'}</span>
                            <span>${item.bssid}</span>
                        </div>
                        ${hasPwd ? `
                            <button class="btn-action btn-check-pwd" onclick="fetchPwd(${idx})">
                                🔓 点击解密并查看密码
                            </button>
                            <div class="pwd-box" id="pwd-box-${idx}"></div>
                        ` : ''}
                    </div>
                `;
            }).join('');
        }

        async function fetchPwd(idx) {
            const item = currentNetworks[idx];
            const box = document.getElementById(`pwd-box-${idx}`);
            box.style.display = 'flex';
            box.innerHTML = '<span style="font-size:13px; color:var(--text-sec);"><span class="spinner"></span> 正在向接口申请解密...</span>';

            try {
                const resp = await fetch('/api/query_password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target: item, nearby: currentNetworks })
                });
                const data = await resp.json();
                if (data.error) throw new Error(data.error);

                if (!data.passwords || data.passwords.length === 0) {
                    box.innerHTML = '<span style="color:#FF3B30; font-size:13px;">未解析出可用密码</span>';
                    return;
                }

                box.innerHTML = data.passwords.map((p, pIdx) => `
                    <div class="pwd-item">
                        <div>
                            <div style="font-size:11px; color:var(--text-sec);">密码选项 ${pIdx+1}</div>
                            <div class="pwd-val">${p.password}</div>
                        </div>
                        <button class="btn-copy" onclick="copyText('${p.password}')">复制密码</button>
                    </div>
                `).join('');
            } catch (err) {
                box.innerHTML = `<span style="color:#FF3B30; font-size:13px;">获取失败: ${err.message}</span>`;
            }
        }

        async function manualQuery() {
            const ssid = document.getElementById('manualSsid').value.trim();
            const bssid = document.getElementById('manualBssid').value.trim();
            const resultBox = document.getElementById('manualResult');
            if (!ssid) {
                alert('请输入 Wi-Fi 名称');
                return;
            }

            resultBox.style.display = 'block';
            resultBox.innerHTML = '<span class="spinner"></span> 正在检索密码...';

            try {
                const resp = await fetch('/api/manual_query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ssid, bssid })
                });
                const data = await resp.json();
                if (data.error) throw new Error(data.error);

                if (!data.passwords || data.passwords.length === 0) {
                    resultBox.innerHTML = '<div style="color:var(--text-sec); font-size:13px; padding:10px;">万能钥匙数据库中未查询到该 Wi-Fi 的密码</div>';
                    return;
                }

                resultBox.innerHTML = `
                    <div class="pwd-box" style="display:flex;">
                        ${data.passwords.map((p, pIdx) => `
                            <div class="pwd-item">
                                <div>
                                    <div style="font-size:11px; color:var(--text-sec);">${ssid} (密码${pIdx+1})</div>
                                    <div class="pwd-val">${p.password}</div>
                                </div>
                                <button class="btn-copy" onclick="copyText('${p.password}')">复制</button>
                            </div>
                        `).join('')}
                    </div>
                `;
            } catch (err) {
                resultBox.innerHTML = `<span style="color:#FF3B30; font-size:13px;">查询失败: ${err.message}</span>`;
            }
        }

        function copyText(txt) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(txt).then(() => {
                    showToast('已复制密码: ' + txt);
                }).catch(() => {
                    prompt('请手动长按复制密码:', txt);
                });
            } else {
                prompt('请手动长按复制密码:', txt);
            }
        }

        updateStatus();
    </script>
</body>
</html>
"""


class RequestHandler(BaseHTTPRequestHandler):
    client = ProtocolClient()
    iface = None

    def log_message(self, format, *args):
        pass

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/api/status":
            detected = self.iface or detect_wifi_interface()
            self.send_json({"interface": detected})
        elif self.path == "/api/scan":
            try:
                detected = self.iface or detect_wifi_interface()
                networks = scan_networks(detected)
                statuses = {}
                if networks:
                    statuses = self.client.query_status(networks)

                for n in networks:
                    n["has_password"] = statuses.get(n["bssid"].lower(), False)

                networks.sort(key=lambda x: (1 if x["has_password"] else 0, x["level"]), reverse=True)
                self.send_json({"networks": networks, "interface": detected})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len)
        try:
            req_body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            req_body = {}

        if self.path == "/api/query_password":
            target = req_body.get("target")
            nearby = req_body.get("nearby", [])
            if not target:
                self.send_json({"error": "缺少目标网络"}, status=400)
                return
            try:
                passwords = self.client.fetch_passwords(target, nearby)
                self.send_json({"passwords": passwords})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)

        elif self.path == "/api/manual_query":
            ssid = req_body.get("ssid", "").strip()
            bssid = req_body.get("bssid", "").strip() or "00:11:22:33:44:55"
            if not ssid:
                self.send_json({"error": "请输入网络名称"}, status=400)
                return
            target = {
                "ssid": ssid,
                "bssid": bssid,
                "capabilities": "WPA2-PSK-CCMP",
                "level": -50
            }
            try:
                passwords = self.client.fetch_passwords(target, [target])
                self.send_json({"passwords": passwords})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
        else:
            self.send_response(404)
            self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def run_server(host="0.0.0.0", port=8888, iface=None):
    RequestHandler.iface = iface
    server = ThreadedHTTPServer((host, port), RequestHandler)
    print(f"[*] Linux WifiKEY web service started on http://{host}:{port}")
    if iface:
        print(f"[*] Using designated wireless interface: {iface}")
    else:
        detected = detect_wifi_interface()
        print(f"[*] Auto-detected wireless interface: {detected or 'None'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down server...")
        server.server_close()
