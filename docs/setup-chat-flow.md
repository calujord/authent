# Setup Chat — Guía de integración para Frontend

> Endpoint base: `/api/hub/projects/{project_id}/setup/chat/`  
> Auth: Bearer Token (JWT)

---

## Resumen

El Setup Chat es un **asistente conversacional** que guía al usuario paso a paso para configurar su bot de WhatsApp. Funciona como un chat normal: el usuario envía mensajes y recibe respuestas del asistente.

El proceso tiene **3 etapas internas**. El backend informa en qué etapa está a través del campo `current_section`:

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
│  identity    │ ──▶ │    behavior      │ ──▶ │    review      │
│  Identidad   │     │  Comportamiento  │     │    Revisión    │
│  del negocio │     │    del bot       │     │  y confirmación│
└──────────────┘     └──────────────────┘     └────────────────┘
```

---

## Layout de pantalla: Panel izquierdo + Chat

```
┌─────────────────────────────┬─────────────────────────────────────────┐
│  CONFIGURACIÓN DEL BOT      │  Chat                                   │
│                             │                                         │
│  ● Identidad ← activa      │  🤖 ¡Hola! Soy tu asistente de         │
│  ○ Comportamiento           │     configuración. ¿Cómo se llama      │
│  ○ Revisión                 │     tu negocio?                        │
│                             │                                         │
│  ─────────────────────      │              Somos Gafas Virtuals ORG  │
│                             │              vendemos gafas de         │
│  Datos recopilados:         │              realidad aumentada     👤 │
│                             │                                         │
│  Negocio: Gafas Virtuals    │  🤖 ¡Qué interesante! ¿Qué tipo de    │
│  Descripción: Venta de...   │     consultas reciben más?             │
│  Servicios: (pendiente)     │                                         │
│  Tono: (pendiente)          │  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│                             │                                         │
│  ─────────────────────      │                                         │
│                             │                                         │
│  INTEGRACIONES              │                                         │
│                             │                                         │
│  🔌 Iris (Base de           │                                         │
│     conocimiento)           │                                         │
│     [ Configurar ]          │                                         │
│                             │                                         │
│  🔌 Atlas CRM               │                                         │
│     [ Configurar ]          │                                         │
│                             │                                         │
├─────────────────────────────┼─────────────────────────────────────────┤
│                             │  [  Escribe tu mensaje...   ] [➤]       │
└─────────────────────────────┴─────────────────────────────────────────┘
```

---

## Panel izquierdo: Etapas del flujo

Usar `current_section` de la respuesta para marcar la etapa activa.

### Definición de etapas (hardcoded en el frontend)

```dart
// O su equivalente en el framework que uses
final sections = [
  {
    "key": "identity",
    "label": "Identidad del negocio",
    "icon": "🏢",
    "fields": [
      { "key": "company",      "label": "Nombre del negocio" },
      { "key": "description",  "label": "Descripción" },
      { "key": "specialties",  "label": "Servicios principales" },
      { "key": "tone",         "label": "Tono de comunicación" },
    ]
  },
  {
    "key": "behavior",
    "label": "Comportamiento del bot",
    "icon": "🤖",
    "fields": [
      { "key": "message_types", "label": "Tipos de consultas" },
      { "key": "appointments",  "label": "Ofrece agendar citas" },
      { "key": "special_rules", "label": "Instrucciones especiales" },
    ]
  },
  {
    "key": "review",
    "label": "Revisión y confirmación",
    "icon": "✅",
    "fields": []
  }
];
```

### Estado visual de cada etapa

| Condición | Indicador visual |
|-----------|-----------------|
| Etapa anterior a `current_section` | ✅ Completada (check verde) |
| Etapa igual a `current_section` | 🔵 Activa (resaltada, punto azul) |
| Etapa posterior a `current_section` | ⚪ Pendiente (gris, icono vacío) |
| `is_complete == true` | Todas ✅ |

### Llenar los "Datos recopilados"

Cuando `is_complete == true`, el campo `config` contiene los datos finales. Mientras tanto, el panel puede mostrar los campos como "pendiente" o intentar extraer datos parciales del `config` (que será `null` hasta el final).

**Opción simple (recomendada):** No mostrar datos parciales. Solo mostrar los campos con valores cuando `is_complete == true` y `config` tiene datos.

**Cuando config está disponible:**

```json
// config.identity
{
  "company": "Gafas Virtuals ORG",
  "description": "Venta de gafas de realidad aumentada",
  "specialties": ["Venta", "Alquiler", "Soporte técnico"],
  "tone": "cercano y profesional"
}
```

Mapear a:

| Campo | Valor del config |
|-------|-----------------|
| Nombre del negocio | `config.identity.company` |
| Descripción | `config.identity.description` |
| Servicios principales | `config.identity.specialties` (join con ", ") |
| Tono de comunicación | `config.identity.tone` |

---

## Panel izquierdo: Integraciones (Iris y Atlas CRM)

Debajo de las etapas, mostrar una sección de integraciones. Estas se configuran **independientemente** del chat, a través de endpoints separados.

### Endpoint de integraciones

```
Base: /api/hub/projects/{project_id}/integrations/
```

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/integrations/` | Listar integraciones del proyecto |
| `POST` | `/integrations/` | Crear nueva integración |
| `GET` | `/integrations/{id}/` | Detalle de una integración |
| `PATCH` | `/integrations/{id}/` | Actualizar integración |
| `DELETE` | `/integrations/{id}/` | Eliminar integración |

