import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from supabase import create_client, Client

app = FastAPI()

# Configuración de CORS para que tus páginas de GitHub Pages puedan hablar con Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔑 Inicialización de las variables de entorno (Render las lee de tu panel)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Faltan las credenciales de Supabase en las variables de entorno.")

# Inicializamos los clientes de Supabase y Groq
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = Groq(api_key=GROQ_API_KEY)

# Modelo de datos que espera el formulario del admin.html
class Propiedad(BaseModel):
    direccion: str
    precio: float
    expensas: float
    descripcion: str


# 1️⃣ ENDPOINT: Guardar una propiedad en Supabase de forma permanente
@app.post("/api/propiedades")
async def guardar_propiedad(propiedad: Propiedad):
    try:
        response = supabase.table("propiedades").insert({
            "direccion": propiedad.direccion,
            "precio": propiedad.precio,
            "expensas": propiedad.expensas,
            "descripcion": propiedad.descripcion
        }).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Supabase no devolvió datos tras la inserción.")
            
        nuevo_id = response.data[0]["id"]
        return {"status": "success", "id": nuevo_id, "message": "Propiedad guardada para siempre"}
    except Exception as e:
        print(f"Error en POST propiedades: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en Supabase: {str(e)}")


# 2️⃣ ENDPOINT: Traer los datos de una propiedad para mostrar en la interfaz
@app.get("/api/propiedades/{propiedad_id}")
async def obtener_propiedad(propiedad_id: int):
    try:
        response = supabase.table("propiedades").select("*").eq("id", propiedad_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")
            
        return response.data[0]
    except Exception as e:
        print(f"Error en GET propiedad: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al consultar Supabase: {str(e)}")


# 3️⃣ ENDPOINT: El chat inteligente acoplado a Supabase y Groq
@app.post("/api/chat/{propiedad_id}")
async def chatear_propiedad(propiedad_id: int, data: dict):
    try:
        # Extraemos el mensaje del cuerpo enviado por el frontend
        mensaje_usuario = data.get("mensaje", "")
        if not mensaje_usuario:
            raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")

        # Buscamos la ficha técnica del dpto en Supabase
        response = supabase.table("propiedades").select("*").eq("id", propiedad_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada en la base de datos")
            
        propiedad = response.data[0]

        # Entrenamos a la IA con los datos reales de esta propiedad específica
        system_prompt = (
            f"Sos un asistente inmobiliario virtual de Argentina fluido y profesional. "
            f"Tu objetivo es responder consultas basándote ÚNICAMENTE en la siguiente información:\n"
            f"- Dirección: {propiedad['direccion']}\n"
            f"- Precio de Alquiler: ${propiedad['precio']}\n"
            f"- Expensas: ${propiedad['expensas']}\n"
            f"- Descripción y Condiciones: {propiedad['descripcion']}\n\n"
            f"Reglas: Responde de forma amable, clara y concisa. Usa modismos argentinos si es natural. "
            f"Si te preguntan por algo que NO está detallado en la descripción, responde amablemente que no dispones de esa información "
            f"en este momento pero que pueden coordinar con el martillero agendando una visita con el botón de abajo."
        )

        # Llamada a Groq usando Llama 3
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensaje_usuario}
            ],
            temperature=0.7,
            max_tokens=500
        )

        respuesta_ia = completion.choices[0].message.content
        return {"respuesta": respuesta_ia}

    except Exception as e:
        print(f"BOMBA EN EL CHAT: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno en el chat: {str(e)}")