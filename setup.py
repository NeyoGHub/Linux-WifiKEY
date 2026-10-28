from setuptools import setup, find_packages

setup(
    name="linux-wifikey",
    version="1.0.0",
    description="Lightweight Wi-Fi Scanner and WiFiMasterKey Protocol Service for Linux",
    author="Neyo",
    packages=find_packages(),
    install_requires=[
        "cryptography>=38.0.0",
    ],
    entry_points={
        "console_scripts": [
            "linux-wifikey=app:main",
        ],
    },
    python_requires=">=3.8",
)
