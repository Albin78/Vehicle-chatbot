import os
import json
import httpx
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# -------------------------
# CORS
# -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# MongoDB (ASYNC)
# -------------------------
mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URI"))
db = mongo_client[os.getenv("MONGO_DB")]
collection = db[os.getenv("MONGO_COLLECTION")]

# -------------------------
# Ollama
# -------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")


# -------------------------
# Format Vehicle Data
# -------------------------
def format_vehicle_context(data):

    def safe_dt(val):
        return val.strftime("%Y-%m-%d %H:%M:%S") if isinstance(val, datetime) else str(val)

    return {
        "IMEI": data.get("imei"),
        "Last Updated": safe_dt(data.get("last_updated")),
        "Latitude": data.get("lat"),
        "Longitude": data.get("lon"),
        "Location": f"https://www.google.com/maps?q={data.get('lat')},{data.get('lon')}" if data.get("lat") and data.get("lon") else None,
        "Speed": data.get("speed"),
        "Engine RPM": data.get("engineRpm"),
        "Ignition": "On" if data.get("ignitionOn") == "1" else "Off",
        "Moving": "Yes" if data.get("moving") else "No",
        "Altitude": data.get("altitude"),
        "Odometer": data.get("odometerCurrentReading"),
        "Engine Temperature": data.get("engineTemperature"),
        "Driver ID": data.get("DriverID"),
        "Battery": data.get("battery_level")
    }


# -------------------------
# Build Prompt
# -------------------------
def build_prompt(vehicle_data_list, question, all_records=False):

    if all_records:

        context = "\n\n".join(
            [
                f"Record {i+1}:\n"
                + "\n".join([f"{k}: {v}" for k, v in record.items()])
                for i, record in enumerate(vehicle_data_list)
            ]
        )

    else:

        latest = vehicle_data_list[-1]

        context = "\n".join([f"{k}: {v}" for k, v in latest.items()])

    return f"""
You are a VMS (Vehicle Monitoring System) bot.

You ONLY answer questions related to the vehicle data below.

If the question is unrelated respond ONLY:
"I am a VMS bot, so I am unable to answer the question."

Vehicle Data:
{context}

Question: {question}
Answer:
""".strip()


# -------------------------
# Async Ollama Call
# -------------------------
async def ask_ollama(prompt):

    async with httpx.AsyncClient(timeout=60) as client:

        response = await client.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
        )

    if response.status_code == 200:
        return response.json().get("response", "").strip()

    return "Error: Ollama request failed"


# -------------------------
# Fetch Records (ASYNC)
# -------------------------
async def fetch_all_records(imei, limit=500):

    cursor = collection.find({"imei": imei}).sort("last_updated", 1).limit(limit)

    records = []

    async for record in cursor:
        records.append(format_vehicle_context(record))

    return records


# -------------------------
# WebSocket Chat
# -------------------------
@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):

    await websocket.accept()

    imei = None

    try:

        while True:

            message = await websocket.receive_text()
            data = json.loads(message)

            # ----------------
            # Set IMEI
            # ----------------
            if "imei" in data:

                imei = data["imei"]

                await websocket.send_text(f"Connected to IMEI: {imei}")

                continue

            # ----------------
            # Question
            # ----------------
            if "question" in data:

                if not imei:

                    await websocket.send_text("Please send IMEI first.")
                    continue

                vehicle_data_list = await fetch_all_records(imei)

                if not vehicle_data_list:

                    await websocket.send_text("No data found for this IMEI.")
                    continue

                question = data["question"]

                all_records = any(
                    keyword in question.lower()
                    for keyword in [
                        "all",
                        "average",
                        "history",
                        "total",
                        "records",
                        "trend",
                        "day",
                        "week",
                        "month",
                    ]
                )

                prompt = build_prompt(vehicle_data_list, question, all_records)

                response = await ask_ollama(prompt)

                await websocket.send_text(response)

    except WebSocketDisconnect:

        print("Client disconnected")