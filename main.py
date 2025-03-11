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

# Configurar CORS para permitir solicitudes desde orígenes específicos
origins = [
    "https://api-valuaciones.onrender.com",
    "https://v0-crear-front-api.vercel.app",
    # Añadir la URL de tu Replit deployment
    "https://" + os.environ.get("REPL_SLUG", "startup-valuation-api") + "." + os.environ.get("REPL_OWNER", "replit") + ".repl.co"
]

# Para desarrollo y testing, permitir orígenes adicionales
if os.environ.get("ALLOW_ALL_ORIGINS", "false").lower() == "true":
    origins.append("*")
    allow_creds = False
else:
    allow_creds = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_creds,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Añadir middleware para logging de peticiones
@app.middleware("http")
async def log_requests(request, call_next):
    import time
    start_time = time.time()

    # Log request details
    print(f"Request: {request.method} {request.url}")
    if request.method in ["POST", "PUT"]:
        try:
            body = await request.body()
            print(f"Request body: {body.decode()}")
        except Exception as e:
            print(f"Could not log request body: {e}")

    response = await call_next(request)

    # Log response details
    process_time = time.time() - start_time
    print(f"Response status: {response.status_code}")
    print(f"Process time: {process_time:.4f} seconds")

    return response

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

@app.get("/status")
def check_status():
    return {"status": "online", "message": "API funcionando correctamente"}

@app.get("/diagnostico")
def diagnostico():
    """Endpoint para verificar el estado completo de la API"""
    import sys
    import platform

    # Información de configuración
    cors_origins = app.user_middleware[0].options.get("allow_origins", [])

    return {
        "status": "online",
        "version": app.version,
        "python_version": sys.version,
        "sistema_operativo": platform.system(),
        "endpoints_disponibles": {
            "root": "/",
            "status": "/status",
            "test_client": "/test",
            "vc_method": ["/valuate/vc_method/", "/valuate/vc-method/"],
            "dcf_method": ["/valuate/dcf/", "/valuate/dcf-method/"],
            "berkus_method": ["/valuate/berkus/", "/valuate/berkus-method/"],
            "first_chicago_method": ["/valuate/first_chicago/", "/valuate/first-chicago/"]
        },
        "cors": {
            "origins": cors_origins,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        }
    }

# Modelo de datos que ingresará el usuario
class StartupData(BaseModel):
    name: str
    revenue: float
    growth_rate: float
    investment_required: float

# Modelo específico para DCF
class DCFData(BaseModel):
    initial_cash_flow: float
    growth_rate: float
    discount_rate: float = 0.15
    terminal_growth_rate: float = 0.03
    projection_years: int = 5

# Modelo específico para VC Method
class VCData(BaseModel):
    name: str = "Startup X"
    revenue: float
    growth_rate: float 
    investment_required: float = 500000
    # Campos opcionales para compatibilidad con el formato DCF
    initial_cash_flow: float = None
    discount_rate: float = None
    terminal_growth_rate: float = None
    projection_years: int = None