### Tipos de integración disponibles

| `service_type` | Nombre para mostrar | Descripción para el usuario |
|----------------|---------------------|----------------------------|
| `iris` | Iris — Base de conocimiento | Conecta una base de datos con información de tu negocio para que el bot responda con datos reales |
| `atlas_crm` | Atlas CRM | Conecta tu sistema de gestión de clientes para guardar automáticamente los datos que capture el bot |
| `custom` | Webhook personalizado | Conecta cualquier servicio externo mediante una URL |

---

### Configurar Iris (Base de conocimiento)

Iris permite que el bot consulte información real del negocio (catálogo, preguntas frecuentes, etc.) para dar respuestas precisas.

**Crear integración Iris:**

```http
POST /api/hub/projects/{project_id}/integrations/
Authorization: Bearer eyJ...
Content-Type: application/json
```

```json
{
  "service_type": "iris",
  "label": "Base de conocimiento principal",
  "api_url": "https://iris.ejemplo.com/api/search",
  "api_key": "iris-secret-key-123",
  "api_key_header": "X-API-Key",
  "config": {},
  "is_active": true
}
```

**Response 201:**

```json
{
  "id": "uuid",
  "service_type": "iris",
  "service_type_display": "Iris (Knowledge Base)",
  "label": "Base de conocimiento principal",
  "api_url": "https://iris.ejemplo.com/api/search",
  "api_key_header": "X-API-Key",
  "config": {},
  "is_active": true,
  "created_at": "2026-03-18T10:00:00Z"
}
```

> `api_key` es **write-only**: nunca se devuelve en las respuestas.

**Formulario sugerido para el usuario:**

| Campo del formulario | Campo API | Requerido | Ayuda para el usuario |
|---------------------|-----------|-----------|----------------------|
| URL del servicio | `api_url` | Sí | La dirección donde está tu base de conocimiento Iris |
| Clave de acceso | `api_key` | Sí | La clave secreta para conectar con Iris |
| Nombre del header | `api_key_header` | No (default: `X-API-Key`) | Normalmente no necesitas cambiarlo |
| Nombre | `label` | No | Un nombre para identificar esta conexión |
| Activa | `is_active` | No (default: `true`) | Activar o desactivar la conexión |

---

### Configurar Atlas CRM

Atlas CRM permite que el bot guarde automáticamente los datos de contacto que capture (nombre, email, etc.) en el sistema de gestión de clientes.

**Crear integración Atlas CRM:**

```http
POST /api/hub/projects/{project_id}/integrations/
Authorization: Bearer eyJ...
Content-Type: application/json
```

