# Atharix Hub — Backend

Plataforma SaaS para desplegar bots de WhatsApp en minutos. Un negocio crea su proyecto, configura su bot con un chat guiado por IA y lo conecta a WhatsApp Cloud API — sin código, sin n8n, sin complicaciones.

## Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Framework | Django 5.x + Django REST Framework |
| Base de datos | PostgreSQL 15 + PostGIS |
| Autenticación | JWT (SimpleJWT + token blacklist) |
| Tareas asíncronas | Celery + RabbitMQ (broker) + Redis (results) |
| IA | OpenAI GPT-4o (onboarding + chatbot) |
| Mensajería | WhatsApp Cloud API (Meta Graph API v22.0) |
| Pagos | Stripe (suscripciones + webhooks) |
| Almacenamiento | AWS S3 (django-storages) / local |
| Email | Resend |
| Admin | django-unfold |
| API Docs | drf-spectacular (Swagger + ReDoc) |
| Contenedores | Docker Compose |

## Arquitectura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend    │────▶│  Nginx :80  │────▶│  Django :8000│
│  (Next.js)   │     │  (proxy)    │     │  (DRF API)  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────┬────────────┼────────────┐
                    │              │            │            │
              ┌─────▼─────┐ ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
              │ PostgreSQL │ │ RabbitMQ  │ │ Redis │ │  Celery   │
              │   :5450    │ │   :5690   │ │ :6390 │ │ (workers) │
              └───────────┘ └───────────┘ └───────┘ └───────────┘
```

## Estructura del Proyecto

```
atharixhub_backend/
├── docker-compose.yml
├── .env                        # Variables de entorno
├── fixtures/                   # Datos iniciales
├── requirements/
│   └── requirements.txt
├── app/
│   ├── Dockerfile
│   ├── manage.py
│   ├── config/                 # Settings, URLs, Celery
│   ├── core/                   # BaseModel, utilidades, uploads
│   ├── users/                  # Autenticación, JWT, usuarios
│   ├── business/               # Negocios, sucursales, miembros
│   ├── hub/                    # ★ App principal — bots de WhatsApp
│   ├── bridge/                 # API Keys para integraciones externas
│   └── subscriptions/          # Suscripciones Stripe
└── nginx/
```

## Hub — La App Principal

Hub es el corazón de Atharix Hub. Gestiona todo el ciclo de vida de un bot de WhatsApp:

### Modelos

| Modelo | Descripción |
|---|---|
| `Project` | Un bot desplegado con su config, credenciales WA y webhook |
| `ProjectIntegration` | Conexiones externas (Iris, CRM, custom) |
| `Conversation` | Estado de conversación por usuario de WhatsApp |
| `Message` | Mensajes individuales (user/assistant/system) |
| `SetupChat` | Chat de onboarding con IA para configurar el bot |

### Ciclo de Vida de un Proyecto

```
1. Crear proyecto (POST /api/hub/projects/)
       ↓
2. Setup Chat — IA entrevista al dueño del negocio
   GET  /api/hub/projects/{id}/setup/chat/   → inicia conversación
   POST /api/hub/projects/{id}/setup/chat/   → envía mensaje
       ↓
   Sección 1: Identidad (nombre, descripción, especialidades, tono)
   Sección 2: Comportamiento (tipos de mensajes, citas, instrucciones)
   Sección 3: Revisión (resumen + confirmación → genera chatbot_config)
       ↓
3. Configurar credenciales de WhatsApp Cloud API
   PATCH /api/hub/projects/{id}/
   {wa_phone_number_id, wa_access_token, wa_verify_token}
       ↓
4. Configurar webhook en Meta
   URL: /api/hub/webhook/{webhook_token}/
       ↓
5. Activar proyecto → status: "active"
       ↓
   ¡Bot funcionando! 🚀
```

### Pipeline de Mensajes (flow.py)

Cuando llega un mensaje de WhatsApp al webhook:

```
Mensaje entrante
    ↓
