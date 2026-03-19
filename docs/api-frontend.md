# Atharix Hub — API Reference (Frontend)

> **Base URL:** `http://localhost:8020`  
> **Swagger UI:** `http://localhost:8020/api/docs/`  
> **ReDoc:** `http://localhost:8020/api/redoc/`  
> **OpenAPI Schema:** `http://localhost:8020/api/schema/`  
> **Versión:** 1.0 — Marzo 2026

---

## Autenticación

Todos los endpoints protegidos requieren el header:

```
Authorization: Bearer <access_token>
```

**JWT:**
| Token | Duración | Rotación |
|-------|----------|----------|
| Access | 1 día | — |
| Refresh | 30 días | Sí (cada refresh emite nuevo par) |

**Claims del JWT (access):**

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "is_staff": false,
  "email_verified": true,
  "token_type": "access",
  "exp": 1773923624,
  "iat": 1773837224,
  "jti": "unique-jwt-id"
}
```

---

## Convenciones

| Concepto | Detalle |
|----------|---------|
| **IDs** | UUIDs en todos los modelos (`"550e8400-e29b-41d4-a716-446655440000"`) |
| **Paginación** | `?page=2&page_size=20` → `{ count, next, previous, results }` |
| **Soft Delete** | `DELETE` marca `is_deleted=true`, nunca elimina de la DB |
| **Timestamps** | ISO 8601 UTC: `"2026-03-18T10:00:00Z"` |
| **Idioma** | Header `Accept-Language: es` para contenido traducido (es, en, pt, fr, it) |
| **Search** | `?search=término` en endpoints que lo soportan |
| **Ordering** | `?ordering=-created_at` (prefijo `-` = descendente) |
| **Avatar URLs** | Signed URLs con expiración de 30 minutos |
| **Write-only** | `api_key`, `wa_access_token`, `openai_api_key`, passwords → nunca se exponen en GET |

### Formato de Errores

```json
// Validación de campos
{
  "email": ["Este campo es requerido."],
  "password": ["La contraseña es muy corta."]
}

// Error general
{
  "detail": "No se encontró.",
  "error_code": "not_found"
}
```

### Códigos HTTP

| Código | Significado |
|--------|-------------|
| `200` | OK |
| `201` | Creado |
| `204` | Sin contenido (delete exitoso) |
| `400` | Request inválido / validación fallida |
| `401` | No autenticado (token faltante o expirado) |
| `403` | Prohibido (sin permisos) |
| `404` | No encontrado |
| `429` | Rate limit excedido |
| `500` | Error del servidor |

---

## Índice

| # | Sección | Prefix |
|---|---------|--------|
| 1 | [Auth — Login / Logout / Token](#1-auth--login--logout--token) | `/api/auth/` |
| 2 | [Registro (3 pasos)](#2-registro-3-pasos) | `/api/auth/register/` |
| 3 | [Verificación de Email](#3-verificación-de-email) | `/api/auth/` |
| 4 | [Recuperación de Contraseña](#4-recuperación-de-contraseña) | `/api/auth/password-reset/` |
| 5 | [Perfil de Usuario](#5-perfil-de-usuario) | `/api/auth/` |
| 6 | [Sesiones y Dispositivos](#6-sesiones-y-dispositivos) | `/api/auth/sessions/` |
| 7 | [Términos y Condiciones](#7-términos-y-condiciones) | `/api/auth/terms/` |
| 8 | [Política de Privacidad](#8-política-de-privacidad) | `/api/auth/privacy/` |
| 9 | [Hub — Proyectos](#9-hub--proyectos) | `/api/hub/projects/` |
| 10 | [Hub — Integraciones](#10-hub--integraciones) | `.../integrations/` |
| 11 | [Hub — Conversaciones](#11-hub--conversaciones) | `.../conversations/` |
| 12 | [Hub — Flows (Motor Visual)](#12-hub--flows-motor-visual) | `.../flows/` |
| 13 | [Hub — Nodos](#13-hub--nodos) | `.../flows/{id}/nodes/` |
| 14 | [Hub — Analytics](#14-hub--analytics) | `.../analytics/` |
| 15 | [Hub — Setup Chat (Onboarding IA)](#15-hub--setup-chat-onboarding-ia) | `.../setup/chat/` |
| 16 | [Hub — Webhook WhatsApp](#16-hub--webhook-whatsapp) | `/api/hub/webhook/` |
| 17 | [Core — Países](#17-core--países) | `/api/core/countries/` |
| 18 | [Core — Notificaciones](#18-core--notificaciones) | `/api/core/notifications/` |
| 19 | [Core — Upload](#19-core--upload) | `/api/core/upload/` |
| 20 | [Health & System](#20-health--system) | `/health/` |

---

## 1. Auth — Login / Logout / Token

### `POST /api/auth/login/`
> Auth: No

```json
// Request
{
  "email": "user@example.com",
  "password": "password123"
}

