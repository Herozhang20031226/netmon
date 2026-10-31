import ipaddress
import platform
import subprocess

from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/")
def root():
    return {"message": "NetMon is running"}

@app.get("/ping/{ip}")
def ping(ip: str):
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address")

    count_flag = "-n" if platform.system() == "Windows" else "-c"

    result = subprocess.run(
        ["ping", count_flag, "1", ip],
        capture_output=True,
        timeout=5,
    )

    return {"ip": ip, "reachable": result.returncode == 0}