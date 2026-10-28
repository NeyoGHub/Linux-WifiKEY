#!/usr/bin/env python3
"""Linux WifiKEY - Entrypoint script."""

import argparse
import sys
from linux_wifikey.web import run_server


def main():
    parser = argparse.ArgumentParser(
        description="Linux WifiKEY - Lightweight Wi-Fi Scanner & WiFiMasterKey Protocol Service"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Listen host (default: 0.0.0.0)")
    parser.add_argument("-p", "--port", type=int, default=8888, help="Listen port (default: 8888)")
    parser.add_argument("-i", "--iface", default=None, help="Wireless interface to use (e.g. wlan0, default: auto)")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, iface=args.iface)


if __name__ == "__main__":
    main()
