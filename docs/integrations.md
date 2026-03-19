# Atharix Hub — Integraciones con Servicios Externos

Documento técnico sobre cómo Atharix Hub se conecta con los servicios externos: **WhatsApp Cloud API**, **OpenAI**, **Iris (Knowledge Base)** y **Atlas CRM**.

---

## Arquitectura General

```
                                ┌──────────────┐
                                │   Frontend   │
                                └──────┬───────┘
                                       │ REST API
                                       ▼
┌──────────────┐  webhook   ┌──────────────────┐   async    ┌─────────┐
│   WhatsApp   │ ─────────► │  Atharix Hub Backend│ ────────► │  Celery │
│  Cloud API   │ ◄───────── │   (Django + DRF)  │ ◄──────── │  Worker │
└──────────────┘  send msg  └──────────────────┘            └────┬────┘
                                                                 │
                              ┌──────────────────────────────────┼──────────────┐
                              │                                  │              │
                              ▼                                  ▼              ▼
                        ┌──────────┐                      ┌──────────┐   ┌──────────┐
                        │  OpenAI  │                      │   Iris   │   │  Atlas   │
                        │  GPT-4o  │                      │    KB    │   │   CRM    │
                        └──────────┘                      └──────────┘   └──────────┘
```

---

## 1. WhatsApp Cloud API (Meta)

### Configuración por proyecto

Cada `Project` almacena sus credenciales de WhatsApp:

| Campo | Descripción |
|-------|-------------|
| `wa_phone_number_id` | ID del número de teléfono en Meta Business |
| `wa_access_token` | Token de acceso permanente (write-only en API) |
| `wa_verify_token` | Token para verificación del webhook por Meta |
| `webhook_token` | Token auto-generado (`secrets.token_urlsafe(32)`) que forma parte de la URL del webhook |

### URL del Webhook

```
POST https://{domain}/api/hub/webhook/{webhook_token}/
```

Se configura en el panel de Meta Business → App → WhatsApp → Configuration → Webhook URL.

### Verificación del Webhook (GET)

Meta envía un `GET` para verificar el webhook:

```
GET /api/hub/webhook/{webhook_token}/?hub.mode=subscribe&hub.verify_token={wa_verify_token}&hub.challenge={challenge}
```

Atharix Hub valida que `hub.verify_token` coincida con `project.wa_verify_token` y responde con el `challenge` en texto plano.

### Recepción de Mensajes (POST)

Meta envía los mensajes entrantes vía `POST`. Atharix Hub:

1. Busca el proyecto por `webhook_token`
2. Crea un `WebhookEvent` con `status=RECEIVED`
3. Despacha la tarea Celery `process_whatsapp_message.delay(project_id, payload, event_id)`
4. Responde `200 OK` inmediatamente (requerimiento de Meta)

**Archivo:** `hub/views/webhook.py`

### Envío de Mensajes

**Archivo:** `hub/services/whatsapp.py` → clase `WhatsAppService`

```
POST https://graph.facebook.com/v22.0/{phone_number_id}/messages
Headers:
  Authorization: Bearer {wa_access_token}
  Content-Type: application/json

Body:
{
  "messaging_product": "whatsapp",
  "to": "34612345678",
  "type": "text",
  "text": {"body": "Hola, ¿en qué puedo ayudarte?"}
}
```

- **Timeout:** 15 segundos
- **Métodos:** `send_text()` (async) y `send_text_sync()` (sync, usado en Celery)

---

## 2. OpenAI

### Configuración por proyecto

| Campo | Descripción | Default |
|-------|-------------|---------|
| `openai_api_key` | API key de OpenAI (write-only en API) | — |
| `openai_model` | Modelo a usar | `gpt-4o` |
| `openai_temperature` | Temperatura de generación | `0.7` |

### Llamada a la API

**Archivo:** `hub/services/flow.py` → función `call_openai()`

```
POST https://api.openai.com/v1/chat/completions
Headers:
  Authorization: Bearer {openai_api_key}
  Content-Type: application/json

Body:
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "{system_prompt generado dinámicamente}"},
    {"role": "user", "content": "mensaje anterior 1"},
    {"role": "assistant", "content": "respuesta anterior 1"},
    ...últimos 20 mensajes de historial...
    {"role": "user", "content": "mensaje actual del usuario"}
  ],
  "temperature": 0.7
}
```

- **Timeout:** 30 segundos
- **Historial:** Últimos 20 mensajes de la conversación
- **System prompt:** Generado dinámicamente por `build_system_prompt()` combinando:
  - Identidad del negocio (`chatbot_config.identity`)
  - Reglas de formato para WhatsApp (`chatbot_config.format_rules`)
  - Etiquetas de captura `{{NAME:...}}` y `{{EMAIL:...}}`
  - Fase actual de la conversación (sin nombre → con nombre → perfil completo)
  - Resultados de Iris KB (si hay integración activa)

### Respuesta