// Response 200
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "is_staff": false,
    "email_verified": true,
    "avatar": "https://s3.../signed-url?...",
    "date_joined": "2026-01-15T10:00:00Z",
    "last_login": "2026-03-18T10:00:00Z"
  }
}
```

### `POST /api/auth/logout/`
> Auth: Sí

```json
// Request
{ "refresh": "eyJ..." }

// Response 200
{ "message": "Successfully logged out" }
```

### `GET /api/auth/verify-token/`
> Auth: Sí — Verifica si el access token actual es válido.

```json
// Response 200
{
  "valid": true,
  "user": { /* mismo objeto user del login */ }
}
```

### `POST /api/auth/token/refresh/`
> Auth: No

```json
// Request
{ "refresh": "eyJ..." }

// Response 200
{
  "access": "eyJ...",
  "refresh": "eyJ..."  // nuevo refresh (rotación activa)
}
```

---

## 2. Registro (3 pasos)

### Paso 1 — `POST /api/auth/register/check-email/`
> Auth: No — Throttle: **5/hora por IP**

```json
// Request
{ "email": "nuevo@example.com" }

// Response 200
{
  "message": "Código de verificación enviado al correo electrónico.",
  "expires_in_minutes": 15
}

// Error 400
{ "email": ["Ya existe un usuario con este email."] }
```

### Paso 2 — `POST /api/auth/register/verify-pin/`
> Auth: No — Throttle: **10/hora**

```json
// Request
{
  "email": "nuevo@example.com",
  "pin": "1234"
}

// Response 200
{
  "message": "Correo electrónico verificado correctamente.",
  "verification_token": "signed-token-string"
}

// Errores 400
{ "detail": "No hay código pendiente para este email." }
{ "detail": "El código ha expirado. Solicita uno nuevo." }
{ "detail": "Código incorrecto. Te quedan 4 intentos." }
```

### Paso 3 — `POST /api/auth/register/complete/`
> Auth: No — Throttle: **10/hora**

```json
// Request
{
  "verification_token": "signed-token-string",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword123",
  "password_confirm": "securepassword123",
  "terms_id": 1
}

// Response 201
{
  "message": "Usuario registrado exitosamente.",
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {
    "id": "uuid",
    "email": "nuevo@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "is_staff": false,
    "email_verified": true,
    "avatar": null,
    "date_joined": "2026-03-18T10:00:00Z",
    "last_login": "2026-03-18T10:00:00Z"
  }
}
```

> **Notas:**
> - `terms_id`: ID del T&C activo (obtener con `GET /api/auth/terms/latest/`)
> - `password`: mínimo 6 caracteres
> - Se envía email de bienvenida automáticamente
> - El registro legacy `POST /api/auth/register/` sigue disponible pero se recomienda el flujo de 3 pasos

---

## 3. Verificación de Email

### `POST /api/auth/verify-email/`
> Auth: No — Throttle: **20/hora** — Max 5 intentos por código

```json
// Request
{
  "email": "user@example.com",
  "code": "123456"
}

// Response 200
{ "detail": "Email address verified successfully." }
```

### `POST /api/auth/resend-verification/`
> Auth: No — Throttle: **3/hora**

```json
// Request
{ "email": "user@example.com" }

// Response 200
{ "detail": "A new verification code has been sent to your email." }
```

---

## 4. Recuperación de Contraseña

### Paso 1 — `POST /api/auth/password-reset/request/`
> Auth: No — Alias: `POST /api/auth/recovery/`

```json
// Request
{ "email": "user@example.com" }

// Response 200
{
  "message": "Reset PIN sent to your email",
  "hash_token": "abc123def456..."
}
```

> Guardar `hash_token` para el paso 2.

### Paso 2 — `POST /api/auth/password-reset/verify/`
> Auth: No — Alias: `POST /api/auth/check/`

```json
// Request
{
  "email": "user@example.com",
  "hash_token": "abc123def456...",
  "pin": "1234"
}

