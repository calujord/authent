# Flujo de Onboarding Completo - Documentación Frontend

> **Base URL:** `http://localhost:8020/api`  
> **Auth:** Bearer token en header `Authorization`

---

## Visión General

El onboarding de un proyecto en Atharix Hub sigue este flujo:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  1. Crear   │────▶│ 2. Plugins  │────▶│ 3. Setup    │────▶│ 4. Bot      │
│  Proyecto   │     │  (config)   │     │    Chat     │     │   LIVE 🟢   │
│  (DRAFT)    │     │ WA/AI/Iris/ │     │  (AI chat)  │     │             │
│             │     │   Atlas     │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Paso 1: Crear Proyecto

```
POST /hub/projects/
```

**Request:**
```json
{
  "name": "Mi Negocio"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid-del-proyecto",
  "name": "Mi Negocio",
  "status": "draft",
  "has_whatsapp_credentials": false,
  "has_chatbot_config": false,
  "webhook_url": "/api/hub/webhook/abc123/",
  "integrations": [],
  "conversation_count": 0
}
```

**Estado del proyecto:** `DRAFT`

---

## Paso 2: Configurar Plugins

Los plugins son los servicios que tu bot necesita para funcionar. Se configuran **antes** del Setup Chat para que el flow auto-generado los incluya.

### Tipos de Plugin

| `plugin_type` | Nombre | Qué necesita | Para qué |
|---------------|--------|-------------|----------|
| `whatsapp` | WhatsApp | `token` (Access Token) | Canal de comunicación |
| `openai` | OpenAI | `token` (API Key) | Inteligencia artificial del bot |
| `iris` | Iris | `token` + `config.collections` | Base de conocimiento |
| `atlas` | Atlas CRM | `token` (API Key) | Captura automática de contactos |

### 2.1 Login en Iris / Atlas (obtener token)

Antes de crear un plugin de Iris o Atlas, el usuario necesita autenticarse para obtener su API key.

**Login Atlas:**
```
POST /hub/plugins/login/atlas/
```

**Request:**
```json
{
  "email": "usuario@empresa.com",
  "password": "secreto"
}
```

**Response:** `200 OK`
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "usuario@empresa.com",
    "name": "Carlos"
  }
}
```

**Login Iris:**
```
POST /hub/plugins/login/iris/
```

**Request:**
```json
{
  "email": "usuario@empresa.com",
  "password": "secreto"
}
```

**Response:** `200 OK`
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "usuario@empresa.com"
  },
  "collections": [
    {"id": "uuid-1", "name": "Productos", "document_count": 45},
    {"id": "uuid-2", "name": "FAQ", "document_count": 120},
    {"id": "uuid-3", "name": "Políticas", "document_count": 15}
  ]
}
```

**Errores de login:**

| Código | Significado |
|--------|-------------|
| 401 | Credenciales inválidas |
| 502 | No se pudo conectar con el servicio externo |

### 2.2 Listar plugins del proyecto

```
GET /hub/projects/{project_id}/plugins/
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid-1",
    "plugin_type": "whatsapp",
    "plugin_type_display": "WhatsApp",
    "config": {},
    "is_active": true,
    "has_token": true,
    "created_at": "2026-03-18T..."
  },
  {
    "id": "uuid-2",
    "plugin_type": "iris",
    "plugin_type_display": "Iris (Knowledge Base)",
    "config": {
      "collections": ["uuid-1", "uuid-2"]
    },
    "is_active": true,
    "has_token": true,
    "created_at": "2026-03-18T..."
  }
]
```

### 2.3 Crear plugin

```
POST /hub/projects/{project_id}/plugins/
```

**WhatsApp:**
```json
{
  "plugin_type": "whatsapp",
  "token": "EAAGm0PX4ZC..."
}
```

**OpenAI:**
```json
{
  "plugin_type": "openai",
  "token": "sk-proj-abc123..."
}
```

