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
            "DCF Method": "/valuate/dcf/",
            "Berkus Method": "/valuate/berkus/",
            "First Chicago Method": "/valuate/first_chicago/"
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

# Método de valuación Berkus
@app.post("/valuate/berkus/")
def berkus_method(data: StartupData):
    # El método Berkus asigna valor basado en 5 aspectos clave
    base_value = 500000  # Valor base por idea/concepto
    
    # Valoraciones basadas en revenue y growth rate
    management_value = min(500000, data.revenue * 0.2)  # Calidad del equipo de gestión
    product_value = min(500000, data.revenue * 0.3)     # Calidad/avance del producto
    market_value = min(500000, data.growth_rate * 1000000)  # Tamaño/potencial del mercado
    competition_value = min(500000, (1 - min(data.growth_rate, 0.5)) * 500000)  # Reducción por competencia
    
    total_valuation = base_value + management_value + product_value + market_value + competition_value
    return {"valuation": total_valuation}

# Método de valuación First Chicago
@app.post("/valuate/first_chicago/")
def first_chicago_method(data: StartupData):
    # First Chicago considera múltiples escenarios (éxito, lateral, fracaso)
    
    # Escenario optimista (éxito)
    success_probability = min(data.growth_rate * 2, 0.7)  # Mayor growth rate = más probabilidad de éxito
    success_valuation = data.revenue * 15  # Múltiplo más alto en caso de éxito
    
    # Escenario base (lateral)
    base_probability = 0.2
    base_valuation = data.revenue * 5  # Múltiplo moderado
    
    # Escenario pesimista (fracaso)
    failure_probability = 1 - success_probability - base_probability
    failure_valuation = data.investment_required * 0.5  # Valor de liquidación
    
    # Valoración ponderada por probabilidad
    weighted_valuation = (success_probability * success_valuation + 
                         base_probability * base_valuation + 
                         failure_probability * failure_valuation)
    
    return {"valuation": weighted_valuation}

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
