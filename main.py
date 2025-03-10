from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

# Crear la API
app = FastAPI(
    title="Startup Valuation API",
    description="API for valuing startups using different methods",
    version="1.0.0"
)

# Configurar CORS para permitir solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://tudominio-vercel.vercel.app"],  # Reemplaza con tu dominio real de Vercel
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
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
    # Validación de datos
    if data.revenue <= 0:
        return {"valuation": 0, "error": "Los ingresos deben ser positivos"}
    
    # Cálculo del valor de salida considerando el crecimiento
    multiple = max(5, 10 + data.growth_rate * 10)  # Ajusta el múltiplo según el crecimiento
    exit_value = data.revenue * multiple
    
    # El retorno esperado por inversores varía según el riesgo
    investor_return = max(3, 8 - data.growth_rate * 5)  # Menor crecimiento = mayor retorno requerido
    
    valuation = exit_value / investor_return
    return {"valuation": round(valuation, 2)}

# Método de valuación Descuento de Flujos de Caja (DCF)
@app.post("/valuate/dcf/")
def dcf_method(data: StartupData):
    # Validación de datos
    if data.revenue <= 0:
        return {"valuation": 0, "error": "Los ingresos deben ser positivos"}
    
    # Tasa de descuento ajustada al riesgo
    base_discount_rate = 0.1  # Base del 10%
    risk_adjustment = min(0.2, max(0.05, 0.25 - data.growth_rate))  # Menor crecimiento = mayor riesgo
    discount_rate = base_discount_rate + risk_adjustment
    
    # Proyección de flujos por 5 años
    total_value = 0
    annual_revenue = data.revenue
    
    for year in range(1, 6):
        annual_revenue *= (1 + data.growth_rate)
        # Asumiendo un margen operativo del 20%
        cash_flow = annual_revenue * 0.2
        # Valor presente del flujo
        total_value += cash_flow / ((1 + discount_rate) ** year)
    
    # Valor terminal (perpetuidad)
    terminal_growth = min(0.03, data.growth_rate / 3)  # Crecimiento terminal conservador
    terminal_value = (annual_revenue * 0.2 * (1 + terminal_growth)) / (discount_rate - terminal_growth)
    terminal_value_discounted = terminal_value / ((1 + discount_rate) ** 5)
    
    valuation = total_value + terminal_value_discounted
    return {"valuation": round(valuation, 2)}

# Método de valuación Berkus
@app.post("/valuate/berkus/")
def berkus_method(data: StartupData):
    # El método Berkus asigna valor basado en 5 aspectos clave
    # Cada aspecto puede valer entre 0 y 500,000 USD
    
    # Valor base por idea/concepto
    base_value = 500000
    
    # Calidad del equipo de gestión (aproximada por ingresos)
    revenue_factor = min(1.0, data.revenue / 2000000)
    management_value = 500000 * revenue_factor
    
    # Calidad/avance del producto
    product_factor = min(1.0, max(0.2, data.revenue / 1000000))
    product_value = 500000 * product_factor
    
    # Tamaño/potencial del mercado
    market_factor = min(1.0, max(0.1, data.growth_rate * 2))
    market_value = 500000 * market_factor
    
    # Reducción del riesgo por competencia
    competition_factor = min(1.0, max(0.1, 1 - (data.growth_rate / 2)))
    competition_value = 500000 * competition_factor
    
    # Riesgo financiero (basado en inversión requerida vs ingresos)
    financial_ratio = min(1.0, max(0.1, data.revenue / max(1, data.investment_required)))
    financial_value = 500000 * financial_ratio
    
    total_valuation = base_value + management_value + product_value + market_value + competition_value + financial_value
    return {"valuation": round(total_valuation, 2)}

# Método de valuación First Chicago
@app.post("/valuate/first_chicago/")
def first_chicago_method(data: StartupData):
    # First Chicago considera múltiples escenarios (éxito, lateral, fracaso)
    
    # Validación de datos
    if data.revenue <= 0:
        return {"valuation": 0, "error": "Los ingresos deben ser positivos"}
    
    # Escenario optimista (éxito)
    success_probability = min(0.7, max(0.1, data.growth_rate))
    success_multiple = 15 + (data.growth_rate * 10)
    success_valuation = data.revenue * success_multiple
    
    # Escenario base (lateral)
    base_probability = min(0.7, max(0.2, 0.5 - data.growth_rate/2))
    base_multiple = 5 + (data.growth_rate * 3)
    base_valuation = data.revenue * base_multiple
    
    # Escenario pesimista (fracaso)
    failure_probability = max(0.1, 1 - success_probability - base_probability)
    failure_multiple = max(0.2, min(1.0, data.investment_required / data.revenue))
    failure_valuation = data.revenue * failure_multiple
    
    # Normalización de probabilidades
    total_probability = success_probability + base_probability + failure_probability
    success_probability /= total_probability
    base_probability /= total_probability
    failure_probability /= total_probability
    
    # Valoración ponderada por probabilidad
    weighted_valuation = (
        success_probability * success_valuation + 
        base_probability * base_valuation + 
        failure_probability * failure_valuation
    )
    
    # Detalles de cada escenario para mayor transparencia
    scenarios = {
        "success": {
            "probability": round(success_probability, 2),
            "valuation": round(success_valuation, 2)
        },
        "base": {
            "probability": round(base_probability, 2),
            "valuation": round(base_valuation, 2)
        },
        "failure": {
            "probability": round(failure_probability, 2),
            "valuation": round(failure_valuation, 2)
        }
    }
    
    return {
        "valuation": round(weighted_valuation, 2),
        "scenarios": scenarios
    }

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
    # Usar puerto 8080 directamente
    port = 8080
    try:
        # Primero matar cualquier proceso que pueda estar usando el puerto
        import os
        os.system(f"pkill -f 'uvicorn' || true")
        
        print(f"Iniciando servidor en puerto {port}...")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")
        # Si el puerto 8080 está ocupado, usar otro puerto
        try:
            port = 3000
            print(f"Intentando con puerto {port}...")
            uvicorn.run(app, host="0.0.0.0", port=port)
        except Exception:
            # Como último recurso, usar un puerto aleatorio
            print("Usando puerto aleatorio...")
            uvicorn.run(app, host="0.0.0.0", port=0)
