import os  
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from groq import Groq

app = FastAPI(title="InmoAsistente API - Backend con IA GRATIS")

# CONFIGURACIÓN DE GROQ PROFESIONAL (100% limpia para GitHub)
api_key_env = os.environ.get("GROQ_API_KEY")
if not api_key_env:
    # Esto es por si te olvidás de setearla localmente, para que no rompa sin avisar
    raise RuntimeWarning("ATENCIÓN: No se encontró la variable de entorno GROQ_API_KEY")

client = Groq(api_key=api_key_env)

# Habilitar CORS para que tus archivos HTML locales puedan comunicarse con el servidor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar la base de datos local SQLite
def init_db():
    conn = sqlite3.connect("inmo_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS propiedades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            direccion TEXT NOT NULL,
            precio REAL NOT NULL,
            expensas REAL NOT NULL,
            descripcion_completa TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Modelos de datos para las peticiones
class PropiedadIn(BaseModel):
    direccion: str
    precio: float
    expensas: float
    descripcion_completa: str

class ChatIn(BaseModel):
    propiedad_id: int
    mensaje_usuario: str

# 1. RUTA PARA GUARDAR UN DEPARTAMENTO (Desde admin.html)
@app.post("/api/propiedades")
def guardar_propiedad(propiedad: PropiedadIn):
    try:
        conn = sqlite3.connect("inmo_database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO propiedades (direccion, precio, expensas, descripcion_completa)
            VALUES (?, ?, ?, ?)
        """, (propiedad.direccion, propiedad.precio, propiedad.expensas, propiedad.descripcion_completa))
        conn.commit()
        propiedad_id = cursor.lastrowid
        conn.close()
        return {"status": "success", "message": "Propiedad guardada", "id": propiedad_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. RUTA PARA LEER LOS DATOS DE LA PROPIEDAD (Desde demo.html)
@app.get("/api/propiedades/{propiedad_id}")
def obtener_propiedad(propiedad_id: int):
    conn = sqlite3.connect("inmo_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT direccion, precio, expensas, descripcion_completa FROM propiedades WHERE id = ?", (propiedad_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
        
    return {"direccion": row[0], "precio": row[1], "expensas": row[2], "descripcion_completa": row[3]}

# 3. RUTA PARA PROCESAR EL CHAT CON IA OPTIMIZADA
@app.post("/api/chat")
def chatear_con_ia(chat: ChatIn):
    conn = sqlite3.connect("inmo_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT direccion, precio, expensas, descripcion_completa FROM propiedades WHERE id = ?", (chat.propiedad_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    direccion, precio, expensas, descripcion = row[0], row[1], row[2], row[3]

    # Rediseñamos las instrucciones para obligar a la IA a ser coherente y natural
    system_prompt = f"""
    Sos una asistente humana y súper profesional de una inmobiliaria en Bahía Blanca. Tu tarea es responder dudas sobre el dpto en {direccion}.
    
    REGLAS DE ORO PARA TU PERSONALIDAD:
    1. Hablá de forma natural, fluida y amigable (estilo argentino/bahiense, pero sin exagerar, neutro-cordial).
    2. Respuestas CORTAS y AL GRANO (máximo 2 o 3 oraciones). No metas discursos eternos de bienvenida si el usuario te dice algo corto como "hola" o "sí".
    3. Si el usuario te saluda o te dice algo genérico, respondé un saludo corto y preguntale qué duda específica tiene sobre el dpto.
    4. Usá EXCLUSIVAMENTE estos datos para responder:
       - Dirección: {direccion}
       - Alquiler: ${precio}
       - Expensas: ${expensas}
       - Detalles cargados: {descripcion}
    5. Si te preguntan algo que NO está en los detalles de arriba, decí: "Mirá, no tengo ese dato exacto acá en la ficha, pero si querés podés consultarlo directo con el martillero al agendar la visita al final."
    """

    try:
        # Llamada a Groq con el modelo Llama 3.1
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": chat.mensaje_usuario}
            ],
            temperature=0.4  # Temperatura baja para evitar que invente cosas o se vaya por las ramas
        )
        respuesta_ia = response.choices[0].message.content
        return {"respuesta": respuesta_ia}
    except Exception as e:
        print("\n❌ ERROR DETECTADO EN GROQ:", str(e), "\n")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)