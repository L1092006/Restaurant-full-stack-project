# Restaurant Full-Stack Project

A full-stack restaurant ordering platform with a Django REST API backend, a React (Vite) frontend, and a standalone AI chatbot service that can converse with users and act inside the live app on their behalf.

## Overview

This project lets customers browse a restaurant's menu, manage a cart, place orders, and track order status, while admins/staff can manage menu items, categories, and orders through role-based permissions. An AI assistant is integrated as a separate service that can answer questions, look up menu items and orders, and navigate or modify the user's cart directly in the browser via tool calls.

## Architecture

```
Restaurant-full-stack-project/
├── backend/                  # Django REST Framework API (MySQL)
│   └── restaurantAPI/
│       ├── api/               # Models, serializers, views, tests
│       └── restaurantAPI/     # Django project settings/urls
├── chatbot_backend/          # LangGraph-based AI agent (WebSocket server)
│   ├── chatbot.py             # Agent graph: memory, tools, summarization
│   ├── server.py              # WebSocket server bridging client <-> agent
│   └── prompts.py             # System prompts
├── frontend/restaurant/      # React + Vite SPA
│   └── src/
│       ├── contexts/          # Auth, Cart, Chatbot state
│       ├── pages/              # Route-level pages
│       └── components/        # Reusable UI (Chakra UI-based)
└── deploy/                    # AWS infrastructure-as-code
    ├── cloud_formation_templates/   # vpc_dev.yaml + backend_infra.yaml
    └── scripts/               # Bash deploy / teardown automation
```

## Tech Stack

**Backend (API)**
- Django 6 + Django REST Framework
- MySQL (via a `PyMySQL` driver shim installed as MySQLdb)
- Custom cookie-based JWT authentication (built on `djangorestframework-simplejwt`)
- `django-environ` for environment-based configuration
- `django-cors-headers` for cross-origin requests
- `gunicorn` as the production WSGI server

**Frontend**
- React 18 + Vite 7
- Chakra UI v3 for components/theming
- React Router v7
- React Hook Form + Zod for form validation
- Context API for auth, cart, and chatbot state

**AI Chatbot Service**
- LangGraph for the agent's stateful reasoning graph
- LangChain (OpenRouter / OpenAI / Ollama-compatible) for the underlying LLM
- Pinecone for vector-based long-term memory retrieval
- WebSockets for real-time bidirectional communication with the frontend
- SQLite for agent checkpointing (conversation state persistence)

**Infrastructure (AWS)**
- CloudFormation across two stacks: a VPC/networking stack and an application stack
- Application Load Balancer with HTTPS (ACM) and path-based routing to the API and chatbot
- Auto Scaling Group of EC2 (self-provisioning via launch-template UserData + systemd)
- RDS MySQL for the database
- S3 + CloudFront (Origin Access Control) for the static frontend

## Features

### Customer-facing
- Sign up / log in with JWT-based authentication (access token in memory, refresh token in an httpOnly cookie)
- Browse menu items by category
- Add, update, and remove items from a persistent cart
- Place orders and view order history / order status
- Cancel their own pending orders
- Chat with an AI assistant that can answer questions, browse the menu, and manage the cart on their behalf

### Admin / staff
- Full CRUD on menu items and categories (Django model permissions)
- View and manage all orders and carts (permission-gated)
- Update order status through its lifecycle (processing → preparing → shipping → completed)

### AI Assistant
- Maintains long-term memory per user via Pinecone (past conversations + site info)
- Summarizes and prunes conversation history to stay within context limits
- Calls tools that execute in the user's live browser session (navigate pages, add cart items, fetch orders) via a WebSocket tool-call protocol
- Updates a running user profile between sessions based on conversation history

## Getting Started

### Prerequisites
- Python 3.12+ (Django 6 requires 3.12 or newer)
- Node.js 18+
- MySQL server
- (Optional, for the chatbot) Pinecone API key and an OpenRouter/OpenAI API key, or a local Ollama model