// Response 200
{ "message": "PIN verified successfully", "valid": true }
```

### Paso 3 — `POST /api/auth/password-reset/confirm/`
> Auth: No

```json
// Request
{
  "email": "user@example.com",
  "hash_token": "abc123def456...",
  "pin": "1234",
  "new_password": "newpassword123",
  "new_password_confirm": "newpassword123"
}

// Response 200
{ "message": "Password reset successfully", "user_id": "uuid" }
```

### Cambiar contraseña (autenticado) — `POST /api/auth/password-change/`
> Auth: Sí — Alias: `POST /api/auth/change-password/`

```json
// Request
{
  "current_password": "oldpassword123",
  "new_password": "newpassword123",
  "new_password_confirm": "newpassword123"
}

// Response 200
{ "message": "Password changed successfully" }
```

---

## 5. Perfil de Usuario

### `GET /api/auth/profile/`
> Auth: Sí

```json
// Response 200
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "birth_date": "1990-01-15",
  "phone_number": "+34666777888",
  "gender": "M",
  "avatar": "https://s3.../signed-url?...",
  "date_joined": "2026-01-15T10:00:00Z",
  "email_verified": true,
  "last_login": "2026-03-18T10:00:00Z"
}
```

### `PATCH /api/auth/profile/`
> Auth: Sí

```json
// Request (todos los campos son opcionales)
{
  "first_name": "Jane",
  "last_name": "Smith",
  "birth_date": "1990-01-15",
  "phone_number": "+34666777888",
  "gender": "F"
}

// Response 200 — perfil actualizado
```

> **Gender choices:** `M` (Masculino), `F` (Femenino), `O` (Otro), `P` (Prefiero no decir)

### `PUT/PATCH /api/auth/update-profile/`
> Auth: Sí — Mismo comportamiento, respuesta incluye `message` + `user`.

### `POST /api/auth/avatar/`
> Auth: Sí — Content-Type: `multipart/form-data`

```
avatar: <archivo imagen>
```

```json
// Response 200
{
  "avatar": "https://s3.../signed-url?...",
  "message": "Avatar uploaded successfully"
}
```

> Formatos: JPEG, PNG, GIF, WEBP. Máximo 5 MB.

### `POST /api/auth/users/delete-account/`
> Auth: Sí

```json
// Request
{
  "password": "currentpassword123",
  "confirmation": "DELETE MY ACCOUNT",
  "refresh_token": "eyJ..."
}

// Response 200
{
  "message": "Tu cuenta ha sido eliminada permanentemente",
  "details": {
    "user_id": "uuid",
    "email": "user@example.com",
    "sessions_deleted": 3,
    "reset_tokens_deleted": 0,
    "terms_acceptances_deleted": 1
  }
}
```

---

## 6. Sesiones y Dispositivos

### `GET /api/auth/sessions/`
> Auth: Sí

```json
// Response 200 (paginado)
{
  "count": 3,
  "results": [
    {
      "id": "uuid",
      "device_name": "iPhone 14 Pro",
      "device_type": "mobile",
      "device_info": "iPhone 14 Pro - iOS 17.2",
      "os_name": "iOS",
      "os_version": "17.2",
      "browser": null,
      "browser_version": null,
      "location": "Madrid, España",
      "ip_address": "192.168.1.100",
      "is_active": true,
      "is_current": true,
      "has_push_notifications": true,
      "fcm_token_updated_at": "2026-03-18T10:30:00Z",
      "created_at": "2026-03-15T10:00:00Z",
      "last_activity": "2026-03-18T10:30:00Z",
      "expires_at": "2026-04-14T10:00:00Z"
    }
  ]
}
```

### `POST /api/auth/sessions/`
> Auth: Sí

```json
// Request
{
  "jti": "jwt-id-from-token",
  "device_name": "iPhone 14 Pro",
  "device_type": "mobile",
  "os_name": "iOS",
  "os_version": "17.2",
  "fcm_token": "firebase-cloud-messaging-token"
}

// Response 201
```

> **device_type:** `mobile`, `desktop`, `web`, `tablet`

### `DELETE /api/auth/sessions/{id}/revoke/`
> Auth: Sí — Revoca una sesión específica (no la actual).

```json
// Response 200
{ "message": "Session revoked successfully" }
```

### `DELETE /api/auth/sessions/revoke_all/`
> Auth: Sí — Revoca todas las sesiones excepto la actual.

```json
// Response 200
{ "message": "All other sessions revoked", "revoked_count": 2 }
```

### `POST /api/auth/sessions/register_fcm_token/`
> Auth: Sí

```json
// Request
{ "fcm_token": "firebase-cloud-messaging-token" }

