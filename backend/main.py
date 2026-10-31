import ipaddress
import platform
import re
import subprocess

from fastapi import FastAPI, HTTPException

app = FastAPI()

LATENCY_PATTERN = re.compile(r"time[=<]([\d.]+)\s*ms")

@app.get("/")
def root():
    return {"message": "NetMon is running"}

@app.get("/ping/{ip}")
def ping(ip: str):
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address")

    system = platform.system()
    count_flag = "-n" if system == "Windows" else "-c"
    command = "ping6" if addr.version == 6 and system == "Darwin" else "ping"

    try: 
        result = subprocess.run(
            ["ping", count_flag, "1", ip],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return {"ip": ip, "reachable": False, "latency_ms": None}

    reachable = result.returncode == 0
    latency_ms = None
    if reachable:
        match = LATENCY_PATTERN.search(result.stdout)
        if match:
            latency_ms = float(match.group(1))

    return {"ip": ip, "reachable": reachable, "latency_ms": latency_ms}