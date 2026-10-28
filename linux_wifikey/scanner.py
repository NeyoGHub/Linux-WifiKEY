"""Wi-Fi interface detection and scanning module for Linux."""

import glob
import os
import re
import subprocess


def detect_wifi_interface():
    """Auto-detect the first available wireless interface."""
    # 1. Environment variable override
    env_iface = os.environ.get("WIFI_IFACE")
    if env_iface:
        return env_iface

    # 2. Check /sys/class/net/*/wireless
    wireless_paths = glob.glob("/sys/class/net/*/wireless")
    for p in wireless_paths:
        iface = p.split("/")[-2]
        if iface:
            return iface

    # 3. Check `iw dev`
    try:
        res = subprocess.run(["iw", "dev"], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                line = line.strip()
                if line.startswith("Interface "):
                    return line.split("Interface ")[1].strip()
    except Exception:
        pass

    # 4. Check `nmcli -t -f DEVICE,TYPE device`
    try:
        res = subprocess.run(["nmcli", "-t", "-f", "DEVICE,TYPE", "device"], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if ":wifi" in line:
                    return line.split(":wifi")[0].strip()
    except Exception:
        pass

    return None


def decode_ssid(raw_ssid):
    """Decode raw SSID strings from iw, handling mixed ASCII and \\xHH UTF-8 bytes."""
    if r"\x" not in raw_ssid:
        return raw_ssid
    try:
        b = bytearray()
        i = 0
        n = len(raw_ssid)
        while i < n:
            if i + 3 < n and raw_ssid[i:i+2] == r"\x":
                try:
                    b.append(int(raw_ssid[i+2:i+4], 16))
                    i += 4
                    continue
                except ValueError:
                    pass
            b.extend(raw_ssid[i].encode("utf-8"))
            i += 1
        return b.decode("utf-8", errors="replace")
    except Exception:
        return raw_ssid


def scan_networks(iface=None):
    """Scan nearby Wi-Fi networks using iw, with dump fallback."""
    if not iface:
        iface = detect_wifi_interface()

    if not iface:
        return []

    output = ""
    # Try active scan first
    try:
        res = subprocess.run(["sudo", "/usr/sbin/iw", "dev", iface, "scan"], capture_output=True, text=True, timeout=12)
        if res.returncode == 0:
            output = res.stdout
    except Exception:
        pass

    # If active scan failed (e.g. device busy), fallback to scan dump
    if not output:
        try:
            res = subprocess.run(["sudo", "/usr/sbin/iw", "dev", iface, "scan", "dump"], capture_output=True, text=True, timeout=5)
            output = res.stdout
        except Exception:
            pass

    if not output:
        return []

    networks = []
    current = None

    for line in output.splitlines():
        line_strip = line.strip()
        if line_strip.startswith("BSS "):
            if current and current.get("ssid") and current.get("bssid"):
                networks.append(current)
            bssid_match = re.search(r"BSS ([0-9a-fA-F:]{17})", line_strip)
            current = {
                "bssid": bssid_match.group(1).lower() if bssid_match else "",
                "ssid": "",
                "level": -70,
                "frequency": 2412,
                "capabilities": "WPA2-PSK-CCMP"
            }
        elif current is not None:
            if line_strip.startswith("SSID:"):
                raw_ssid = line_strip[5:].strip()
                current["ssid"] = decode_ssid(raw_ssid)
            elif line_strip.startswith("signal:"):
                sig_match = re.search(r"signal:\s*(-?[0-9.]+)", line_strip)
                if sig_match:
                    current["level"] = int(float(sig_match.group(1)))
            elif line_strip.startswith("freq:"):
                freq_match = re.search(r"freq:\s*([0-9]+)", line_strip)
                if freq_match:
                    current["frequency"] = int(freq_match.group(1))
            elif "RSN:" in line_strip or "WPA:" in line_strip:
                if "WPA3" in line_strip or "SAE" in line_strip:
                    current["capabilities"] = "WPA3-SAE"
                else:
                    current["capabilities"] = "WPA2-PSK-CCMP"

    if current and current.get("ssid") and current.get("bssid"):
        networks.append(current)

    # De-duplicate keeping the strongest signal
    bssid_map = {}
    for n in networks:
        if not n["ssid"]:
            continue
        b = n["bssid"]
        if b not in bssid_map or n["level"] > bssid_map[b]["level"]:
            bssid_map[b] = n

    return list(bssid_map.values())