// Response 200
{
  "message": "FCM token registered successfully",
  "session_id": "uuid",
  "fcm_token_updated_at": "2026-03-18T10:30:00Z"
}
```

### `DELETE /api/auth/sessions/unregister_fcm_token/`
> Auth: Sí

```json
// Response 200
{ "message": "FCM token removed successfully" }
```

---

## 7. Términos y Condiciones

### `GET /api/auth/terms/`
> Auth: No

```json
// Response 200 (paginado)
{
  "count": 1,
  "results": [
    {
      "id": 1,
      "version": "1.0",
      "content": "<h1>Términos y Condiciones de Atharix Hub</h1>...",
      "is_active": true,
      "created_at": "2026-03-18T12:32:00Z"
    }
  ]
}
```

> El campo `content` se localiza automáticamente según `Accept-Language`.

### `GET /api/auth/terms/latest/`
> Auth: No — Solo retorna la versión activa actual.

### `GET /api/auth/terms/{id}/`
> Auth: No

### `GET /api/auth/terms/status/`
> Auth: Sí — Indica si el usuario necesita aceptar una nueva versión.

```json
// Response 200
{
  "current_version": "1.0",
  "user_accepted_version": "1.0",
  "needs_acceptance": false,
  "terms_content": {
    "version": "1.0",
    "title": "Términos y Condiciones",
    "content": "...",
    "created_at": "2026-03-18T12:32:00Z"
  }
}
```

### `POST /api/auth/terms/accept/`
> Auth: Sí

```json
// Request
{ "terms_version": "1.0" }

// Response 201
{
  "message": "Terms accepted successfully",
  "acceptance": {
    "id": 1,
    "user_email": "user@example.com",
    "terms_version": "1.0",
    "accepted_at": "2026-03-18T10:00:00Z",
    "ip_address": "192.168.1.100"
  }
}
```

### `GET /api/auth/terms/history/`
> Auth: Sí — Historial de aceptaciones del usuario.

---

## 8. Política de Privacidad

Misma estructura que Términos. Endpoints disponibles:

| Método | Path | Auth |
|--------|------|------|
| `GET` | `/api/auth/privacy/` | No |
| `GET` | `/api/auth/privacy/latest/` | No |
| `GET` | `/api/auth/privacy/{id}/` | No |

---

## 9. Hub — Proyectos

### `GET /api/hub/projects/`
> Auth: Sí — Solo devuelve proyectos del usuario autenticado.

```json
// Response 200 (paginado)
{
  "count": 2,
  "results": [
    {
      "id": "uuid",
      "name": "Mi Bot WhatsApp",
      "description": "Bot de soporte",
      "status": "active",
      "status_display": "Activo",
      "wa_phone_number_id": "1234567890",
      "wa_verify_token": "my_verify_token",
      "webhook_token": "auto-generated-token",
      "webhook_url": "/api/hub/webhook/auto-generated-token/",
      "chatbot_config": {
        "identity": { "name": "MiBot", "description": "..." },
        "system_prompt": "Eres un asistente...",
        "behavior": { ... }
      },
      "openai_model": "gpt-4o",
      "openai_temperature": 0.7,
      "is_active": true,
      "use_hub_engine": false,
      "has_whatsapp_credentials": true,
      "has_chatbot_config": true,
      "conversation_count": 42,
      "integrations": [ ... ],
      "created_at": "2026-03-18T10:00:00Z",
      "updated_at": "2026-03-18T10:00:00Z"
    }
  ]
}
```

### `POST /api/hub/projects/`
> Auth: Sí

```json
// Request
{
  "name": "Mi Bot WhatsApp",
  "description": "Bot de soporte al cliente",
  "wa_phone_number_id": "1234567890",
  "wa_access_token": "EAAxxxxxxx",
  "wa_verify_token": "my_secret_verify_token",
  "openai_api_key": "sk-...",
  "openai_model": "gpt-4o",
  "openai_temperature": 0.7,
  "chatbot_config": { ... }
}