```json
{
  "service_type": "atlas_crm",
  "label": "CRM principal",
  "api_url": "https://atlas.ejemplo.com/api/contacts",
  "api_key": "atlas-secret-key-456",
  "api_key_header": "Authorization",
  "config": {},
  "is_active": true
}
```

**Response 201:**

```json
{
  "id": "uuid",
  "service_type": "atlas_crm",
  "service_type_display": "Atlas CRM",
  "label": "CRM principal",
  "api_url": "https://atlas.ejemplo.com/api/contacts",
  "api_key_header": "Authorization",
  "config": {},
  "is_active": true,
  "created_at": "2026-03-18T10:00:00Z"
}
```

**Formulario sugerido para el usuario:**

| Campo del formulario | Campo API | Requerido | Ayuda para el usuario |
|---------------------|-----------|-----------|----------------------|
| URL del servicio | `api_url` | Sí | La dirección de tu Atlas CRM |
| Clave de acceso | `api_key` | Sí | La clave secreta para conectar con Atlas |
| Nombre del header | `api_key_header` | No (default: `X-API-Key`) | Usa `Authorization` si Atlas lo requiere |
| Nombre | `label` | No | Un nombre para identificar esta conexión |
| Activa | `is_active` | No (default: `true`) | Activar o desactivar la conexión |

---

### Actualizar una integración (cambiar URL o clave)

```http
PATCH /api/hub/projects/{project_id}/integrations/{integration_id}/
Authorization: Bearer eyJ...
Content-Type: application/json
```

```json
{
  "api_url": "https://nueva-url.ejemplo.com/api",
  "api_key": "nueva-clave-secreta"
}
```

> Si no se envía `api_key`, la clave existente se mantiene sin cambios. Solo enviar este campo cuando el usuario quiera cambiarla.

### Eliminar una integración

```http
DELETE /api/hub/projects/{project_id}/integrations/{integration_id}/
Authorization: Bearer eyJ...
```

```json
// Response 204 No Content
```

### Listar integraciones del proyecto

```http
GET /api/hub/projects/{project_id}/integrations/
Authorization: Bearer eyJ...
```

```json
{
  "count": 2,
  "results": [
    {
      "id": "uuid-1",
      "service_type": "iris",
      "service_type_display": "Iris (Knowledge Base)",
      "label": "Base de conocimiento",
      "api_url": "https://iris.ejemplo.com/api/search",
      "api_key_header": "X-API-Key",
      "config": {},
      "is_active": true,
      "created_at": "2026-03-18T10:00:00Z"
    },
    {
      "id": "uuid-2",
      "service_type": "atlas_crm",
      "service_type_display": "Atlas CRM",
      "label": "CRM principal",
      "api_url": "https://atlas.ejemplo.com/api/contacts",
      "api_key_header": "Authorization",
      "config": {},
      "is_active": true,
      "created_at": "2026-03-18T10:00:00Z"
    }
  ]
}
```

---

### Estado de las integraciones en el panel

Usar el GET de integraciones para determinar qué mostrar:

| Condición | Estado visual |
|-----------|--------------|
| No existe integración de ese tipo | Botón "Configurar" (gris) |
| Existe y `is_active == true` | ✅ Conectada (verde) + botón "Editar" |
| Existe y `is_active == false` | ⚠️ Desactivada (amarillo) + botón "Editar" |

**Restricción:** Solo puede existir **una integración activa por tipo** por proyecto. El backend lo valida y devuelve error 400 si se intenta crear una segunda del mismo tipo.

---

## Endpoints del Setup Chat

### 1. Iniciar o retomar conversación

```
GET /api/hub/projects/{project_id}/setup/chat/
```

**Response 200:**

```json
{
  "message": "¡Hola! Soy tu asistente de configuración...",
  "messages": [
    { "role": "assistant", "content": "¡Hola! Soy tu asistente de configuración..." }
  ],
  "current_section": "identity",
  "is_complete": false,
  "config": null
}
```

---

### 2. Enviar mensaje del usuario

```
POST /api/hub/projects/{project_id}/setup/chat/
Content-Type: application/json
```

**Request:**

```json
{
  "message": "Somos un despacho de abogados especializado en inmigración"
}
```

