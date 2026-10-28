"""Core protocol client for WiFiMasterKey API."""

import base64
import json
import math
import random
import time
import urllib.request
import uuid
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

HOST = "api.ttwifi.net"
TRANSPORT_PATH = "/mapi2"
TOKEN_PATH = "/user/token"
STATUS_PATH = "/wifi/status"
PASSWORD_PATH = "/wifi/spotInfo"
EXCHANGE_SEED = "Jk2u#nfP8mJ@9dq%Wcbqvgt89qRNe5v!"
SV_SEED = "9a929a7c118749588b51bb179e358638"
SV_VERSION = "sb250916"


def canonical_json(val):
    if val is None:
        return "null"
    elif isinstance(val, dict):
        items = sorted(val.items(), key=lambda x: str(x[0]))
        return "{" + ",".join(f"{json.dumps(str(k))}:{canonical_json(v)}" for k, v in items) + "}"
    elif isinstance(val, list):
        return "[" + ",".join(canonical_json(v) for v in val) + "]"
    elif isinstance(val, str):
        return json.dumps(val)
    elif isinstance(val, bool):
        return "true" if val else "false"
    elif isinstance(val, (int, float)):
        return str(val)
    else:
        raise TypeError(f"Unsupported json type: {type(val)}")


def cipher_aes(data: bytes, seed: str, encrypt: bool) -> bytes:
    key = seed.encode("utf-8")
    if len(key) != 32:
        key = key.ljust(32, b'0')[:32]
    iv = key[:16]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    if encrypt:
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        encryptor = cipher.encryptor()
        return encryptor.update(padded_data) + encryptor.finalize()
    else:
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(data) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return unpadder.update(decrypted) + unpadder.finalize()


def make_sv():
    unsigned = random.getrandbits(32)
    payload = f"{unsigned}:{SV_VERSION}:{int(time.time() * 1000)}".encode("utf-8")
    encrypted = cipher_aes(payload, SV_SEED, True)
    return base64.b64encode(encrypted).decode("ascii")


def post_request(path: str, model: dict, seed: str, token: str = None):
    url = f"https://{HOST}{TRANSPORT_PATH}"
    plain = path.encode("ascii") + b"\n" + canonical_json(model).encode("utf-8")
    body = cipher_aes(plain, seed, True)

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "octet-stream")
    req.add_header("User-Agent", "ureq/2.12.1")
    req.add_header("Accept-Encoding", "gzip")
    if token:
        req.add_header("x-http-token", token)

    with urllib.request.urlopen(req, timeout=30) as resp:
        wire = resp.read()
        cipher_header = resp.headers.get("x-cypher-type")
        encoding = resp.headers.get("Content-Encoding")
        if encoding == "gzip":
            import gzip
            wire = gzip.decompress(wire)

        response_seed = None
        if cipher_header == "1":
            response_seed = EXCHANGE_SEED
        elif cipher_header == "2":
            response_seed = seed

        if response_seed:
            try:
                decoded = cipher_aes(wire, response_seed, False)
            except Exception:
                decoded = wire
        else:
            decoded = wire

        res_json = json.loads(decoded.decode("utf-8"))
        code = res_json.get("1")
        if code != 0:
            raise Exception(f"API {code}: {res_json.get('2', '未知错误')}")
        return res_json