// Response 201
```

> **Notas:**
> - `webhook_token` se genera automáticamente (32 chars seguro)
> - `wa_access_token` y `openai_api_key` son write-only
> - `owner` se asigna al usuario autenticado

### `GET /api/hub/projects/{id}/`
> Auth: Sí (owner)

### `PATCH /api/hub/projects/{id}/`
> Auth: Sí (owner)

### `DELETE /api/hub/projects/{id}/`
> Auth: Sí (owner) — Soft delete.

---

## 10. Hub — Integraciones

### `GET /api/hub/projects/{project_id}/integrations/`
> Auth: Sí

```json
// Response 200 (paginado)
{
  "count": 2,
  "results": [
    {
      "id": "uuid",
      "service_type": "iris_kb",
      "service_type_display": "Iris Knowledge Base",
      "label": "KB Principal",
      "api_url": "https://iris.example.com/api",
      "api_key_header": "X-API-Key",
      "config": {},
      "is_active": true,
      "created_at": "2026-03-18T10:00:00Z"
    }
  ]
}
```

### `POST /api/hub/projects/{project_id}/integrations/`
> Auth: Sí

```json
// Request
{
  "service_type": "iris_kb",
  "label": "KB Principal",
  "api_url": "https://iris.example.com/api",
  "api_key": "secret-key",
  "api_key_header": "X-API-Key",
  "config": {},
  "is_active": true
}
```

> `api_key` es **write-only**. Nunca se expone en respuestas.

### `PATCH /api/hub/projects/{project_id}/integrations/{id}/`
> Auth: Sí — Si no envías `api_key`, se conserva el existente.

### `DELETE /api/hub/projects/{project_id}/integrations/{id}/`
> Auth: Sí — Soft delete.

---

## 11. Hub — Conversaciones

### `GET /api/hub/projects/{project_id}/conversations/`
> Auth: Sí — **Filtros:** `phase`, `is_lead` — **Search:** `captured_email`, `wa_profile_name`

```json
// Response 200 (paginado)
{
  "count": 150,
  "results": [
    {
      "id": "uuid",
      "wa_id": "34666777888",
      "wa_profile_name": "John Doe",
      "captured_name": "John",
      "captured_email": "john@example.com",
      "phase": "captured",
      "phase_display": "Datos capturados",
      "interaction_count": 12,
      "crm_contact_id": "crm-uuid",
      "is_lead": true,
      "message_count": 12,
      "created_at": "2026-03-15T10:00:00Z",
      "updated_at": "2026-03-18T10:30:00Z"
    }
  ]
}
```

> **Phases:** `initial`, `engaged`, `captured`, `converted`

### `GET /api/hub/projects/{project_id}/conversations/{id}/`
> Auth: Sí — Incluye array de `messages`.

```json
// Response 200
{
  "id": "uuid",
  "wa_id": "34666777888",
  "wa_profile_name": "John Doe",
  // ... campos de conversación ...
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "Hola, quisiera información",
      "wa_message_id": "wamid.xxx",
      "metadata": {},
      "created_at": "2026-03-18T10:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "¡Hola John! Con gusto te ayudo...",
      "wa_message_id": "wamid.yyy",
      "metadata": { "tokens_used": 150 },
      "created_at": "2026-03-18T10:00:05Z"
    }
  ]
}
```

### `GET /api/hub/projects/{project_id}/conversations/stats/`
> Auth: Sí

```json
// Response 200
{
  "total": 150,
  "by_phase": {
    "initial": 30,
    "engaged": 45,
    "captured": 52,
    "converted": 23
  },
  "with_email": 75,
  "leads": 52
}
```

---

## 12. Hub — Flows (Motor Visual)

El motor visual permite diseñar pipelines de procesamiento con nodos conectados en un grafo dirigido.

### `GET /api/hub/projects/{project_id}/flows/`
> Auth: Sí

```json
// Response 200 (paginado)
{
  "count": 2,
  "results": [
    {
      "id": "uuid",
      "name": "Flujo principal",
      "description": "Pipeline de mensajes entrantes",
      "is_active": true,
      "is_draft": false,
      "entry_node_id": "uuid-del-nodo",
      "viewport": { "x": 0, "y": 0, "zoom": 1 },
      "nodes": [ /* array de nodos */ ],
      "node_count": 4,
      "created_at": "2026-03-18T10:00:00Z",
      "updated_at": "2026-03-18T10:00:00Z"
    }
  ]
}
```

### `POST /api/hub/projects/{project_id}/flows/`
> Auth: Sí

```json
// Request
{
  "name": "Flujo soporte",
  "description": "Flujo para soporte al cliente"
}

