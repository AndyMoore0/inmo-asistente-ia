# 🤖 InmoAsistente IA - Sistema Automatizado de Atención y Calificación

Una solución de software integral (SaaS) diseñada específicamente para el sector inmobiliario. Este sistema automatiza la atención de interesados en propiedades en alquiler mediante Inteligencia Artificial, califica el perfil de los clientes mediante un filtro comercial y deriva los "leads" listos para cerrar directo al WhatsApp de la agencia.

---

## 🛠️ Arquitectura del Sistema

El proyecto está construido bajo una arquitectura cliente-servidor moderna y liviana, dividida en tres componentes principales:

### 1. Servidor Backend (`FastAPI` + Python)
Es el "motor" de la aplicación. Se encarga de procesar las peticiones, hablar con la base de datos y conectarse con los modelos de lenguaje.
* **Framework:** `FastAPI` por su alta velocidad de respuesta y manejo nativo de CORS para desarrollo local.
* **Integración de IA:** Conexión con la API de `Groq` para consumir el modelo **Llama 3.1 (8B Instant)**. Se configuró un *System Prompt* personalizado que moldea la personalidad del bot para que responda de forma cortita, al grano y con un tono cordial/profesional adaptado al mercado argentino.
* **Seguridad:** Implementación de Variables de Entorno (`os.environ.get`) para proteger las API Keys de accesos no autorizados.

### 2. Base de Datos (`SQLite`)
Un motor de base de datos relacional embebido que almacena la información de los inmuebles.
* **Estructura:** Cuenta con una tabla `propiedades` que registra: `id`, `direccion`, `precio`, `expensas` y `descripcion_completa`.
* El chat consume estos datos dinámicamente según el ID que reciba en la URL (`?id=X`), permitiendo que el mismo sistema sirva para infinitas propiedades en simultáneo.

### 3. Frontend Interactivo (`HTML5` + `CSS3` + `JavaScript`)
Una interfaz de usuario con enfoque *mobile-first* optimizada para simular una aplicación de celular de última generación.
* **Modularidad:** Al hacer clic en "Agendar Visita", se despliega un formulario interactivo (ventana modal) que pausa el chat para capturar los datos del cliente.
* **Conversión:** Si el usuario pasa el filtro de requisitos, el sistema inyecta dinámicamente un botón de acción directa hacia WhatsApp con un mensaje pre-armado de alta prioridad.

---## 🔮 Próximas Funcionalidades (Roadmap de Desarrollo)


Para transformar este MVP en una plataforma SaaS lista para comercializar a gran escala, se planifica la implementación de los siguientes módulos en las próximas fases:1. **🧮 Calculador Inteligente de Costos de Entrada:** Integración de lógica matemática para que la IA calcule automáticamente y en tiempo real el monto total requerido para firmar el contrato (mes de adelanto, depósito, sellados y honorarios notariales), redondeando los valores para mayor claridad del usuario.2. **📉 Simulador de Ajustes de Alquiler:** Incorporación de un módulo predictivo que simule los aumentos del canon locativo mensual en base a proyecciones de los índices oficiales (IPC/ICL) según la periodicidad del contrato, reduciendo la incertidumbre del inquilino.3. **🛡️ Filtro Avanzado y Validación de Garantías:** Evolución del formulario de pre-calificación para evaluar tipos específicos de respaldo (Garantía Propietaria, Seguros de Caución, Recibos de Sueldo) confrontándolos automáticamente contra las exigencias del propietario del inmueble antes de derivar el lead a WhatsApp.4. **🪄 Optimizador de Fichas Técnicas con IA:** Interfaz en el panel de administración para que la agencia pegue textos en crudo o desordenados y el modelo de lenguaje los estructure automáticamente en una descripción atractiva y estandarizada.

---## 📋 Flujo de Datos (Cómo funciona)

| Paso | Componente | Acción |
| :--- | :--- | :--- |
| **1** | `admin.html` | La inmobiliaria carga los datos y detalles comerciales de un departamento. |
| **2** | `Backend (API)` | El servidor recibe el JSON y lo guarda en la base de datos `SQLite`. Se genera un link único. |
| **3** | `demo.html` | El estudiante abre el link. El script lee el `?id=X` de la URL y precarga los textos desde la API. |
| **4** | `Chat con IA` | El usuario charla por teclado. Cada mensaje viaja al backend, se mezcla con la ficha del dpto y `Llama 3.1` responde con total coherencia humana. |
| **5** | `Filtro Comercial` | El usuario decide agendar. Completa el formulario y, si cumple los requisitos, el sistema desbloquea el WhatsApp directo del martillero. |

---

## 🛠️ Instalación y Uso Local

### Requisitos Previos
Tener instalado Python 3.10 o superior y las dependencias del proyecto:
```bash
pip install fastapi uvicorn groq