```json
{
  "content": "texto de la respuesta",
  "tokens_prompt": 1234,
  "tokens_completion": 256,
  "tokens_total": 1490,
  "latency_ms": 2300,
  "model": "gpt-4o-2024-08-06"
}
```

Si falla, retorna un mensaje genérico de error + `"error": true` en las métricas.

---

## 3. Iris — Knowledge Base

### Modelo de integración

Se configura como una `ProjectIntegration` con `service_type = "iris"`:

```
POST /api/hub/projects/{project_id}/integrations/
{
  "service_type": "iris",
  "label": "Base de conocimiento principal",
  "api_url": "https://iris.example.com/api/v1/search",
  "api_key": "iris-api-key-xxx",
  "api_key_header": "X-API-Key"
}
```

### Llamada a la API

**Archivo:** `hub/services/knowledge.py` → clase `KnowledgeService`

```
POST {api_url}
Headers:
  {api_key_header}: {api_key}
  Content-Type: application/json

Body:
{
  "query": "texto del mensaje del usuario",
  "limit": 5
}
```

- **Timeout:** 10 segundos

### Respuesta esperada de Iris

```json
{
  "results": [
    {
      "text": "Contenido relevante del documento...",
      "score": 0.85,
      "metadata": {
        "title": "Nombre del documento"
      }
    },
    {
      "text": "Otro fragmento relevante...",
      "score": 0.72,
      "metadata": {
        "title": "Otro documento"
      }
    }
  ]
}
```

### Filtrado por score

Solo se usan resultados con `score > score_threshold`.

El threshold es configurable en `chatbot_config.knowledge_base.score_threshold` (default: **0.25**).

### Cómo se usa

Los resultados se inyectan en el system prompt de OpenAI como sección contextual:

```
INFORMACIÓN RELEVANTE DE LA BASE DE CONOCIMIENTO:

--- Nombre del documento ---
Contenido relevante del documento...

--- Otro documento ---
Otro fragmento relevante...
```

Esto permite que el bot responda con datos reales del negocio sin inventar información.

### Si no hay integración Iris

El bot responde normalmente usando solo su `chatbot_config` (personalidad, instrucciones), sin contexto de knowledge base. Retorna lista vacía.

---

## 4. Atlas CRM

### Modelo de integración

Se configura como una `ProjectIntegration` con `service_type = "atlas_crm"`:

```
POST /api/hub/projects/{project_id}/integrations/
{
  "service_type": "atlas_crm",
  "label": "Atlas CRM",
  "api_url": "https://atlas.example.com/api/contacts",
  "api_key": "atlas-api-key-xxx",
  "api_key_header": "X-API-Key"
}
```

### Cuándo se activa

**Solo** cuando se cumplen estas condiciones simultáneamente:
1. El email **acaba de ser capturado** en esta interacción (`email_just_captured = True`)
2. La conversación ya tiene `captured_name` y `captured_email`
3. Existe una integración `atlas_crm` activa en el proyecto

### Llamada 1: Crear contacto

**Archivo:** `hub/services/crm.py` → `CRMService.capture_contact()`

```
POST {api_url}/capture/
Headers:
  {api_key_header}: {api_key}
  Content-Type: application/json

Body:
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "email": "juan@mail.com",
  "phone": "+34612345678",
  "source_detail": "WhatsApp Bot",
  "tags": ["whatsapp"],
  "notes": "Usuario: Hola, quiero información\nBot: ¡Hola! ¿En qué puedo ayudarte?\n..."
}
```

- **Timeout:** 10 segundos
- **Notas:** Se incluyen los últimos 6 mensajes de la conversación (máx. 200 chars cada uno)
- **Nombre:** Se divide `captured_name` por el primer espacio → `first_name` + `last_name`

### Respuesta esperada

```json
{
  "contact_id": "abc123",
  "id": "abc123"
}
```

Se acepta `contact_id` o `id` como identificador del contacto creado.

### Llamada 2: Convertir a Lead

```
POST {api_url}/{contact_id}/convert-to-lead/
Headers:
  {api_key_header}: {api_key}
  Content-Type: application/json

Body:
{
  "title": "Consulta - Juan Pérez",
  "priority": "medium",
  "currency": "EUR",
  "notes": "Lead generado desde WhatsApp Bot. Usuario: Hola...\nBot: ..."
}
```

### Post-captura

Si ambas llamadas son exitosas:
- Se guarda `crm_contact_id` en la conversación
- Se marca `is_lead = True`

### Si no hay integración Atlas

No se ejecuta ninguna llamada. El bot funciona normalmente sin CRM.

---

## 5. Modelo ProjectIntegration

**Archivo:** `hub/models/integration.py`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `project` | FK → Project | Proyecto asociado |
| `service_type` | `iris` / `atlas_crm` / `custom` | Tipo de servicio |
| `label` | CharField(100) | Nombre descriptivo |
| `api_url` | URLField(500) | URL base del servicio |
| `api_key` | TextField | API key (write-only en REST, nunca se expone en GET) |
| `api_key_header` | CharField(100) | Header HTTP para la API key (default: `X-API-Key`) |
| `config` | JSONField | Configuración extra por servicio |
| `is_active` | BooleanField | Si está activa |