// Response 201 — Flow vacío (sin nodos)
```

### `GET /api/hub/projects/{project_id}/flows/{id}/`
### `PATCH /api/hub/projects/{project_id}/flows/{id}/`
### `DELETE /api/hub/projects/{project_id}/flows/{id}/`
> Soft delete.

---

### `PUT /api/hub/projects/{project_id}/flows/{id}/canvas/`
> Auth: Sí — **Guarda el canvas completo atómicamente.** Reemplaza todos los nodos.

```json
// Request
{
  "nodes": [
    {
      "node_id": "whatsapp_in_1",
      "node_type": "channel_whatsapp_in",
      "label": "WhatsApp Entrada",
      "position_x": 250,
      "position_y": 100,
      "config": {},
      "connections": { "output": "enrich_1" }
    },
    {
      "node_id": "enrich_1",
      "node_type": "hub_enrich",
      "label": "Enriquecer",
      "position_x": 250,
      "position_y": 250,
      "config": {},
      "connections": { "output": "openai_1" }
    },
    {
      "node_id": "openai_1",
      "node_type": "openai_completion",
      "label": "OpenAI Respuesta",
      "position_x": 250,
      "position_y": 400,
      "config": {},
      "connections": { "output": "whatsapp_out_1" }
    },
    {
      "node_id": "whatsapp_out_1",
      "node_type": "channel_whatsapp_out",
      "label": "WhatsApp Salida",
      "position_x": 250,
      "position_y": 550,
      "config": {},
      "connections": {}
    }
  ],
  "entry_node_id": "whatsapp_in_1",
  "viewport": { "x": 0, "y": 0, "zoom": 1 }
}

// Response 200 — Flow actualizado con todos los nodos
```

### `POST /api/hub/projects/{project_id}/flows/{id}/activate/`
> Auth: Sí — Activa el flow, lo asigna como `active_flow` del proyecto y habilita `use_hub_engine=true`.

```json
// Response 200 — Flow activado
// Error 400 — "El flujo necesita un nodo de entrada para activarse"
```

### `POST /api/hub/projects/{project_id}/flows/{id}/deactivate/`
> Auth: Sí — Desactiva el flow, revierte al pipeline legacy.

### `POST /api/hub/projects/{project_id}/flows/{id}/duplicate/`
> Auth: Sí — Crea copia con todos los nodos. Nombre: `"{original} (copia)"`.

---

## 13. Hub — Nodos

CRUD individual de nodos. Para guardar el canvas completo, usar `PUT .../canvas/` (sección 12).

### `GET /api/hub/projects/{project_id}/flows/{flow_id}/nodes/`
> Auth: Sí

```json
// Response 200 (paginado)
{
  "count": 4,
  "results": [
    {
      "id": "uuid",
      "node_id": "whatsapp_in_1",
      "node_type": "channel_whatsapp_in",
      "node_type_display": "WhatsApp (entrada)",
      "label": "WhatsApp Entrada",
      "position_x": 250.0,
      "position_y": 100.0,
      "config": {},
      "connections": { "output": "enrich_1" }
    }
  ]
}
```

### `POST .../nodes/`
### `PATCH .../nodes/{id}/`
### `DELETE .../nodes/{id}/`

### Tipos de Nodo

| `node_type` | Display | Categoría |
|---|---|---|
| `channel_whatsapp_in` | WhatsApp (entrada) | Canal |
| `channel_whatsapp_out` | WhatsApp (salida) | Canal |
| `openai_completion` | OpenAI Completion | AI |
| `openai_assistant` | OpenAI Assistant | AI |
| `hub_enrich` | Enriquecimiento | Hub |
| `hub_memory` | Memoria de conversación | Hub |
| `iris_search` | Iris Knowledge Base | Integración |
| `atlas_crm_capture` | Atlas CRM Captura | Integración |
| `condition` | Condición | Control de flujo |
| `switch` | Switch | Control de flujo |
| `delay` | Delay | Control de flujo |
| `http_request` | HTTP Request | Datos |
| `set_variable` | Set Variable | Datos |
| `template` | Template | Datos |
| `code` | Código Python | Utilidad |
| `webhook_response` | Webhook Response | Utilidad |

### Estructura de `connections`

Las conexiones definen las aristas del grafo. Cada clave es un nombre de salida y el valor es el `node_id` destino:

```json
// Nodo simple (una salida)
{ "output": "next_node_id" }

// Nodo condicional (dos salidas)
{ "true": "node_if_true", "false": "node_if_false" }