1. Extraer datos del payload de WhatsApp
2. Obtener/crear conversación + historial
3. Buscar en base de conocimiento (Iris)
4. Construir system prompt (config + fase + knowledge)
5. Llamar OpenAI
6. Parsear respuesta (extraer tags {{NAME:...}} {{EMAIL:...}})
7. Actualizar perfil/fase de conversación
8. Guardar mensajes en BD
9. Enviar respuesta por WhatsApp
10. Integración CRM (si se capturó email)
```

### Fases de Conversación

El bot maneja 3 fases automáticamente:

| Fase | Objetivo |
|---|---|
| `no_name` | Bienvenida + capturar nombre de forma natural |
| `has_name_no_email` | Atención personalizada + capturar email |
| `complete_profile` | Servicio completo con toda la info |

## API Endpoints

### Autenticación
```
POST   /api/auth/login/              → JWT tokens
POST   /api/auth/register/           → Registro
POST   /api/auth/token/refresh/      → Refrescar access token
```

### Negocio
```
GET    /api/business/businesses/      → Listar mis negocios
POST   /api/business/businesses/      → Crear negocio
GET    /api/business/types/           → Tipos de negocio
```

### Hub (Bots)
```
GET    /api/hub/projects/                              → Listar proyectos
POST   /api/hub/projects/                              → Crear proyecto
GET    /api/hub/projects/{id}/                         → Detalle
PATCH  /api/hub/projects/{id}/                         → Actualizar

GET    /api/hub/projects/{id}/setup/chat/              → Obtener/iniciar setup
POST   /api/hub/projects/{id}/setup/chat/              → Enviar mensaje al setup
DELETE /api/hub/projects/{id}/setup/chat/              → Reiniciar setup

GET    /api/hub/projects/{id}/integrations/            → Integraciones
POST   /api/hub/projects/{id}/integrations/            → Crear integración

GET    /api/hub/projects/{id}/conversations/           → Conversaciones
GET    /api/hub/projects/{id}/conversations/{id}/      → Detalle + mensajes
GET    /api/hub/projects/{id}/conversations/stats/     → Estadísticas

POST   /api/hub/webhook/{token}/                       → Webhook WhatsApp (público)
GET    /api/hub/webhook/{token}/                       → Verificación Meta
```

### Documentación API
```
GET    /api/docs/                     → Swagger UI
GET    /api/redoc/                    → ReDoc
```

## Setup Local

### 1. Clonar y configurar

```bash
git clone git@github.com:atharix/atlas_backend.git
cd atlas_backend
cp .env.example .env
```

### 2. Configurar `.env`

Valores mínimos para desarrollo:

```env
ENVIRONMENT=dev
DEBUG=True
DB_NAME=atharixhub_db
DB_USER=atharixhub_user
DB_PASSWORD=tu-password
DB_PORT=5450
REDIS_PORT=6390
WEB_PORT=8020
SECRET_KEY=genera-una-key-con-django
OPENAI_API_KEY=sk-proj-tu-api-key    # Necesario para el setup chat
```

### 3. Levantar servicios

```bash
docker compose up -d
```

Esto levanta: PostgreSQL, Redis, RabbitMQ, Django, Nginx y workers de Celery.

### 4. Verificar

```bash
# Ver logs
docker compose logs web --tail=20

# Probar health check
curl http://localhost:8020/health/

# Login (superuser auto-creado: admin@atharix.com / admin123)
curl -X POST http://localhost:8020/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@atharix.com", "password": "admin123"}'
```

### 5. Crear tu primer bot

```bash
TOKEN="tu-access-token-jwt"

# 1. Crear negocio
curl -X POST http://localhost:8020/api/business/businesses/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mi Negocio", "business_type": "ID_DEL_TIPO"}'

# 2. Crear proyecto
curl -X POST http://localhost:8020/api/hub/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mi Bot", "business_id": "ID_DEL_NEGOCIO"}'

# 3. Iniciar configuración guiada por IA
curl http://localhost:8020/api/hub/projects/{ID}/setup/chat/ \
  -H "Authorization: Bearer $TOKEN"

# 4. Responder preguntas del setup
curl -X POST http://localhost:8020/api/hub/projects/{ID}/setup/chat/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Somos un despacho de abogados..."}'
```

## Puertos

| Servicio | Puerto |
|---|---|
| Web (Nginx) | 8020 |
| PostgreSQL | 5450 |
| Redis | 6390 |
| RabbitMQ | 5690 |
| RabbitMQ Management | 15690 |

## Comandos Útiles

```bash
# Logs de un servicio
docker compose logs web -f

# Ejecutar comando Django
docker compose exec web python manage.py shell

# Crear migraciones
docker compose exec web python manage.py makemigrations

# Aplicar migraciones
docker compose exec web python manage.py migrate

# Cargar fixtures
docker compose exec web python manage.py loaddata fixtures/business_types.json

# Lint
docker compose exec web ruff check .

# Admin panel
http://localhost:8020/admin/   (admin@atharix.com / admin123)
```