### Backend setup
```bash
# NOTE: requirements.txt lives in backend/, but manage.py lives in backend/restaurantAPI/
cd backend
pip install -r requirements.txt
cd restaurantAPI

# Create a .env file (next to manage.py) with at least:
#   SECRET_KEY=<your Django secret key>
#   STAGE=DEV                      # DEBUG is on unless STAGE=PROD
#   TAX=0.08
#   ALLOWED_ORIGINS=http://localhost:5173
#   DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT   (MySQL credentials)

python manage.py migrate
python manage.py runserver
```

### Frontend setup
```bash
cd frontend/restaurant
npm install

# Create a .env file with:
#   VITE_BACKEND_URL=http://localhost:8000/api   # REST base — must NOT end in a slash
#   VITE_CHATBOT_URL=ws://localhost:8001/chat    # chatbot WebSocket
#   VITE_DEBUG=true

npm run dev
```

### Chatbot service setup
```bash
cd chatbot_backend
pip install -r requirements.txt

# Create a .env file with:
#   CLOUD=true                      # true = OpenRouter, false = local Ollama
#   OPENROUTER_MODEL=<model name>
#   OPENROUTER_API_KEY=<key>
#   PINECONE_API_KEY=<key>
#   INDEX_NAME=<pinecone index name>
#   MODEL_CONTEXT=<context window size>
#   MEMORY_LENGTH=<max words per memory chunk>
#   DB_NAME / DB_USER / DB_PASSWORD / DB_HOST / DB_PORT   (MySQL — the server creates its tables on startup)

python server.py
```

## API Overview

| Endpoint | Description |
|---|---|
| `POST /api/auth/signup/` | Create a new user account |
| `POST /api/auth/login/` | Authenticate, returns access token + sets refresh cookie |
| `POST /api/auth/refresh/` | Rotate access token using the refresh cookie |
| `POST /api/auth/logout/` | Clear the refresh cookie (ends the session) |
| `GET/POST /api/items/` | List / create menu items |
| `GET/POST /api/categories/` | List / create categories |
| `GET/POST/PATCH/DELETE /api/carts/` | Manage the current user's cart |
| `GET/POST/PATCH /api/orders/` | Place and manage orders |
| `GET /api/users/<id or "me">/` | Fetch user profile |

## Testing

The Django backend includes an APITestCase suite covering authentication flows (signup, login, refresh, logout) and permission edge cases.

```bash
cd backend/restaurantAPI
python manage.py test
```

> Note: the test runner uses MySQL directly (it creates a `test_<DB_NAME>` database), so a reachable MySQL server with create privileges is required — there is no SQLite fallback.

## Deployment (AWS)

Infrastructure is defined as code in `deploy/` and provisioned with **two CloudFormation stacks that must be created in order**:

1. **VPC stack** (`vpc_dev.yaml`) — VPC, public/private subnets across 2 AZs, Internet Gateway, and a NAT gateway.
2. **Application stack** (`backend_infra.yaml`) — an internet-facing ALB (HTTPS with HTTP→HTTPS redirect) that path-routes `/api/*` to the Django service and `/chat*` to the chatbot service, an Auto Scaling Group of EC2 in private subnets, RDS MySQL, and an S3 + CloudFront distribution (OAC) for the frontend.

The app stack imports the network stack's outputs, so its `NetworkStackName` parameter must equal the VPC stack's name. EC2 instances **self-provision at boot**: launch-template UserData clones the repo, checks out the `deploy_aws` branch, and runs each service's `setup.sh` (virtualenv, `.env`, migrations, and systemd units). Push code to `deploy_aws` before launching new instances — nothing is baked into an AMI.

The frontend is **not** deployed by the stack; build and upload it manually:

```bash
cd frontend/restaurant && npm run build
aws s3 sync dist s3://<frontend-bucket> --delete
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```

See `deploy/README.md` and `CLAUDE.md` for the full parameter list, ordered commands, and known deployment gotchas.

## License

No license specified yet.
