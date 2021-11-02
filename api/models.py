from pydantic import BaseModel

class HealthItem(BaseModel):
    heart_rate: float
    oxygen_saturation: float

class EnvItem(BaseModel):
    temperature: float
    humidity: float