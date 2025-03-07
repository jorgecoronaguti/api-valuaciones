from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Crear la API
app = FastAPI(
    title="Startup Valuation API",
    description="API for valuing startups using different methods",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Startup Valuation API",
        "endpoints": {
            "VC Method": "/valuate/vc_method/",
            "DCF Method": "/valuate/dcf/"
        }
    }

# Modelo de datos que ingresará el usuario
class StartupData(BaseModel):
    name: str
    revenue: float
    growth_rate: float
    investment_required: float

# Método de valuación Venture Capital (VC Method)
@app.post("/valuate/vc_method/")
def vc_method(data: StartupData):
    exit_value = data.revenue * 10  # Suponemos un múltiplo de 10x
    investor_return = 5  # Suponemos retorno de 5x
    valuation = exit_value / investor_return
    return {"valuation": valuation}

# Método de valuación Descuento de Flujos de Caja (DCF)
@app.post("/valuate/dcf/")
def dcf_method(data: StartupData):
    discount_rate = 0.1  # Tasa de descuento del 10%
    projected_cash_flow = data.revenue * (1 + data.growth_rate)
    discounted_value = projected_cash_flow / (1 + discount_rate)
    return {"valuation": discounted_value}

# Endpoint para servir el cliente de prueba HTML
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

@app.get("/test", response_class=HTMLResponse)
async def get_test_client():
    with open("test_client.html", "r") as f:
        return f.read()

# Ejecutar la API si se ejecuta el archivo
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