# Método de valuación Venture Capital (VC Method)
@app.post("/valuate/vc_method/")
@app.post("/valuate/vc-method/")  # Ruta alternativa con guión para mayor compatibilidad
def vc_method(data: dict | VCData | StartupData | DCFData):
    try:
        # Si es un diccionario, convertirlo a un objeto
        if isinstance(data, dict):
            try:
                # Intentar convertir a StartupData primero
                data = StartupData(**data)
            except Exception as e:
                try:
                    # Si falla, intentar con DCFData
                    data = DCFData(**data)
                except Exception as e2:
                    # Si ambos fallan, usar VCData que tiene más campos opcionales
                    data = VCData(**data)

        # Extraer los valores necesarios del modelo de datos
        revenue = getattr(data, "revenue", None)
        if revenue is None and hasattr(data, "initial_cash_flow"):
            revenue = data.initial_cash_flow

        growth_rate = getattr(data, "growth_rate", 0.2)
        # Si el crecimiento viene en porcentaje (20 en vez de 0.2)
        if growth_rate > 1:
            growth_rate = growth_rate / 100

        # Validación de datos
        if revenue is None or revenue <= 0:
            return {"valuation": 0, "error": "Los ingresos deben ser positivos"}

        # Cálculo del valor de salida considerando el crecimiento
        multiple = max(5, 10 + growth_rate * 10)  # Ajusta el múltiplo según el crecimiento
        exit_value = revenue * multiple

        # El retorno esperado por inversores varía según el riesgo
        investor_return = max(3, 8 - growth_rate * 5)  # Menor crecimiento = mayor retorno requerido

        valuation = exit_value / investor_return
        return {"valuation": round(valuation, 2)}
    except Exception as e:
        print(f"Error en el cálculo VC Method: {e}")
        return {"valuation": 0, "error": f"Error al calcular: {str(e)}"}

