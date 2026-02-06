from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from datetime import datetime
import csv
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

app = FastAPI()

STATIC_DIR = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")


@app.get("/")
async def register_page():
    return FileResponse(STATIC_DIR / "register.html")


@app.get("/register")
async def register_page_alias():
    return FileResponse(STATIC_DIR / "register.html")


@app.get("/desk/pharmacy")
async def desk_pharmacy_page():
    return FileResponse(STATIC_DIR / "desk-pharmacy.html")


@app.get("/desk/laboratory")
async def desk_laboratory_page():
    return FileResponse(STATIC_DIR / "desk-laboratory.html")


@app.get("/desk/clinic")
async def desk_clinic_page():
    return FileResponse(STATIC_DIR / "desk-clinic.html")


@app.get("/display")
async def display_page():
    return FileResponse(STATIC_DIR / "display.html")


@app.get("/api/queues")
async def get_queues():
    return JSONResponse(queues)

# In-memory queues
queues = {
    "pharmacy": [],
    "lab": [],
    "clinic": [],
    "referral": [],
    "appointment": []
}

# Active connections
connections = []


def log_to_csv(patient_id, service):
    with open("data/today.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            patient_id,
            service
        ])


async def broadcast():
    for ws in connections:
        await ws.send_json(queues)


@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    connections.append(ws)

    # Send initial state
    await ws.send_json(queues)

    try:
        while True:
            data = await ws.receive_json()

            action = data["action"]

            if action == "register":
                pid = data["patient_id"]
                service = data["service"]

                queues[service].append(pid)
                log_to_csv(pid, service)

            elif action == "next":
                service = data["service"]

                if queues[service]:
                    queues[service].pop(0)

            await broadcast()

    except WebSocketDisconnect:
        connections.remove(ws)
