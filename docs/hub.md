# Hub — Motor de Bots de WhatsApp

El **Hub** es la aplicación central de Atharix Hub. Gestiona el ciclo de vida completo de un bot de WhatsApp: desde la creación del proyecto, la configuración guiada por IA (Setup Chat), la recepción de mensajes vía webhook, el pipeline de respuesta con OpenAI, hasta la captura de datos y envío a CRM.

---

## Tabla de contenidos

1. [Arquitectura general](#arquitectura-general)
2. [Modelos de datos](#modelos-de-datos)
3. [Ciclo de vida del proyecto](#ciclo-de-vida-del-proyecto)
4. [Setup Chat — Configuración guiada por IA](#setup-chat--configuración-guiada-por-ia)
5. [Pipeline de mensajes (flow.py)](#pipeline-de-mensajes)
6. [Webhooks de WhatsApp](#webhooks-de-whatsapp)
7. [Fases de conversación](#fases-de-conversación)
8. [Integraciones externas](#integraciones-externas)
9. [Referencia de API](#referencia-de-api)
10. [Estructura del chatbot_config](#estructura-del-chatbot_config)

---

## Arquitectura general

```
┌────────────────────────────────────────────────────────────────┐
│                       ATHARIX HUB PLATFORM                    │
│                                                               │
│  ┌─────────┐    ┌─────────────┐    ┌───────────────────────┐  │
│  │ Frontend │───▶│   Hub API   │───▶│     Setup Chat (IA)   │  │
│  │  (SPA)   │    │  /api/hub/  │    │  Entrevista → Config  │  │
│  └─────────┘    └──────┬──────┘    └───────────────────────┘  │
│                        │                                      │
│            ┌───────────┼───────────┐                          │
│            ▼           ▼           ▼                          │
│     ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│     │ Projects │ │ Convos   │ │ Messages │                   │
│     │ (config) │ │ (estado) │ │ (chat)   │                   │
│     └──────────┘ └──────────┘ └──────────┘                   │
│                                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │                WhatsApp Webhook Pipeline                  │ │
│  │                                                           │ │
│  │  Meta ──▶ Webhook ──▶ Celery Task ──▶ flow.py pipeline   │ │
│  │                                           │               │ │
│  │      ┌────────────────────────────────────┤               │ │
│  │      ▼              ▼            ▼        ▼               │ │
│  │   Knowledge      OpenAI      WhatsApp    CRM             │ │
│  │   (Iris)         (GPT-4o)    (Send)     (Atlas)          │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

---

## Modelos de datos

### Project (`hub_project`)

Modelo central. Un proyecto = un bot desplegado para un negocio.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `business` | FK → Business | Negocio al que pertenece |
| `name` | CharField(200) | Nombre del proyecto |
| `description` | TextField | Descripción opcional |
| `status` | CharField | `draft` · `configuring` · `active` · `paused` |
| `wa_phone_number_id` | CharField(100) | Phone Number ID de WhatsApp Cloud API |
| `wa_access_token` | TextField | Token de acceso (write-only en API) |
| `wa_verify_token` | CharField(200) | Token de verificación para webhook |
| `webhook_token` | CharField(64) | Token único auto-generado para la URL del webhook |
| `chatbot_config` | JSONField | Configuración completa del bot (ver [estructura](#estructura-del-chatbot_config)) |
| `openai_api_key` | TextField | API key de OpenAI del negocio (write-only en API) |
| `openai_model` | CharField(50) | Modelo a usar (default: `gpt-4o`) |
| `openai_temperature` | Float | Temperatura (default: `0.7`) |
| `is_active` | Boolean | Si el proyecto acepta webhooks |

**Propiedades calculadas:**
- `webhook_url` → `/api/hub/webhook/{webhook_token}/`
- `has_whatsapp_credentials` → `True` si tiene `wa_phone_number_id` y `wa_access_token`
- `has_chatbot_config` → `True` si `chatbot_config` tiene sección `identity`

### Conversation (`hub_conversation`)

Estado de una conversación por usuario de WhatsApp.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `project` | FK → Project | Proyecto asociado |
| `wa_id` | CharField(50) | Número de WhatsApp del usuario |
| `wa_profile_name` | CharField(200) | Nombre de perfil de WhatsApp |
| `captured_name` | CharField(200) | Nombre capturado por el bot |
| `captured_email` | EmailField | Email capturado por el bot |
| `phase` | CharField | `no_name` · `has_name_no_email` · `complete_profile` |
| `interaction_count` | Integer | Contador de interacciones (se resetea al capturar nombre) |
| `crm_contact_id` | CharField(100) | ID del contacto en CRM externo |
| `is_lead` | Boolean | Si fue convertido a lead |
| `metadata` | JSONField | Datos adicionales |

**Constraint único:** `(project, wa_id)` donde `is_deleted=False`

### Message (`hub_message`)

Mensajes individuales de una conversación.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `conversation` | FK → Conversation | Conversación padre |
| `role` | CharField | `user` · `assistant` · `system` |
| `content` | TextField | Contenido del mensaje |
| `wa_message_id` | CharField(100) | ID del mensaje en WhatsApp |
| `metadata` | JSONField | Metadatos adicionales |

### ProjectIntegration (`hub_project_integration`)

Conexiones a servicios externos por proyecto.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `project` | FK → Project | Proyecto asociado |
| `service_type` | CharField | `iris` · `atlas_crm` · `custom` |
| `label` | CharField(100) | Nombre descriptivo |
| `api_url` | URLField | URL del servicio |
| `api_key` | CharField(500) | API key (write-only en API) |
| `api_key_header` | CharField(100) | Header para el API key (default: `X-API-Key`) |
| `config` | JSONField | Configuración adicional |
| `is_active` | Boolean | Si la integración está activa |

**Constraint único:** `(project, service_type)` donde `is_deleted=False`

### SetupChat (`hub_setup_chat`)

Chat de onboarding guiado por IA. Relación OneToOne con Project.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `project` | OneToOne → Project | Proyecto asociado |
| `messages` | JSONField | Historial de mensajes `[{role, content}]` |
| `current_section` | CharField | `identity` · `behavior` · `review` |
| `collected_data` | JSONField | Datos recopilados (copia del config al finalizar) |
| `is_complete` | Boolean | Si ya se generó la configuración |

---

## Ciclo de vida del proyecto

```
  ┌───────────┐     Setup Chat      ┌──────────────┐      Credenciales     ┌────────┐
  │   DRAFT   │ ──────────────────▶ │ CONFIGURING  │ ────────────────────▶ │ ACTIVE │
  │           │   (chatbot_config   │              │   + verificar webhook │        │
  │ Proyecto  │    generado por IA) │  Config OK   │                       │  Bot   │
  │  creado   │                     │  falta WA    │                       │  LIVE  │
  └───────────┘                     └──────────────┘                       └────┬───┘
                                                                               │
                                                                          ┌────▼───┐
                                                                          │ PAUSED │
                                                                          │ (manual)│
                                                                          └────────┘
```

### 1. Crear proyecto (DRAFT)

```bash
POST /api/hub/projects/
Authorization: Bearer <jwt>

{
  "name": "Mi Bot",
  "description": "Bot de atención para mi negocio"
}
```

El proyecto se crea en estado `draft`. El negocio se asigna automáticamente del usuario autenticado.

### 2. Configurar con Setup Chat (DRAFT → CONFIGURING)

El Setup Chat entrevista al usuario en 3 secciones para generar el `chatbot_config`:

1. **Identity** → nombre, descripción, especialidades, tono
2. **Behavior** → clasificación de mensajes, citas, instrucciones especiales
3. **Review** → resumen + confirmación → genera JSON

Cuando el usuario confirma en la revisión, el `chatbot_config` se guarda automáticamente y el estado cambia a `configuring`.

### 3. Credenciales de WhatsApp (CONFIGURING → ACTIVE)

```bash
PATCH /api/hub/projects/{id}/
Authorization: Bearer <jwt>

{
  "wa_phone_number_id": "123456789",
  "wa_access_token": "EAAxxxxx...",
  "wa_verify_token": "mi-token-secreto",
  "status": "active"
}
```

### 4. Registrar webhook en Meta

Usar la `webhook_url` del proyecto (`/api/hub/webhook/{webhook_token}/`) como URL de webhook en la [configuración de la app de Meta](https://developers.facebook.com/apps/).

Meta enviará un GET de verificación con `hub.verify_token` que el sistema valida automáticamente.

---

## Setup Chat — Configuración guiada por IA

El Setup Chat es una interfaz conversacional donde GPT-4o entrevista al dueño del negocio para generar toda la configuración del bot.

### Flujo de secciones

```
┌──────────┐   {{NEXT_SECTION}}   ┌──────────┐   {{NEXT_SECTION}}   ┌────────┐
│ IDENTITY │ ──────────────────▶ │ BEHAVIOR │ ──────────────────▶  │ REVIEW │
│          │                      │          │                      │        │
│ - Nombre │                      │ - Tipos  │                      │ Resumen│
│ - Desc.  │                      │ - Citas  │                      │ + JSON │
│ - Espec. │                      │ - Rules  │                      │        │
│ - Tono   │                      │          │                      │        │
└──────────┘                      └──────────┘                      └────────┘
                                                                        │
                                                                  {{CONFIG_START}}
                                                                     JSON
                                                                  {{CONFIG_END}}
                                                                        │
                                                                        ▼
                                                              chatbot_config saved
                                                              status → configuring
```

### Tags de control (invisibles para el usuario)

| Tag | Función |
|-----|---------|
| `{{NEXT_SECTION}}` | Avanza a la siguiente sección. La IA lo agrega cuando tiene toda la info de la sección actual |
| `{{CONFIG_START}}` / `{{CONFIG_END}}` | Envuelven el JSON final generado en la sección de revisión |

Estos tags se eliminan de la respuesta visible antes de enviarla al frontend.

### API del Setup Chat

**Iniciar / Obtener chat:**
```bash
GET /api/hub/projects/{project_id}/setup/chat/
Authorization: Bearer <jwt>
```

Respuesta (primera vez — genera saludo automático):
```json
{
  "messages": [
    {
      "role": "assistant",
      "content": "¡Hola! Soy el asistente de configuración de Atharix Hub..."
    }
  ],
  "current_section": "identity",
  "is_complete": false,
  "config": null
}
```

**Enviar mensaje:**
```bash
POST /api/hub/projects/{project_id}/setup/chat/
Authorization: Bearer <jwt>

{
  "message": "Somos una clínica dental especializada en ortodoncia"
}
```

Respuesta:
```json
{
  "message": "¡Genial! Una clínica dental especializada en ortodoncia...",
  "is_complete": false,
  "config": null
}
```

Cuando se completa (usuario confirma en revisión):
```json
{
  "message": "He generado la configuración de tu bot. Ya puedes revisarla y activar tu proyecto.",
  "is_complete": true,
  "config": { "identity": {...}, "phases": {...}, ... }
}
```

**Reiniciar chat:**
```bash
DELETE /api/hub/projects/{project_id}/setup/chat/
Authorization: Bearer <jwt>
```

Elimina el chat anterior y genera uno nuevo con saludo fresco.

---

## Pipeline de mensajes

Cuando llega un mensaje de WhatsApp, se ejecuta el pipeline de 10 pasos en `flow.py`:

```
WhatsApp Message (webhook POST)
        │
        ▼
  1. extract_message()     ← Parse del payload de Meta
        │
        ▼
  2. get_or_create_conversation()  ← Busca/crea conversación por wa_id
        │
        ▼
  3. search_knowledge()    ← Busca en Iris (si integración activa)
        │
        ▼
  4. build_system_prompt() ← Construye prompt según:
        │                     - chatbot_config (identity, format_rules, phases...)
        │                     - Fase actual de la conversación
        │                     - Resultados de knowledge base
        │                     - interaction_count (estrategia de captura)
        ▼
  5. call_openai()         ← GPT-4o con historial + system prompt
        │
        ▼
  6. parse_response()      ← Extrae tags {{NAME:...}} y {{EMAIL:...}}
        │                     Limpia formato para WhatsApp
        ▼
  7. update_conversation() ← Actualiza captured_name, captured_email, phase
        │
        ▼
  8. save_messages()       ← Guarda user_msg + assistant_msg en DB
        │
        ▼
  9. send_whatsapp()       ← Envía respuesta vía WhatsApp Cloud API
        │
        ▼
  10. handle_crm()         ← Si email recién capturado → crea contacto + lead en CRM
```

### Tags de captura en el pipeline

El bot usa tags invisibles en sus respuestas para capturar datos del usuario:

- `{{NAME:Juan Pérez}}` → Captura el nombre real del usuario
- `{{EMAIL:juan@mail.com}}` → Captura el email del usuario

Estos tags se eliminan antes de enviar la respuesta al usuario de WhatsApp.

---

## Webhooks de WhatsApp

### URL del webhook

Cada proyecto tiene un `webhook_token` único generado automáticamente:

```
https://tu-dominio.com/api/hub/webhook/{webhook_token}/
```

### Verificación (GET)

Meta envía un GET con estos parámetros:
- `hub.mode` = `subscribe`
- `hub.verify_token` = el `wa_verify_token` del proyecto
- `hub.challenge` = valor a devolver

El sistema valida el token y devuelve el `challenge`.

### Mensajes entrantes (POST)

- El endpoint siempre responde `200 OK` inmediatamente
- El payload se despacha a **Celery** como tarea asíncrona (`process_whatsapp_message`)
- Solo se procesan mensajes de tipo `text`

---

## Fases de conversación

El bot progresa a través de fases para capturar datos del usuario de forma natural:

```
┌──────────┐   nombre capturado   ┌───────────────────┐   email capturado   ┌──────────────────┐
│ NO_NAME  │ ──────────────────▶ │ HAS_NAME_NO_EMAIL │ ──────────────────▶ │ COMPLETE_PROFILE │
│          │    {{NAME:...}}      │                   │    {{EMAIL:...}}     │                  │
│ Objetivo:│                      │ Objetivo:         │                     │ Atención plena   │
│ Obtener  │                      │ Personalizar +    │                     │ sin pedir más    │
│ nombre   │                      │ obtener email     │                     │ datos            │
└──────────┘                      └───────────────────┘                     └──────────────────┘
```

### Estrategia de captura de nombre

- **Interacción 0:** Bienvenida + mención de especialidades + pedir nombre naturalmente
- **Interacciones impares:** Pide el nombre con frase variada
- **Interacciones pares:** No pide el nombre (da respiro al usuario)

El `interaction_count` se resetea a 0 cuando se captura el nombre.

---

## Integraciones externas

### Iris — Base de conocimiento

| Campo | Valor |
|-------|-------|
| `service_type` | `iris` |
| Función | Búsqueda semántica de documentos relevantes |
| Config extra | `score_threshold` en `chatbot_config.knowledge_base` (default: 0.25) |

Los resultados se inyectan en el system prompt para que el bot responda con información precisa.

### Atlas CRM

| Campo | Valor |
|-------|-------|
| `service_type` | `atlas_crm` |
| Función | Crear contacto + convertir a lead al capturar email |
| Datos enviados | nombre, email, teléfono (+wa_id), notas de conversación |

El CRM se activa automáticamente cuando se captura el email del usuario.

---

## Referencia de API

Base URL: `/api/hub/`

### Proyectos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/projects/` | Listar proyectos del usuario |
| `POST` | `/projects/` | Crear proyecto |
| `GET` | `/projects/{id}/` | Detalle del proyecto |
| `PATCH` | `/projects/{id}/` | Actualizar proyecto |
| `DELETE` | `/projects/{id}/` | Eliminar (soft delete) |

### Setup Chat

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/projects/{id}/setup/chat/` | Obtener / iniciar chat |
| `POST` | `/projects/{id}/setup/chat/` | Enviar mensaje |
| `DELETE` | `/projects/{id}/setup/chat/` | Reiniciar configuración |

### Integraciones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/projects/{id}/integrations/` | Listar integraciones |
| `POST` | `/projects/{id}/integrations/` | Crear integración |
| `PATCH` | `/projects/{id}/integrations/{int_id}/` | Actualizar |
| `DELETE` | `/projects/{id}/integrations/{int_id}/` | Eliminar |

### Conversaciones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/projects/{id}/conversations/` | Listar conversaciones |
| `GET` | `/projects/{id}/conversations/{conv_id}/` | Detalle con mensajes |
| `GET` | `/projects/{id}/conversations/stats/` | Estadísticas por fase |

### Webhook (público, sin auth)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/webhook/{token}/` | Verificación de Meta |
| `POST` | `/webhook/{token}/` | Mensaje entrante |

---

## Estructura del chatbot_config

El `chatbot_config` es un JSON generado por el Setup Chat y almacenado en el proyecto. Define toda la personalidad y comportamiento del bot.

```json
{
  "identity": {
    "company": "Nombre del negocio",
    "description": "Descripción breve",
    "specialties": ["especialidad 1", "especialidad 2"],
    "channel": "WhatsApp",
    "tone": "profesional, cercano y empático"
  },

  "model": {
    "name": "gpt-4o",
    "temperature": 0.7
  },

  "format_rules": [
    "Usa *asterisco simple* para negrita. NUNCA uses **doble asterisco**.",
    "Usa _guion bajo_ para cursiva.",
    "PROHIBIDO: **, ##, backticks, html.",
    "Mensajes cortos: máximo 3-4 párrafos."
  ],

  "capture_tags": {
    "name_tag": "{{NAME:NombreReal}}",
    "email_tag": "{{EMAIL:email@ejemplo.com}}",
    "note": "Si da nombre Y email en un mismo mensaje, pon ambas etiquetas."
  },

  "message_classification": {
    "enabled": true,
    "types": {
      "SALUDO": "hola, buenas, buenos días",
      "PREGUNTA": "consulta sobre servicios, precios",
      "DATOS_PERSONALES": "nombre, email u otro dato",
      "SEGUIMIENTO": "sigue una conversación en curso",
      "OTRO": "cualquier otro caso"
    },
    "note": "No muestres la clasificación al usuario."
  },

  "knowledge_base": {
    "score_threshold": 0.25,
    "intro": "INFORMACIÓN RELEVANTE DE LA BASE DE CONOCIMIENTO:",
    "outro": "Usa esta información para responder de forma precisa."
  },

  "phases": {
    "no_name": {
      "title": "BIENVENIDA Y CAPTACIÓN DE NOMBRE",
      "objective": "conseguir el nombre del usuario de forma natural",
      "constraints": [
        "NUNCA digas que 'necesitas' su nombre.",
        "Siempre responde algo útil antes de pedir el nombre."
      ],
      "strategies": [
        {
          "interaction": 0,
          "label": "primera interacción",
          "instructions": [
            "Bienvenida cálida. Preséntate como asistente de {company}.",
            "Menciona especialidades ({specialties}).",
            "Pregunta nombre de forma natural."
          ]
        }
      ],
      "fallback_strategy": {
        "label_template": "interacción {n}",
        "ask_pattern": "odd",
        "ask_message": "SÍ pide el nombre con frase variada.",
        "skip_message": "NO pidas el nombre, dale respiro."
      }
    },

    "has_name_no_email": {
      "title": "ATENCIÓN PERSONALIZADA",
      "description": [
        "SIEMPRE usa su nombre para personalizar.",
        "En algún momento natural, pregunta su email."
      ],
      "appointment": {
        "title": "AGENDAR CITA",
        "suggestions": ["Sugerir cita en momentos naturales"],
        "on_confirm": {
          "steps": ["Pedir email para confirmar la cita"],
          "on_email_captured": "Listo {name}, pronto recibirás confirmación."
        }
      }
    },

    "complete_profile": {
      "title": "CLIENTE IDENTIFICADO",
      "description": [
        "Ya tienes toda la información. No pidas más datos.",
        "Ofrece servicio excepcional."
      ]
    }
  }
}
```

### Secciones estándar (no se preguntan al usuario)

Las siguientes secciones se incluyen siempre con valores por defecto y **no** se preguntan durante el Setup Chat:

- `format_rules` — Reglas de formato para WhatsApp
- `capture_tags` — Tags de captura de nombre y email
- `knowledge_base` — Configuración de base de conocimiento
- `message_classification` — Tipos de clasificación de mensajes

### Secciones personalizadas (recogidas por Setup Chat)

Estas se construyen con las respuestas del usuario:

- `identity` — Nombre, descripción, especialidades, tono
- `phases` — Estrategias de captura y comportamiento por fase
- `model` — Configuración del modelo (se puede ajustar después)