**Atlas CRM** (usar token obtenido del login):
```json
{
  "plugin_type": "atlas",
  "token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Iris** (usar token + seleccionar colecciones del login):
```json
{
  "plugin_type": "iris",
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "config": {
    "collections": ["uuid-1", "uuid-2"]
  }
}
```

**Response:** `201 Created`

> **Nota:** Solo puede haber **un plugin por tipo** por proyecto.

### 2.4 Actualizar plugin

```
PATCH /hub/projects/{project_id}/plugins/{plugin_id}/
```

```json
{
  "config": {
    "collections": ["uuid-1", "uuid-3"]
  }
}
```

### 2.5 Eliminar plugin

```
DELETE /hub/projects/{project_id}/plugins/{plugin_id}/
```

### UI sugerida para plugins

```
┌──────────────────────────────────────────────────────────┐
│  Plugins de tu proyecto                                  │
│                                                          │
│  ┌────────────────────┐  ┌────────────────────┐          │
│  │  💬 WhatsApp       │  │  🤖 OpenAI         │          │
│  │                    │  │                    │          │
│  │  Token de acceso   │  │  API Key           │          │
│  │  [••••••••••••] ✅ │  │  [••••••••••••] ✅ │          │
│  └────────────────────┘  └────────────────────┘          │
│                                                          │
│  ┌────────────────────┐  ┌────────────────────┐          │
│  │  📚 Iris           │  │  👤 Atlas CRM      │          │
│  │                    │  │                    │          │
│  │  [Iniciar sesión]  │  │  [Iniciar sesión]  │          │
│  │                    │  │                    │          │
│  │  Al login:         │  │  Al login:         │          │
│  │  ☑ Productos (45)  │  │  Token obtenido ✅ │          │
│  │  ☑ FAQ (120)       │  │  [Guardar]         │          │
│  │  ☐ Políticas (15)  │  │                    │          │
│  │  [Guardar]         │  │                    │          │
│  └────────────────────┘  └────────────────────┘          │
│                                                          │
│              [Continuar al Setup Chat →]                 │
└──────────────────────────────────────────────────────────┘
```

**Flujo de UI para Iris:**
1. Usuario hace clic en "Iniciar sesión"
2. Modal con email/password → `POST /hub/plugins/login/iris/`
3. Respuesta trae `token` + `collections`
4. Mostrar lista de colecciones con checkboxes
5. Al guardar → `POST /hub/projects/{id}/plugins/` con token + collections seleccionadas

**Flujo de UI para Atlas:**
1. Usuario hace clic en "Iniciar sesión"
2. Modal con email/password → `POST /hub/plugins/login/atlas/`
3. Respuesta trae `token`
4. Auto-guardar → `POST /hub/projects/{id}/plugins/` con token

**Flujo de UI para WhatsApp / OpenAI:**
1. Campo de texto para pegar el token
2. Al guardar → `POST /hub/projects/{id}/plugins/` con token

---

## Paso 3: Setup Chat (Configuración con IA)

El setup chat es una conversación guiada con IA que recorre **3 secciones** en orden:

| # | Sección | `current_section` | Qué hace |
|---|---------|-------------------|----------|
| 1 | Identidad | `identity` | Nombre, descripción, especialidades, tono |
| 2 | Comportamiento | `behavior` | Cómo debe responder el bot (el AI propone, usuario ajusta) |
| 3 | Revisión | `review` | Resumen → confirmación → genera config + flow automático |

### 3.1 Iniciar/Reanudar chat

```
GET /hub/projects/{project_id}/setup/chat/
```

**Response:** `200 OK`
```json
{
  "message": "¡Hola! Soy el asistente de configuración...",
  "messages": [
    {"role": "assistant", "content": "¡Hola! Soy el asistente..."}
  ],
  "current_section": "identity",
  "is_complete": false,
  "config": null
}
```

### 3.2 Enviar mensaje

```
POST /hub/projects/{project_id}/setup/chat/
```

**Request:**
```json
{
  "message": "Somos Análisis Semanal, hacemos análisis económicos"
}
```

**Response:** `200 OK`
```json
{
  "message": "¡Perfecto! Análisis Semanal suena genial...",
  "messages": [
    {"role": "assistant", "content": "¡Hola! Soy el asistente..."},
    {"role": "user", "content": "Somos Análisis Semanal..."},
    {"role": "assistant", "content": "¡Perfecto! Análisis Semanal..."}
  ],
  "current_section": "identity",
  "is_complete": false,
  "config": null
}
```

### 3.3 Transiciones de sección

Cuando el AI tiene toda la info de una sección, avanza automáticamente. El campo `current_section` cambia en la respuesta:

```
identity → behavior → review
```

**Ejemplo de transición identity → behavior:**
- La respuesta incluye resumen de lo recopilado
- Hace una **pregunta concreta** para la siguiente sección
- `current_section` cambia a `"behavior"`

**Ejemplo de transición behavior → review:**
- Confirma el comportamiento
- Dice que va a preparar un resumen
- `current_section` cambia a `"review"`

### 3.4 Setup completo

Cuando el usuario confirma en la revisión:

```json
{
  "message": "¡Tu bot está listo! 🎉 Ya puedes activar tu proyecto...",
  "messages": [...],
  "current_section": "review",
  "is_complete": true,
  "config": {
    "identity": {
      "company": "Análisis Semanal",
      "description": "...",
      "specialties": ["..."],
      "tone": "profesional"
    },
    "model": {"name": "gpt-4o", "temperature": 0.7},
    "format_rules": [...],
    "capture_tags": {...},
    "phases": {...}
  }
}
```

**Qué pasa automáticamente en el backend al completar:**
1. `project.chatbot_config` se guarda con la config generada
2. `project.status` cambia a `"configuring"`
3. **Se crea un Flow automático** con los nodos básicos:
   - `WhatsApp (entrada)` → `OpenAI Assistant` → `WhatsApp (salida)`
   - Si hay integración Iris activa, se añade nodo `Iris Knowledge`
   - Si hay integración Atlas CRM activa, se añade nodo `Atlas CRM`
4. `project.active_flow` se asigna al flow generado
5. `project.use_hub_engine` se activa

### 3.5 Reiniciar setup

```
DELETE /hub/projects/{project_id}/setup/chat/
```

Borra todo y empieza desde cero (identity). También limpia `chatbot_config` y el flow activo.

**Response:** `200 OK` (mismo formato que GET, con el nuevo primer mensaje)

---

## Paso 4: Monitoreo

### 4.1 Ver conversaciones

```
GET /hub/projects/{project_id}/conversations/
```

### 4.2 Ver detalle de conversación

```
GET /hub/projects/{project_id}/conversations/{conversation_id}/
```

### 4.3 Analytics

```
GET /hub/projects/{project_id}/analytics/
GET /hub/projects/{project_id}/analytics/timeseries/
```

---

## Flujo Visual (Flow)

El flow se genera automáticamente al completar el setup. Se puede ver y editar en el editor visual.

### Ver flow activo del proyecto

```
GET /hub/projects/{project_id}/flows/
```

**Response:**
```json
[
  {
    "id": "uuid-del-flow",
    "name": "Análisis Semanal",
    "description": "Flujo generado automáticamente para Análisis Semanal",
    "is_active": true,
    "is_draft": false,
    "nodes": [
      {
        "node_id": "whatsapp_in",
        "node_type": "channel_whatsapp_in",
        "label": "WhatsApp",
        "position_x": 0,
        "position_y": 200,
        "connections": {"default": "openai_assistant"}
      },
      {
        "node_id": "openai_assistant",
        "node_type": "openai_assistant",
        "label": "Análisis Semanal",
        "position_x": 350,
        "position_y": 200,
        "connections": {"default": "whatsapp_out"}
      },
      {
        "node_id": "whatsapp_out",
        "node_type": "channel_whatsapp_out",
        "label": "Respuesta",
        "position_x": 700,
        "position_y": 200,
        "connections": {}
      }
    ]
  }
]
```

**Con Iris + Atlas CRM activos:**
```
WhatsApp In → Iris Search → OpenAI Assistant → Atlas CRM → WhatsApp Out
(0, 200)      (350, 200)    (700, 200)        (1050, 200)  (1400, 200)
```

### Tipos de nodo disponibles

| `node_type` | Icono sugerido | Descripción |
|-------------|----------------|-------------|
| `channel_whatsapp_in` | 💬 | Entrada de WhatsApp |
| `channel_whatsapp_out` | 💬 | Salida de WhatsApp |
| `openai_assistant` | 🤖 | Asistente OpenAI |
| `openai_completion` | 🧠 | Completado OpenAI |
| `iris_search` | 📚 | Búsqueda en base de conocimiento |
| `atlas_crm_capture` | 👤 | Captura de contactos CRM |
| `hub_enrich` | ✨ | Enriquecimiento de contexto |
| `hub_memory` | 💾 | Memoria de conversación |
| `condition` | ❓ | Condición |
| `http_request` | 🌐 | Request HTTP |
| `delay` | ⏱️ | Delay |

---

## UI Sugerida para el Onboarding

### Pantalla principal del Setup Chat

```
┌──────────────────────────────────────────────────────┐
│  ← Volver                        Análisis Semanal    │
├────────────────┬─────────────────────────────────────┤
│                │                                     │
│  PROGRESO      │        CHAT CON IA                  │
│                │                                     │
│  ● Identidad   │   🤖 ¡Hola! Soy el asistente...    │
│    del negocio │                                     │
│                │   👤 Somos Análisis Semanal...       │
│  ○ Comporta-   │                                     │
│    miento      │   🤖 ¡Perfecto! Ahora definamos     │
│                │      cómo se comportará el bot...    │
│  ○ Revisión    │                                     │
│    final       │                                     │
│                │   ┌─────────────────────────────┐   │
│                │   │ Escribe tu mensaje...    ➤  │   │
│                │   └─────────────────────────────┘   │
├────────────────┴─────────────────────────────────────┤
│  [Reiniciar configuración]                           │
└──────────────────────────────────────────────────────┘
```

### Estados del panel de progreso

Usar `current_section` para determinar cuál sección está activa:

| `current_section` | Identidad | Comportamiento | Revisión |
|-------------------|-----------|----------------|----------|
| `identity`        | 🔵 activo | ⚪ pendiente    | ⚪ pendiente |
| `behavior`        | ✅ hecho  | 🔵 activo      | ⚪ pendiente |
| `review`          | ✅ hecho  | ✅ hecho       | 🔵 activo |

Cuando `is_complete = true`: las 3 secciones muestran ✅

### Después del setup (is_complete = true)

Mostrar pantalla de siguiente paso:

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│        ✅ ¡Tu bot está configurado!                  │
│                                                      │
│   Tu bot "Análisis Semanal" está listo.              │
│                                                      │
│   Plugins activos:                                   │
│   ┌──────────────────────────────────────────────┐   │
│   │ 💬 WhatsApp ........................... ✅   │   │
│   │ 🤖 OpenAI ............................. ✅   │   │
│   │ 📚 Iris (2 colecciones) ............... ✅   │   │
│   │ 👤 Atlas CRM .......................... ✅   │   │
│   └──────────────────────────────────────────────┘   │
│                                                      │
│   ┌──────────────────────────────────────────────┐   │
│   │ 🔄 Ver flujo generado                        │   │
│   │    Visualiza y edita el flujo de tu bot       │   │
│   │                                     [Ver flow]│  │
│   └──────────────────────────────────────────────┘   │
│                                                      │
│              [🚀 Activar proyecto]                   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## Flujo Completo en Código (Ejemplo Flutter/Dart)

```dart
// 1. Crear proyecto
final project = await api.post('/hub/projects/', {'name': 'Mi Bot'});
final projectId = project['id'];