# Método de valuación Descuento de Flujos de Caja (DCF)
@app.post("/valuate/dcf/")
@app.post("/valuate/dcf-method/")  # Ruta alternativa con guión para mayor compatibilidad
def dcf_method(data: dict | DCFData | StartupData):
    print(f"DCF Method received data: {data}")
    try:
        # Si es un diccionario, convertirlo a un objeto tipo BaseModel
        if isinstance(data, dict):
            try:
                # Intentar convertir a DCFData primero
                if 'initial_cash_flow' in data:
                    # Asegurarse de que todos los campos requeridos existan
                    if 'terminal_growth_rate' not in data:
                        data['terminal_growth_rate'] = 0.03
                    if 'discount_rate' not in data:
                        data['discount_rate'] = 0.15
                    if 'projection_years' not in data:
                        data['projection_years'] = 5
                    data = DCFData(**data)
                else:
                    # Si no tiene initial_cash_flow, convertir a StartupData
                    data = StartupData(**data)
            except Exception as e:
                # Si falla la conversión, intentar con StartupData como fallback
                print(f"Error al convertir datos: {e}")
                try:
                    data = StartupData(**data)
                except:
                    # Crear un objeto DCFData mínimo si todo falla
                    default_data = {
                        'initial_cash_flow': 100000,
                        'growth_rate': 0.2,
                        'discount_rate': 0.15,
                        'terminal_growth_rate': 0.03,
                        'projection_years': 5
                    }
                    # Actualizar con los datos proporcionados si existen
                    for key, value in data.items():
                        if key in default_data:
                            default_data[key] = value
                    data = DCFData(**default_data)

        # Compatibilidad con ambos modelos
        if hasattr(data, 'revenue') and not hasattr(data, 'initial_cash_flow'):
            # Usar el modelo StartupData
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
        else:
            # Usar el modelo DCFData
            # Validación
            if getattr(data, 'initial_cash_flow', 0) <= 0:
                return {"valuation": 0, "error": "El flujo de caja inicial debe ser positivo"}

            # Asegurarse de que todos los campos necesarios están presentes
            initial_cash_flow = getattr(data, 'initial_cash_flow', 0)
            growth_rate = getattr(data, 'growth_rate', 0.2)
            discount_rate = getattr(data, 'discount_rate', 0.1)
            terminal_growth_rate = getattr(data, 'terminal_growth_rate', 0.03)
            projection_years = getattr(data, 'projection_years', 5)

            # Convertir porcentajes si es necesario (si vienen como 20 en lugar de 0.2)
            growth_rate = growth_rate / 100 if growth_rate > 1 else growth_rate
            discount_rate = discount_rate / 100 if discount_rate > 1 else discount_rate
            terminal_growth_rate = terminal_growth_rate / 100 if terminal_growth_rate > 1 else terminal_growth_rate

            # Evitar división por cero
            if discount_rate <= terminal_growth_rate:
                discount_rate = terminal_growth_rate + 0.01

            # Cálculo del valor presente de los flujos futuros
            total_value = 0
            cash_flow = initial_cash_flow

            for year in range(1, projection_years + 1):
                cash_flow *= (1 + growth_rate)
                # Valor presente del flujo
                total_value += cash_flow / ((1 + discount_rate) ** year)

            # Valor terminal (perpetuidad)
            terminal_value = (cash_flow * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
            terminal_value_discounted = terminal_value / ((1 + discount_rate) ** projection_years)

            valuation = total_value + terminal_value_discounted

        return {"valuation": round(valuation, 2)}
    except Exception as e:
        print(f"Error en el cálculo DCF: {e}")
        return {"valuation": 0, "error": f"Error al calcular: {str(e)}"}

# Método de valuación Berkus
@app.post("/valuate/berkus/")
@app.post("/valuate/berkus-method/")  # Ruta alternativa con guión para mayor compatibilidad
def berkus_method(data: dict | StartupData | DCFData):
    try:
        # Si es un diccionario, convertirlo a StartupData o manejar DCFData
        if isinstance(data, dict):
            try:
                # Intentar convertir a StartupData primero
                data = StartupData(**data)
            except Exception as e:
                # Si falla, intentar con DCFData o crear objeto compatible
                try:
                    # Si tiene initial_cash_flow, tratar como DCFData
                    if 'initial_cash_flow' in data:
                        # Crear un objeto DCFData
                        dcf_data = {}
                        for key in ['initial_cash_flow', 'growth_rate', 'discount_rate', 'terminal_growth_rate', 'projection_years']:
                            if key in data:
                                dcf_data[key] = data[key]
                        data = DCFData(**dcf_data)
                    else:
                        # Crear un objeto StartupData con valores por defecto
                        startup_data = {
                            'name': 'Startup X',
                            'revenue': 1000000,
                            'growth_rate': 0.2,
                            'investment_required': 500000
                        }
                        # Actualizar con los datos proporcionados
                        for key, value in data.items():
                            if key in startup_data:
                                startup_data[key] = value
                        data = StartupData(**startup_data)
                except Exception as e2:
                    print(f"Error al convertir datos: {e2}")
                    # Crear un objeto mínimo si todo falla
                    data = StartupData(
                        name="Startup X",
                        revenue=1000000,
                        growth_rate=0.2,
                        investment_required=500000
                    )

        # Asegurarse de tener campos necesarios
        revenue = getattr(data, 'revenue', None)
        if revenue is None and hasattr(data, 'initial_cash_flow'):
            revenue = data.initial_cash_flow

        growth_rate = getattr(data, 'growth_rate', 0.2)
        # Si el crecimiento viene en porcentaje (20 en vez de 0.2)
        if growth_rate > 1:
            growth_rate = growth_rate / 100

        investment_required = getattr(data, 'investment_required', 500000)

        # Validación
        if revenue is None or revenue <= 0:
            return {"valuation": 0, "error": "Los ingresos deben ser positivos"}

        # El método Berkus asigna valor basado en 5 aspectos clave
        # Cada aspecto puede valer entre 0 y 500,000 USD

        # Valor base por idea/concepto
        base_value = 500000

        # Calidad del equipo de gestión (aproximada por ingresos)
        revenue_factor = min(1.0, revenue / 2000000)
        management_value = 500000 * revenue_factor

        # Calidad/avance del producto
        product_factor = min(1.0, max(0.2, revenue / 1000000))
        product_value = 500000 * product_factor

        # Tamaño/potencial del mercado
        market_factor = min(1.0, max(0.1, growth_rate * 2))
        market_value = 500000 * market_factor

        # Reducción del riesgo por competencia
        competition_factor = min(1.0, max(0.1, 1 - (growth_rate / 2)))
        competition_value = 500000 * competition_factor

        # Riesgo financiero (basado en inversión requerida vs ingresos)
        financial_ratio = min(1.0, max(0.1, revenue / max(1, investment_required)))
        financial_value = 500000 * financial_ratio

        total_valuation = base_value + management_value + product_value + market_value + competition_value + financial_value
        return {"valuation": round(total_valuation, 2)}
    except Exception as e:
        print(f"Error en el cálculo Berkus: {e}")
        return {"valuation": 0, "error": f"Error al calcular: {str(e)}"}

# Método de valuación First Chicago
@app.post("/valuate/first_chicago/")
@app.post("/valuate/first-chicago/")  # Ruta alternativa con guión para mayor compatibilidad
def first_chicago_method(data: dict | StartupData | DCFData):
    try:
        # Si es un diccionario, convertirlo a StartupData o manejar DCFData
        if isinstance(data, dict):
            try:
                # Intentar convertir a StartupData primero
                data = StartupData(**data)
            except Exception as e:
                # Si falla, intentar con DCFData o crear objeto compatible
                try:
                    # Si tiene initial_cash_flow, tratar como DCFData
                    if 'initial_cash_flow' in data:
                        # Crear un objeto DCFData
                        dcf_data = {}
                        for key in ['initial_cash_flow', 'growth_rate', 'discount_rate', 'terminal_growth_rate', 'projection_years']:
                            if key in data:
                                dcf_data[key] = data[key]
                        data = DCFData(**dcf_data)
                    else:
                        # Crear un objeto StartupData con valores por defecto
                        startup_data = {
                            'name': 'Startup X',
                            'revenue': 1000000,
                            'growth_rate': 0.2,
                            'investment_required': 500000
                        }
                        # Actualizar con los datos proporcionados
                        for key, value in data.items():
                            if key in startup_data:
                                startup_data[key] = value
                        data = StartupData(**startup_data)
                except Exception as e2:
                    print(f"Error al convertir datos: {e2}")
                    # Crear un objeto mínimo si todo falla
                    data = StartupData(
                        name="Startup X",
                        revenue=1000000,
                        growth_rate=0.2,
                        investment_required=500000
                    )

        # Asegurarse de tener campos necesarios
        revenue = getattr(data, 'revenue', None)
        if revenue is None and hasattr(data, 'initial_cash_flow'):
            revenue = data.initial_cash_flow

        growth_rate = getattr(data, 'growth_rate', 0.2)
        # Si el crecimiento viene en porcentaje (20 en vez de 0.2)
        if growth_rate > 1:
            growth_rate = growth_rate / 100

        investment_required = getattr(data, 'investment_required', 500000)

        # Validación
        if revenue is None or revenue <= 0:
            return {"valuation": 0, "error": "Los ingresos deben ser positivos"}

        # First Chicago considera múltiples escenarios (éxito, lateral, fracaso)

        # Escenario optimista (éxito)
        success_probability = min(0.7, max(0.1, growth_rate))
        success_multiple = 15 + (growth_rate * 10)
        success_valuation = revenue * success_multiple

        # Escenario base (lateral)
        base_probability = min(0.7, max(0.2, 0.5 - growth_rate/2))
        base_multiple = 5 + (growth_rate * 3)
        base_valuation = revenue * base_multiple

        # Escenario pesimista (fracaso)
        failure_probability = max(0.1, 1 - success_probability - base_probability)
        failure_multiple = max(0.2, min(1.0, investment_required / revenue))
        failure_valuation = revenue * failure_multiple

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
    except Exception as e:
        print(f"Error en el cálculo First Chicago: {e}")
        return {"valuation": 0, "error": f"Error al calcular: {str(e)}"}

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
        print(f"Iniciando servidor en puerto {port}...")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Error al iniciar el servidor en puerto {port}: {e}")
        # Intentar con puerto alternativo
        try:
            port = 3000
            print(f"Intentando con puerto alternativo {port}...")
            uvicorn.run(app, host="0.0.0.0", port=port)
        except Exception as e:
            print(f"Error al iniciar el servidor en puerto alternativo: {e}")