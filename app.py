import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from groq import Groq

app = FastAPI(title="InmoAsistente API - Backend con Supabase Permanente")

# Habilitar CORS para conectar tus HTML de GitHub Pages y locales
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔐 CONFIGURACIÓN DE SEGURIDAD (Variables de Entorno)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not all([GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    raise RuntimeWarning("ATENCIÓN: Faltan configurar variables de entorno obligatorias.")

# Inicializar clientes de las APIs de la nube
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# Modelo de datos para recibir propiedades desde el admin.html
class Propiedad(BaseModel):
    direccion: str
    precio: float
    expensas: float
    descripcion: str

# 1️⃣ ENDPOINT: Guardar una propiedad en Supabase de forma permanente
@app.post("/api/propiedades")
async def guardar_propiedad(propiedad: Propiedad):
    try:
        data, count = supabase.table("propiedades").insert({
            "direccion": propiedad.direccion,
            "precio": propiedad.precio,
            "expensas": propiedad.expensas,
            "descripcion": propiedad.descripcion
        }).execute()
        
        # Devolvemos el ID que le asignó automáticamente la base de datos
        nuevo_id = data[1][0]["id"]
        return {"status": "success", "id": nuevo_id, "message": "Propiedad guardada para siempre"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en Supabase: {str(e)}")

# 2️⃣ ENDPOINT: Buscar una propiedad por ID para el Chatbot
@app.get("/api/propiedades/{propiedad_id}")
async def obtener_propiedad(propiedad_id: int):
    try:
        response = supabase.table("propiedades").select("*").eq("id", propiedad_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3️⃣ ENDPOINT: El cerebro del Chatbot (IA Groq + Llama 3)
@app.post("/api/chat/{propiedad_id}")
async def chat_propiedad(propiedad_id: int, mensaje: dict):
    # Buscamos la propiedad directo en Supabase
    prop_resp = supabase.table("propiedades").select("*").eq("id", propiedad_id).execute()
    if not prop_resp.data:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    
    propiedad = prop_resp.data[0]
    user_msg = mensaje.get("mensaje", "")

    # Contexto ultra personalizado para defender las condiciones inmobiliarias
    system_prompt = f"""
    Sos un asistente virtual experto de una inmobiliaria argentina. Tu objetivo es responder consultas de inquilinos basándote ÚNICAMENTE en la siguiente información de la propiedad.
    Si te preguntan algo que NO está especificado acá, decí amablemente que no tenés ese dato y que dejen su consulta para que un agente humano los contacte.

    INFORMACIÓN REAL DE LA PROPIEDAD:
    - Dirección: {propiedad['direccion']}
    - Alquiler Mensual: ${propiedad['precio']:,} ARS
    - Expensas: ${propiedad['expensas']:,} ARS
    - Detalles y Requisitos Excluyentes: {propiedad['descripcion']}

    REGLAS DE ORO:
    1. Sé cordial, profesional y usá modismos argentinos neutros (che, cómo va, claro, etc.).
    2. Respondé de forma corta y precisa, ideal para leer rápido desde un celular.
    3. Si el usuario cumple con el perfil o quiere agendar, indicale amablemente que use el botón de agendar visita.
    """

    try:
        completion = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.5,
        )
        return {"respuesta": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la IA: {str(e)}")