// 2. Configurar plugins

// 2a. WhatsApp (pegar token directo)
await api.post('/hub/projects/$projectId/plugins/', {
  'plugin_type': 'whatsapp',
  'token': whatsappToken,
});

// 2b. OpenAI (pegar token directo)
await api.post('/hub/projects/$projectId/plugins/', {
  'plugin_type': 'openai',
  'token': openaiApiKey,
});

// 2c. Atlas (login primero → obtener token)
final atlasLogin = await api.post('/hub/plugins/login/atlas/', {
  'email': atlasEmail,
  'password': atlasPassword,
});
await api.post('/hub/projects/$projectId/plugins/', {
  'plugin_type': 'atlas',
  'token': atlasLogin['token'],
});

// 2d. Iris (login → obtener token + collections → seleccionar)
final irisLogin = await api.post('/hub/plugins/login/iris/', {
  'email': irisEmail,
  'password': irisPassword,
});
// Mostrar irisLogin['collections'] al usuario para que seleccione
final selectedCollections = ['uuid-1', 'uuid-2']; // user picks
await api.post('/hub/projects/$projectId/plugins/', {
  'plugin_type': 'iris',
  'token': irisLogin['token'],
  'config': {'collections': selectedCollections},
});

// 3. Setup chat (AI configura el bot)
final setup = await api.get('/hub/projects/$projectId/setup/chat/');