// Con manejo de errores
{ "output": "next_node", "error": "fallback_node" }
```

---

## 14. Hub — Analytics

### `GET /api/hub/projects/{project_id}/analytics/?period=30d`
> Auth: Sí — **Periods:** `1d`, `7d`, `30d`, `90d`, `365d`

```json
// Response 200
{
  "total_conversations": 150,
  "messages_sent": 625,
  "messages_received": 625,
  "leads_captured": 52,
  "avg_response_time": 2.3,
  "conversion_rate": 0.35,
  "avg_tokens_used": 300
}
```

### `GET /api/hub/projects/{project_id}/analytics/timeseries/?metric=messages&granularity=day&period=30d`
> Auth: Sí

| Param | Valores |
|-------|---------|
| `metric` | `messages`, `conversations`, `leads`, `tokens`, `response_time` |
| `granularity` | `hour`, `day`, `week`, `month` |
| `period` | `1d`, `7d`, `30d`, `90d`, `365d` |

```json
// Response 200
{
  "metric": "messages",
  "granularity": "day",
  "period": "30d",
  "data": [
    { "timestamp": "2026-03-01", "value": 45 },
    { "timestamp": "2026-03-02", "value": 52 },
    { "timestamp": "2026-03-03", "value": 38 }
  ]
}
```

---

## 15. Hub — Setup Chat (Onboarding IA)

Chat conversacional con IA para configurar un proyecto nuevo. La IA entrevista al dueño del negocio en 3 secciones: identidad → comportamiento → revisión → genera `chatbot_config`.

### `GET /api/hub/projects/{project_id}/setup/chat/`
> Auth: Sí — Inicia o retoma la sesión de setup.

```json
// Response 200
{
  "message": "¡Hola! Soy el asistente de configuración de Atharix Hub...",
  "is_complete": false,
  "config": null
}
```

### `POST /api/hub/projects/{project_id}/setup/chat/`
> Auth: Sí

```json
// Request
{ "message": "Somos un despacho de abogados especializado en inmigración" }

// Response 200
{
  "message": "¡Perfecto! Un despacho de abogados de inmigración...",
  "is_complete": false,
  "config": null
}

// Cuando completa (is_complete: true)
{
  "message": "¡Configuración lista! Tu bot está preparado...",
  "is_complete": true,
  "config": {
    "identity": { "name": "AbogadoBot", "description": "..." },
    "system_prompt": "Eres el asistente virtual de...",
    "behavior": { ... }
  }
}
```

> Cuando `is_complete: true`, el `config` se guarda automáticamente en `project.chatbot_config`.

### `DELETE /api/hub/projects/{project_id}/setup/chat/`
> Auth: Sí — Resetea la conversación del setup.

```json
// Response 200
{ "message": "Setup chat reset" }
```

---

## 16. Hub — Webhook WhatsApp

Endpoints públicos que recibe WhatsApp Cloud API. **No requieren autenticación.**

### `GET /api/hub/webhook/{webhook_token}/`
> Verificación del webhook por Meta.

Meta envía:
```
?hub.mode=subscribe&hub.verify_token={wa_verify_token}&hub.challenge={challenge}
```

Responde con el `challenge` en plain text si el verify_token coincide.

### `POST /api/hub/webhook/{webhook_token}/`
> Recibe mensajes entrantes de WhatsApp.

Siempre devuelve `200` inmediatamente. El procesamiento es asíncrono via Celery.

---

## 17. Core — Países

### `GET /api/core/countries/`
> Auth: No — **Search:** `name`, `code_iso2`, `phone_code` — **Ordering:** `sort_order`, `name`

```json
// Response 200 (paginado)
{
  "count": 195,
  "results": [
    {
      "id": 1,
      "name": "España",
      "code_iso2": "ES",
      "code_iso3": "ESP",
      "numeric_code": 724,
      "phone_code": "+34",
      "currency_code": "EUR",
      "is_active": true,
      "sort_order": 1
    }
  ]
}
```

> `name` se localiza automáticamente según `Accept-Language`.

### `GET /api/core/countries/active/`
> Solo países con `is_active=true`.

### `GET /api/core/countries/by-language/{language}/`
> Nombres en un idioma específico. **Idiomas:** `es`, `en`, `pt`, `fr`, `it`.

### `GET /api/core/countries/by_phone_code/?code=%2B34`
> Busca por código telefónico.

### `GET /api/core/countries/{id}/`
> Detalle de un país.

---

## 18. Core — Notificaciones

### `GET /api/core/notifications/`
> Auth: Sí

```json
// Response 200 (paginado)
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "title": "Bienvenido",
      "message": "¡Bienvenido a Atharix Hub!",
      "notification_type": "info",
      "is_read": false,
      "url": null,
      "created_at": "2026-03-18T10:00:00Z"
    }
  ]
}
```

### `POST /api/core/notifications/{id}/mark_as_read/`
> Auth: Sí

```json
// Response 200 — notificación actualizada con is_read=true y read_at
```

---

## 19. Core — Upload

### `POST /api/core/upload/user/avatar/`
> Auth: Sí — Content-Type: `multipart/form-data`

```
avatar: <archivo imagen>
```

```json
// Response 200
{
  "avatar": "https://s3.../signed-url?...",
  "message": "Avatar uploaded successfully"
}
```

> Formatos: JPEG, PNG, GIF, WEBP. Máximo 5 MB. Se sube a S3.

---

## 20. Health & System

| Método | Path | Auth | Descripción |
|--------|------|------|-------------|
| `GET` | `/health/` | No | Health check completo (DB + Redis) |
| `GET` | `/ready/` | No | Readiness (Kubernetes) |
| `GET` | `/live/` | No | Liveness (Kubernetes) |
| `GET` | `/api/docs/` | No | Swagger UI interactivo |
| `GET` | `/api/redoc/` | No | ReDoc |
| `GET` | `/api/schema/` | No | OpenAPI JSON schema |

### Health check response:

```json
{
  "status": "healthy",
  "timestamp": 1773837219,
  "version": "1.0.0",
  "environment": "dev",
  "checks": {
    "database": { "status": "healthy", "response_time": 48.33 },
    "redis": { "status": "healthy", "response_time": 3.56 }
  },
  "response_time": 87.85
}
```

---

## Páginas Públicas (HTML — para review Apple/Google)

| Path | Descripción |
|------|-------------|
| `/terms/` | Términos y Condiciones (HTML) |
| `/terms/{version}/` | Versión específica |
| `/privacy/` | Política de Privacidad (HTML) |
| `/privacy/{version}/` | Versión específica |

> Acepta `?lang=es` para seleccionar idioma.

---

## Throttle Limits (Resumen)

| Endpoint | Límite |
|----------|--------|
| Check Email (`register/check-email/`) | 5/hora por IP |
| Registro (`register/`, `register/complete/`) | 10/hora por IP |
| Verify PIN (`register/verify-pin/`) | 10/hora por IP |
| Verificación email | 20/hora por IP |
| Reenviar verificación | 3/hora por IP |
| Login | Sin límite explícito |
| Endpoints autenticados | Sin límite |

---

## Flujo Típico de la App

```
1. Splash Screen
   └─ GET /api/auth/verify-token/
      ├─ 200 → Home (token válido)
      └─ 401 → Login