**Constraint:** Solo una integración activa por `(project, service_type)`.

### Endpoints REST

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/hub/projects/{id}/integrations/` | Listar integraciones |
| POST | `/api/hub/projects/{id}/integrations/` | Crear integración |
| GET | `/api/hub/projects/{id}/integrations/{int_id}/` | Detalle |
| PUT/PATCH | `/api/hub/projects/{id}/integrations/{int_id}/` | Actualizar |
| DELETE | `/api/hub/projects/{id}/integrations/{int_id}/` | Eliminar (soft delete) |

---

## 6. Pipeline Completo de un Mensaje

**Archivo:** `hub/services/flow.py` → `process_incoming_message()`

```
Meta WhatsApp
     │
     │ POST /api/hub/webhook/{token}/
     ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. extract_message()                                        │
│    Parsea payload de Meta → {wa_id, text, wa_message_id}    │
│                                                             │
│ 2. get_or_create_conversation()                             │
│    Busca/crea conversación por (project + wa_id)            │
│    Carga historial (últimos 20 mensajes)                    │
│                                                             │
│ 3. search_knowledge()           ──► POST Iris API           │
│    Si hay integración iris activa                           │
│    Filtra por score_threshold                               │
│                                                             │
│ 4. build_system_prompt()                                    │
│    chatbot_config + fase + knowledge results                │
│                                                             │
│ 5. call_openai()                ──► POST OpenAI API         │
│    system_prompt + historial + mensaje actual               │
│    Retorna: texto + tokens + latencia                       │
│                                                             │
│ 6. parse_response()                                         │
│    Extrae {{NAME:...}} y {{EMAIL:...}}                      │
│    Limpia formato para WhatsApp                             │
│                                                             │
│ 7. update_conversation_profile()                            │
│    Actualiza nombre/email capturados + fase                 │
│                                                             │
│ 8. save_messages()                                          │
│    Persiste mensaje del usuario + respuesta del bot         │
│                                                             │
│ 9. send_whatsapp()              ──► POST Graph API Meta     │
│    Envía respuesta al usuario                               │
│                                                             │
│ 10. handle_crm_capture()        ──► POST Atlas CRM API      │
│     Solo si email recién capturado                          │
│     capture_contact + convert_to_lead                       │
└─────────────────────────────────────────────────────────────┘
```

### Métricas registradas por mensaje

Cada ejecución del pipeline registra en `WebhookEvent.metrics`:

| Métrica | Descripción |
|---------|-------------|
| `wa_message_id` | ID del mensaje de WhatsApp |
| `phase_before` / `phase_after` | Fase antes y después del procesamiento |
| `knowledge_results_count` | Resultados encontrados en Iris |
| `openai_tokens_prompt` | Tokens del prompt enviado |
| `openai_tokens_completion` | Tokens generados |
| `openai_tokens_total` | Total de tokens |
| `openai_latency_ms` | Latencia de la llamada a OpenAI |
| `openai_model` | Modelo usado |
| `name_captured` | Si se capturó nombre en esta interacción |
| `email_captured` | Si se capturó email en esta interacción |
| `whatsapp_sent` | Si se envió la respuesta por WhatsApp |
| `crm_triggered` | Si se ejecutó la captura en Atlas CRM |

---

## 7. Seguridad de Credenciales

| Credencial | Almacenamiento | Exposición en API |
|------------|---------------|-------------------|
| `wa_access_token` | `Project.wa_access_token` (TextField) | **write-only** — nunca se retorna en GET |
| `openai_api_key` | `Project.openai_api_key` (TextField) | **write-only** — nunca se retorna en GET |
| `api_key` (integraciones) | `ProjectIntegration.api_key` (TextField) | **write-only** — nunca se retorna en GET |
| `webhook_token` | `Project.webhook_token` (auto-generado) | read-only, no editable |
| `wa_verify_token` | `Project.wa_verify_token` | lectura/escritura normal |

> **Nota:** Las credenciales se almacenan como texto plano en la BD. La protección depende de encriptación a nivel de disco/BD del servidor.

---

## 8. Timeouts y Manejo de Errores

| Servicio | Timeout | En caso de error |
|----------|---------|------------------|
| Iris KB | 10s | Retorna `[]` — el bot responde sin contexto |
| OpenAI | 30s | Retorna mensaje genérico de error |
| WhatsApp | 15s | Log del error, no reintenta |
| Atlas CRM | 10s | Log del error, no reintenta |

Todas las llamadas HTTP usan `httpx` (sync) y capturan `httpx.HTTPError`.

---

## 9. Librería HTTP

Todas las conexiones usan **`httpx`** (no `requests`):
- Sync: `httpx.Client()` (en tareas Celery)
- Async: `httpx.AsyncClient()` (disponible en WhatsApp, no usado actualmente en el pipeline)