bool isComplete = false;
while (!isComplete) {
  final response = await api.post(
    '/hub/projects/$projectId/setup/chat/',
    {'message': userInput},
  );
  
  // response['message']         → mensaje del AI
  // response['current_section'] → sección activa
  // response['is_complete']     → ¿terminó?
  // response['config']          → config generada
  
  isComplete = response['is_complete'];
}
// Al completar: flow auto-generado + proyecto en "configuring"

// 4. Activar proyecto
await api.patch('/hub/projects/$projectId/', {
  'status': 'active',
});
```

---

## Manejo de errores

| Código | Significado | Qué hacer |
|--------|-------------|-----------|
| 400 | Datos inválidos | Mostrar `message` al usuario |
| 401 | Token expirado | Refresh token o re-login |
| 404 | Proyecto no encontrado | Verificar project_id en la URL |
| 409 | Integración duplicada | Ya existe una de ese tipo |
| 500 | Error del servidor | Reintentar o mostrar error genérico |

---

## Resumen de Estados del Proyecto

| Estado | `status` | Significado |
|--------|----------|-------------|
| Borrador | `draft` | Recién creado, sin configurar |
| Configurando | `configuring` | Setup completado, config generada |
| Activo | `active` | Bot recibiendo mensajes |
| Pausado | `paused` | Bot detenido temporalmente |

---

## Sistema de Billing / Tarifas

El sistema de billing permite asignar planes (tarifas) a proyectos, controlar el consumo de mensajes y tokens, y calcular costos de excedente.

### Listar Planes Disponibles

```
GET /hub/plans/
```

**Response:** `200 OK`
```json
{
  "count": 3,
  "results": [
    {
      "id": "uuid-plan",
      "name": "Basico",
      "description": "Plan basico con 1000 mensajes",
      "price_monthly": "29.99",
      "message_limit": 1000,
      "ai_token_limit": 500000,
      "overage_cost_per_message": "0.0500",
      "overage_cost_per_1k_tokens": "0.0100",
      "is_active": true,
      "sort_order": 1
    }
  ]
}
```

### Asignar Plan a Proyecto

```
POST /hub/projects/{project_id}/billing/
```

**Request:**
```json
{
  "plan_id": "uuid-del-plan"
}
```

**Response:** `201 Created` (primera vez) o `200 OK` (cambio de plan)
```json
{
  "id": "uuid-project-plan",
  "plan": "uuid-del-plan",
  "plan_detail": {
    "id": "uuid-del-plan",
    "name": "Basico",
    "price_monthly": "29.99",
    "message_limit": 1000,
    "ai_token_limit": 500000
  },
  "billing_cycle_start": "2026-03-18",
  "billing_cycle_end": "2026-04-17",
  "days_remaining": 30,
  "is_active": true,
  "created_at": "2026-03-18T21:00:00Z"
}
```

### Consultar Billing del Proyecto

```
GET /hub/projects/{project_id}/billing/
```

**Response (con plan):** `200 OK`
```json
{
  "has_plan": true,
  "plan": {
    "id": "uuid-plan",
    "name": "Basico",
    "price_monthly": 29.99,
    "message_limit": 1000,
    "ai_token_limit": 500000
  },
  "billing_cycle": {
    "start": "2026-03-18",
    "end": "2026-04-17",
    "days_remaining": 25
  },
  "usage": {
    "messages_received": 342,
    "messages_sent": 340,
    "total_messages": 682,
    "ai_tokens_used": 234500
  },
  "limits": {
    "messages_used": 682,
    "messages_limit": 1000,
    "messages_percentage": 68.2,
    "tokens_used": 234500,
    "tokens_limit": 500000,
    "tokens_percentage": 46.9
  },
  "overage": {
    "messages_over": 0,
    "tokens_over": 0,
    "cost_messages": 0.0,
    "cost_tokens": 0.0,
    "total_overage_cost": 0.0
  }
}
```

**Response (sin plan):** `200 OK`
```json
{
  "has_plan": false
}
```

### Historial de Uso Diario

```
GET /hub/projects/{project_id}/billing/usage/?days=30
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "date": "2026-03-18",
    "messages_received": 45,
    "messages_sent": 43,
    "total_messages": 88,
    "ai_tokens_used": 32000
  },
  {
    "id": "uuid",
    "date": "2026-03-17",
    "messages_received": 38,
    "messages_sent": 37,
    "total_messages": 75,
    "ai_tokens_used": 28500
  }
]
```

### Billing en el Proyecto (project detail)

El campo `billing` se incluye automáticamente en `GET /hub/projects/{id}/`:

```json
{
  "id": "uuid-proyecto",
  "name": "Mi Negocio",
  "billing": {
    "has_plan": true,
    "plan": { "name": "Basico", "message_limit": 1000 },
    "usage": { "total_messages": 682, "ai_tokens_used": 234500 },
    "limits": { "messages_percentage": 68.2, "tokens_percentage": 46.9 }
  }
}
```

### Wireframe del Dashboard de Plan

```
┌──────────────────────────────────────────────┐
│  Plan: Basico ($29.99/mes)                   │
│                                              │
│  Mensajes:  682 / 1,000  ████████░░  68.2%   │
│  Tokens IA: 234K / 500K  █████░░░░░  46.9%   │
│                                              │
│  Ciclo: 18 Mar → 17 Abr  (25 días restantes) │
│  Excedente: $0.00                            │
│                                              │
│  [Cambiar Plan]                              │
└──────────────────────────────────────────────┘
```

### Seguimiento de Uso

El uso se registra automáticamente:
- Cada mensaje **recibido** del usuario → `messages_received + 1`
- Cada mensaje **enviado** por el bot → `messages_sent + 1`
- Tokens de IA usados → `ai_tokens_used + N`

Los contadores se acumulan por día en `UsageRecord` y se agregan por ciclo de facturación para el resumen.

---

## Debug de Flows

Permite probar un flow sin necesidad de WhatsApp. Simula el envío de mensajes a través del motor de flujos, capturando la respuesta del bot en lugar de enviarla por WhatsApp.

### Enviar Mensaje de Debug

```
POST /hub/projects/{project_id}/flows/{flow_id}/debug/
```

**Request:**
```json
{
  "message": "Hola, quiero información sobre sus servicios"
}
```

**Response:** `200 OK`
```json
{
  "bot_response": "¡Hola! Soy el asistente de Mi Negocio. ¿En qué puedo ayudarte?",
  "metrics": {
    "wa_message_id": "debug_abc123",
    "phase_before": "no_name",
    "node_wa_in_ms": 12,
    "openai_tokens_prompt": 450,
    "openai_tokens_completion": 85,
    "openai_tokens_total": 535,
    "openai_latency_ms": 1200,
    "openai_model": "gpt-4o",
    "node_openai_ms": 1205,
    "whatsapp_sent": false,
    "debug_mode": true,
    "node_wa_out_ms": 0,
    "total_steps": 3,
    "pipeline_duration_ms": 1220,
    "engine": "debug"
  },
  "conversation_id": "uuid-conversacion-debug"
}
```

**Notas:**
- `whatsapp_sent: false` siempre — el modo debug no envía mensajes reales
- `debug_mode: true` indica que se ejecutó en modo debug
- `metrics` incluye tiempos por nodo, tokens de OpenAI, pasos ejecutados
- La conversación persiste entre mensajes (tiene historial)
- Cada usuario tiene su propia sesión de debug por flow

### Obtener Sesión de Debug

```
GET /hub/projects/{project_id}/flows/{flow_id}/debug/
```

**Response:** `200 OK`
```json
{
  "conversation_id": "uuid-conversacion-debug",
  "messages": [
    {
      "id": "uuid-msg-1",
      "role": "user",
      "content": "Hola, quiero información",
      "created_at": "2026-03-19T10:30:00Z"
    },
    {
      "id": "uuid-msg-2",
      "role": "assistant",
      "content": "¡Hola! Soy el asistente de Mi Negocio...",
      "created_at": "2026-03-19T10:30:01Z"
    }
  ],
  "phase": "no_name",
  "captured_name": null,
  "captured_email": null,
  "interaction_count": 1,
  "is_lead": false
}
```

**Sesión vacía:**
```json
{
  "conversation_id": null,
  "messages": [],
  "phase": null,
  "captured_name": null,
  "captured_email": null
}
```

### Resetear Sesión de Debug

```
DELETE /hub/projects/{project_id}/flows/{flow_id}/debug/
```

**Response:** `200 OK`
```json
{
  "message": "Sesión de debug reseteada"
}
```

**Sin sesión activa:** `404`
```json
{
  "message": "No hay sesión de debug activa"
}
```

### Wireframe del Panel de Debug

```
┌──────────────────────────────────────────────┐
│  🔧 Debug: Flow "Mi Flow Principal"          │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ 👤 Hola, quiero información            │  │
│  │                          10:30 AM      │  │
│  │                                        │  │
│  │ 🤖 ¡Hola! Soy el asistente de...      │  │
│  │                          10:30 AM      │  │
│  │                                        │  │
│  │ 👤 Me llamo Carlos                     │  │
│  │                          10:31 AM      │  │
│  │                                        │  │
│  │ 🤖 ¡Encantado Carlos! ¿Cómo puedo...  │  │
│  │                          10:31 AM      │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  Métricas último mensaje:                    │
│  ⏱ Pipeline: 1220ms | Tokens: 535           │
│  📊 Pasos: 3 | Fase: has_name_no_email      │
│                                              │
│  [Escribir mensaje...]          [Enviar]     │
│                                              │
│  [🗑 Resetear Sesión]                        │
└──────────────────────────────────────────────┘
```

### Errores del Debug

| Código | Causa | Acción |
|--------|-------|--------|
| 400 | Flow sin nodo de entrada | Configurar `entry_node` en el flow |
| 404 | Proyecto o flow no encontrado | Verificar IDs en la URL |
| 401 | Token expirado | Refresh token o re-login |