**Validación:** `message` es obligatorio, máximo 2000 caracteres.

**Response 200 (conversación en curso):**

```json
{
  "message": "¡Genial! Un despacho de inmigración, qué interesante...",
  "messages": [
    { "role": "assistant", "content": "¡Hola! Soy tu asistente..." },
    { "role": "user", "content": "Somos un despacho de abogados especializado en inmigración" },
    { "role": "assistant", "content": "¡Genial! Un despacho de inmigración, qué interesante..." }
  ],
  "current_section": "identity",
  "is_complete": false,
  "config": null
}
```

**Response 200 (avanzó de sección):**

```json
{
  "message": "¡Perfecto! Ya tengo claro tu negocio. Ahora cuéntame...",
  "messages": [ /* historial completo */ ],
  "current_section": "behavior",
  "is_complete": false,
  "config": null
}
```

> Cuando `current_section` cambia, el frontend debe actualizar el indicador activo del panel izquierdo.

**Response 200 (configuración finalizada):**

```json
{
  "message": "¡Tu bot está listo! 🎉 Ya puedes activar tu proyecto.",
  "messages": [ /* historial completo */ ],
  "current_section": "review",
  "is_complete": true,
  "config": {
    "identity": {
      "company": "Despacho Legal Inmigración",
      "description": "Despacho de abogados especializado en inmigración",
      "specialties": ["Visados", "Permisos de trabajo", "Nacionalidad"],
      "channel": "WhatsApp",
      "tone": "profesional, cercano y empático"
    }
  }
}
```

---

### 3. Reiniciar conversación

```
DELETE /api/hub/projects/{project_id}/setup/chat/
```

Borra todo y comienza de cero. Devuelve el nuevo saludo inicial con `current_section: "identity"`.

---

## Campos de respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `message` | `string` | Último mensaje del asistente |
| `messages` | `array` | Historial completo `[{ role, content }]` |
| `current_section` | `string` | Etapa actual: `"identity"`, `"behavior"` o `"review"` |
| `is_complete` | `boolean` | `true` cuando terminó la configuración |
| `config` | `object \| null` | La configuración generada (solo cuando `is_complete == true`) |

---

## Flujo completo paso a paso

```
1. ABRIR PANTALLA
   │
   ├──▶ GET /setup/chat/
   │    ├── Pintar panel izquierdo con etapas (marcar current_section)
   │    ├── messages vacío → mostrar solo el saludo
   │    └── messages con datos → reconstruir todo el chat
   │
   ├──▶ GET /integrations/
   │    └── Pintar estado de Iris y Atlas CRM en el panel
   │
2. USUARIO ESCRIBE MENSAJE
   │
   ├──▶ Mostrar burbuja del usuario inmediatamente (optimistic UI)
   ├──▶ Mostrar indicador "escribiendo..." del asistente
   ├──▶ POST /setup/chat/  { "message": "..." }
   │
   ├── Comprobar si current_section cambió
   │   └── Sí → Actualizar indicador del panel (mover el punto activo)
   │
   ├── is_complete == false
   │   └── Agregar burbuja del asistente al chat
   │
   └── is_complete == true
       └── Agregar burbuja del asistente
            Llenar "Datos recopilados" del panel con config
            Ocultar input de texto
            Mostrar botón "Activar proyecto"
   │
3. CONFIGURAR INTEGRACIONES (en cualquier momento)
   │
   ├── Usuario pulsa "Configurar" en Iris
   │   └── Abrir modal/formulario
   │       └── POST /integrations/  { service_type: "iris", ... }
   │
   └── Usuario pulsa "Configurar" en Atlas CRM
       └── Abrir modal/formulario
           └── POST /integrations/  { service_type: "atlas_crm", ... }
   │
4. BOTÓN "ACTIVAR PROYECTO"
   │
   └── Navegar a la pantalla del proyecto
       El chatbot_config ya se guardó automáticamente en el backend
```

---

## Estados de la pantalla