class ProtocolClient:
    def __init__(self):
        self.session = None

    def ensure_session(self):
        if self.session:
            return self.session
        return self.login()

    def login(self):
        client_seed = uuid.uuid4().hex.lower()
        client_seed_enc = base64.b64encode(cipher_aes(client_seed.encode("ascii"), EXCHANGE_SEED, True)).decode("ascii")

        device_info = {
            "1": uuid.uuid4().hex.lower(),
            "2": None, "3": "",
            "4": "Xiaomi", "5": "Xiaomi", "6": "22041216C",
            "7": "android", "8": "33", "9": "tencent",
            "10": None, "11": "", "12": "wklite", "13": "TT0088", "14": 2,
            "50": None, "51": "2400", "52": "1080",
            "53": "Xiaomi/redmi/22041216C", "54": "33", "55": "TKQ1.220829.002",
            "56": "false", "57": "", "61": None, "62": None, "63": None
        }

        req_body = {
            "1": device_info,
            "2": client_seed_enc,
            "3": {"1": "1.1.50", "2": 250926},
            "30": None,
            "31": make_sv()
        }

        res = post_request(TOKEN_PATH, req_body, EXCHANGE_SEED)
        data = res["5"]
        token_cipher = base64.b64decode(data["2"])
        token_data = json.loads(cipher_aes(token_cipher, client_seed, False).decode("utf-8"))

        self.session = {
            "token": token_data["1"],
            "serverSeed": token_data["2"],
            "dhid": data["1"]["9"]
        }
        return self.session

    def query_status(self, networks, lon=116.4074, lat=39.9042):
        session = self.ensure_session()
        bd_lon, bd_lat, bd_alt = self.wgs84_to_bd09(lon, lat)
        routers = []
        for n in networks[:100]:
            routers.append({
                "1": n["ssid"],
                "2": n["bssid"].lower(),
                "3": n.get("capabilities", "WPA-PSK-CCMP"),
                "4": int(n.get("level", -50))
            })

        req_body = {
            "1": routers,
            "2": {"1": bd_lon, "2": bd_lat, "3": bd_alt},
            "3": {
                "1": "", "2": "", "3": "", "4": "", "5": "", "6": "", "7": 0, "8": "",
                "9": "", "10": session["dhid"], "11": "TT0088", "12": 250926, "13": "tencent"
            }
        }
        try:
            res = post_request(STATUS_PATH, req_body, session["serverSeed"], session["token"])
        except Exception as e:
            if "-6" in str(e):
                self.session = None
                return self.query_status(networks, lon, lat)
            raise e

        items = res.get("5", {}).get("1", [])
        status_map = {}
        for item in items:
            bssid = item.get("2", "").lower()
            status_map[bssid] = bool(item.get("7"))
        return status_map

    def fetch_passwords(self, target, nearby, lon=116.4074, lat=39.9042):
        session = self.ensure_session()
        bd_lon, bd_lat, bd_alt = self.wgs84_to_bd09(lon, lat)
        near = []
        for n in nearby[:100]:
            caps = n.get("capabilities", "WPA-PSK-CCMP")
            sec = "WPA" if ("WPA" in caps or "PSK" in caps or "SAE" in caps) else ("WEP" if "WEP" in caps else "NONE")
            near.append({
                "1": n["ssid"],
                "2": n["bssid"].lower(),
                "3": caps,
                "4": int(n.get("level", -50)),
                "6": float(n.get("level", -50)),
                "7": sec
            })

        req_body = {
            "1": target["ssid"],
            "2": target["bssid"].lower(),
            "3": target.get("capabilities", "WPA-PSK-CCMP"),
            "4": None,
            "6": {"1": bd_lon, "2": bd_lat, "3": bd_alt, "9": None},
            "7": near,
            "8": [],
            "9": make_sv(),
            "30": {
                "1": "", "2": "", "3": "", "4": "", "5": "", "6": "", "7": int(time.time() * 1000), "8": "",
                "9": "", "10": session["dhid"], "11": "TT0088", "12": 250926, "13": "tencent"
            }
        }

        try:
            res = post_request(PASSWORD_PATH, req_body, session["serverSeed"], session["token"])
        except Exception as e:
            if "-6" in str(e):
                self.session = None
                return self.fetch_passwords(target, nearby, lon, lat)
            raise e

        data = res.get("5", {})
        pwd_cipher = base64.b64decode(data.get("1", ""))
        ref_cipher = base64.b64decode(data.get("2", ""))

        passwords = json.loads(cipher_aes(pwd_cipher, session["serverSeed"], False).decode("utf-8"))
        references = json.loads(cipher_aes(ref_cipher, session["serverSeed"], False).decode("utf-8"))

        results = []
        for p, r in zip(passwords, references):
            if p:
                results.append({"password": p, "reference": str(r) if r else ""})
        return results

    @staticmethod
    def wgs84_to_bd09(lon, lat, alt=0.0):
        PI = math.pi
        A = 6378245.0
        EE = 0.006693421622965943
        X_PI = PI * 3000.0 / 180.0

        if not (72.004 <= lon <= 137.8347 and 0.8293 <= lat <= 55.8271):
            gcj_lon, gcj_lat = lon, lat
        else:
            x = lon - 105.0
            y = lat - 35.0
            d_lat = (-100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x)))
            d_lat += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
            d_lat += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
            d_lat += (160.0 * math.sin(y / 12.0 * PI) + 320 * math.sin(y * PI / 30.0)) * 2.0 / 3.0

            d_lon = (300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x)))
            d_lon += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
            d_lon += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
            d_lon += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0

            rad_lat = lat / 180.0 * PI
            magic = 1 - EE * (math.sin(rad_lat) ** 2)
            sqrt_magic = math.sqrt(magic)

            gcj_lat = lat + (d_lat * 180.0) / ((A * (1 - EE)) / (magic * sqrt_magic) * PI)
            gcj_lon = lon + (d_lon * 180.0) / (A / sqrt_magic * math.cos(rad_lat) * PI)

        z = math.sqrt(gcj_lon * gcj_lon + gcj_lat * gcj_lat) + 0.00002 * math.sin(gcj_lat * X_PI)
        theta = math.atan2(gcj_lat, gcj_lon) + 0.000003 * math.cos(gcj_lon * X_PI)
        bd_lon = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        return bd_lon, bd_lat, alt
