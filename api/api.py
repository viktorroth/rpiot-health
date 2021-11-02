import os
from typing import Optional
from fastapi import FastAPI
from fastapi.routing import APIRouter
from databases import Database
from models import HealthItem, EnvItem
from twilio.rest import Client


app = FastAPI()

database = Database("sqlite:///backend.db")

@app.on_event("startup")
async def database_connect():
    await database.connect()

    health_query = """
        CREATE TABLE IF NOT EXISTS health (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            heart_rate REAL NOT NULL,
            oxygen_saturation REAL NOT NULL,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    await database.execute(query=health_query)

    env_query = """
        CREATE TABLE IF NOT EXISTS environment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    await database.execute(query=env_query)

@app.on_event("shutdown")
async def database_disconnect():
    await database.disconnect()

@app.get("/ping")
async def ping():
    """Check if API is up and running"""
    return {'ping': 'pong'}

@app.get("/health")
async def get_health_measurements():
    """Return all health measurements"""
    query = "SELECT * FROM health"
    results = await database.fetch_all(query=query)
    return  results

@app.post("/health")
async def add_health_measurement(item: HealthItem):
    """Add a health measurement"""
    query = "INSERT INTO health (heart_rate, oxygen_saturation) VALUES (:heart_rate, :oxygen_saturation)"
    results = await database.execute(query=query, values=item.dict())
    return  results

@app.get("/env")
async def get_env_measurements():
    """Return all environment measurements"""
    query = "SELECT * FROM environment"
    results = await database.fetch_all(query=query)
    return  results

@app.post("/env")
async def add_env_measurement(item: EnvItem):
    """Add a measurement from the environment"""
    query = "INSERT INTO environment (temperature, humidity) VALUES (:temperature, :humidity)"
    results = await database.execute(query=query, values=item.dict())
    return  results

@app.post("/sms_alert")
async def sms_alert(item: HealthItem):
    """Send an SMS alert through Twilio"""
    account_sid = os.environ['TWILIO_ACCOUNT_SID'] 
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_number = os.environ['TWILIO_PHONE_NUMBER']
    personal_number = os.environ['PERSONAL_PHONE_NUMBER']

    client = Client(account_sid, auth_token)
    message = f'ENG103 | Viktor Roth | Health Alert - HR: {item.heart_rate:.2f} Oxygen level: {item.oxygen_saturation:.2f} %'
    res = client.messages.create(body=message, from_=twilio_number, to=personal_number)
    return {'status': res.status}