| Estado | Condición | Panel izquierdo | Chat |
|--------|-----------|----------------|------|
| **Cargando** | GET inicial | Skeleton | Spinner |
| **Identidad** | `current_section == "identity"` | ● Identidad activa | Chat activo |
| **Comportamiento** | `current_section == "behavior"` | ✅ Identidad, ● Comportamiento activa | Chat activo |
| **Revisión** | `current_section == "review"` | ✅✅ anteriores, ● Revisión activa | Chat activo |
| **Completado** | `is_complete == true` | Todas ✅ + datos del config | Input oculto + botón acción |
| **Escribiendo** | Esperando POST | Sin cambio | Indicador typing |
| **Error** | POST falla | Sin cambio | Snackbar + reintentar |

---

## Consejos de implementación

### Burbujas del chat

| `role` | Alineación | Color sugerido |
|--------|------------|----------------|
| `assistant` | Izquierda | Gris claro / color neutro |
| `user` | Derecha | Color primario de la app |

### Transición de sección

Cuando `current_section` cambia en la respuesta, animar la transición del indicador en el panel izquierdo (mover punto activo al siguiente paso, marcar el anterior como completado).

### Modal de integración

Al abrir el formulario de Iris o Atlas CRM, prerrellenar con datos existentes si ya hay una integración creada. Usar `PATCH` para actualizar en vez de `POST`.

### Campo api_key en edición

Mostrar un placeholder tipo `••••••••••` cuando ya existe una integración. Solo enviar `api_key` en el PATCH si el usuario escribe una nueva clave. Si deja el campo vacío, no enviarlo.

### Scroll automático + Reconstrucción

Igual que antes: scroll al final del chat en cada nuevo mensaje. Al volver a la pantalla, `GET /setup/chat/` + `GET /integrations/` para reconstruir todo.

---

## Ejemplo completo de interacción

### 1. Abrir pantalla (carga inicial — dos llamadas en paralelo)

```http
GET /api/hub/projects/{id}/setup/chat/
GET /api/hub/projects/{id}/integrations/
```

**Setup chat:**
```json
{
  "message": "¡Hola! 👋 Soy el asistente de configuración...",
  "messages": [
    { "role": "assistant", "content": "¡Hola! 👋 Soy el asistente..." }
  ],
  "current_section": "identity",
  "is_complete": false,
  "config": null
}
```

**Integraciones:**
```json
{ "count": 0, "results": [] }
```

→ Panel: ● Identidad (activa), ○ Comportamiento, ○ Revisión  
→ Integraciones: Iris [Configurar], Atlas CRM [Configurar]

### 2. Tras varias respuestas, avanza a comportamiento

```json
{
  "message": "¡Perfecto! Ya conozco tu negocio. Ahora cuéntame, ¿qué tipo de preguntas suelen hacerte tus clientes?",
  "messages": [ /* 5 mensajes */ ],
  "current_section": "behavior",
  "is_complete": false,
  "config": null
}
```

→ Panel: ✅ Identidad, ● Comportamiento (activa), ○ Revisión

### 3. Usuario configura Iris mientras chatea

```http
POST /api/hub/projects/{id}/integrations/
{
  "service_type": "iris",
  "label": "KB Gafas Virtuals",
  "api_url": "https://iris.gafasvirtuals.com/api/search",
  "api_key": "sk-iris-xxx"
}
```

→ Panel: Iris ✅ Conectada [Editar]

### 4. Confirmación final

```json
{
  "message": "¡Tu bot está listo! 🎉 Ya puedes activar tu proyecto.",
  "messages": [ /* historial completo */ ],
  "current_section": "review",
  "is_complete": true,
  "config": {
    "identity": {
      "company": "Gafas Virtuals ORG",
      "description": "Venta y alquiler de gafas de realidad aumentada",
      "specialties": ["Venta de gafas", "Alquiler para eventos", "Soporte técnico"],
      "channel": "WhatsApp",
      "tone": "cercano y profesional"
    }
  }
}
```

→ Panel: ✅ Identidad, ✅ Comportamiento, ✅ Revisión  
→ Datos: Negocio: Gafas Virtuals ORG, Servicios: Venta, Alquiler, Soporte  
→ Chat: Input oculto, botón "Activar proyecto" visible
