import ipaddress
import platform
import re
import subprocess
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from database import Device, DeviceCreate, create_db_and_tables, get_session

LATENCY_PATTERN = re.compile(r"time[=<]([\d.]+)\s*ms")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

SessionDep = Annotated[Session, Depends(get_session)]


def parse_ip(ip: str):
    try:
        return ipaddress.ip_address(ip)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address")


@app.get("/")
def root():
    return {"message": "NetMon is running"}


@app.get("/ping/{ip}")
def ping(ip: str):
    addr = parse_ip(ip)

    system = platform.system()
    count_flag = "-n" if system == "Windows" else "-c"
    command = "ping6" if addr.version == 6 and system == "Darwin" else "ping"

    try:
        result = subprocess.run(
            [command, count_flag, "1", ip],
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


@app.post("/devices", status_code=201)
def create_device(device: DeviceCreate, session: SessionDep) -> Device:
    device.ip = str(parse_ip(device.ip))

    existing = session.exec(select(Device).where(Device.ip == device.ip)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Device with this IP already exists")

    db_device = Device.model_validate(device)
    session.add(db_device)
    session.commit()
    session.refresh(db_device)
    return db_device


@app.get("/devices")
def list_devices(session: SessionDep) -> list[Device]:
    return session.exec(select(Device)).all()


@app.get("/devices/{device_id}")
def get_device(device_id: int, session: SessionDep) -> Device:
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.delete("/devices/{device_id}", status_code=204)
def delete_device(device_id: int, session: SessionDep):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    session.delete(device)
    session.commit()