2. Login
   └─ POST /api/auth/login/
      ├─ Guardar access + refresh en secure storage
      └─ POST /api/auth/sessions/ (registrar dispositivo)

3. Registro
   └─ GET /api/auth/terms/latest/ (obtener terms_id)
   └─ POST /api/auth/register/check-email/
   └─ POST /api/auth/register/verify-pin/
   └─ POST /api/auth/register/complete/ (con terms_id)

4. Home
   └─ GET /api/hub/projects/ (listar bots)

5. Crear Bot
   └─ POST /api/hub/projects/
   └─ GET  /api/hub/projects/{id}/setup/chat/ (iniciar onboarding)
   └─ POST /api/hub/projects/{id}/setup/chat/ (responder preguntas)
   └─ Cuando is_complete=true → chatbot_config guardado

6. Configurar WhatsApp
   └─ PATCH /api/hub/projects/{id}/ (wa_phone_number_id, wa_access_token, wa_verify_token)
   └─ Copiar webhook_url y configurar en Meta Business

7. Flow Engine (editor visual)
   └─ GET  /api/hub/projects/{id}/flows/
   └─ POST /api/hub/projects/{id}/flows/ (crear flow)
   └─ PUT  /api/hub/projects/{id}/flows/{id}/canvas/ (guardar canvas)
   └─ POST /api/hub/projects/{id}/flows/{id}/activate/ (activar)

8. Dashboard
   └─ GET /api/hub/projects/{id}/conversations/stats/
   └─ GET /api/hub/projects/{id}/analytics/?period=30d
   └─ GET /api/hub/projects/{id}/analytics/timeseries/?metric=messages&granularity=day

9. Token Refresh (interceptor HTTP)
   └─ Si access expira (401) → POST /api/auth/token/refresh/
   └─ Si refresh expira → Redirigir a Login
```

---

## Credenciales de Desarrollo

| Campo | Valor |
|-------|-------|
| **Superuser** | `admin@atharix.com` / `admin123` |
| **Admin Panel** | `http://localhost:8020/admin/` |
| **Swagger** | `http://localhost:8020/api/docs/` |
| **Web Port** | `8020` |
