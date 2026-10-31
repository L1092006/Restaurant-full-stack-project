# Restaurant Full-Stack Project

A full-stack restaurant ordering platform with a Django REST API backend, a React (Vite) frontend, and a standalone AI chatbot service that can converse with users and act inside the live app on their behalf.

**Jump to:** [Run it locally](#run-it-locally) · [Testing](#testing) · [CI/CD](#cicd-github-actions) · [Deploy to AWS](deploy/README.md)

## Overview

This project lets customers browse a restaurant's menu, manage a cart, place orders, and track order status, while admins/staff can manage menu items, categories, and orders through role-based permissions. An AI assistant is integrated as a separate service that can answer questions, look up menu items and orders, and navigate or modify the user's cart directly in the browser via tool calls.

## Architecture

```
Restaurant-full-stack-project/
├── .github/workflows/        # CI/CD: tests on every PR, build + deploy on every merge to main
├── backend/                  # Django REST Framework API (MySQL) + Dockerfile
│   └── restaurantAPI/
│       ├── api/              # Models, serializers, views, tests
│       └── restaurantAPI/    # Django project settings/urls
├── chatbot_backend/          # LangGraph-based AI agent (WebSocket server) + Dockerfile
│   ├── chatbot.py            # Agent graph: memory, tools, summarization
│   ├── server.py             # WebSocket server bridging client <-> agent
│   └── prompts.py            # System prompts
├── frontend/restaurant/      # React + Vite SPA
│   └── src/
│       ├── contexts/         # Auth, Cart, Chatbot state
│       ├── pages/            # Route-level pages
│       └── components/       # Reusable UI (Chakra UI-based)
└── deploy/                   # AWS infrastructure-as-code
    ├── cloud_formation_templates/   # vpc_dev.yaml + backend_infra.yaml
    └── scripts/              # deploy / upload / teardown scripts
```

How the pieces fit together in production:

```
Browser ──► CloudFront + S3 ............................ React app (static files)
   │
   └─────► Load balancer (HTTPS) ──┬─ /api/*  ──► web_backend container (Django, :8000) ──┐
                                   └─ /chat   ──► chatbot container (WebSocket, :8001) ───┴──► RDS MySQL

           Both containers run on every EC2 server in an Auto Scaling group.
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

**Infrastructure & delivery**
- Docker images for both Python services, published to Docker Hub (`loc109/web_backend`, `loc109/chatbot`)
- GitHub Actions: tests on every pull request; build, push, and deploy on every merge to `main`
- AWS CloudFormation across two stacks: a VPC/networking stack and an application stack
- Application Load Balancer with HTTPS (ACM) and path-based routing to the API and chatbot
- Auto Scaling group of EC2 servers that run the containers with Docker Compose and are replaced one at a time on each release
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

## Run it locally

You'll run up to three services, each in its own terminal: the API on port 8000, the chatbot on port 8001 (optional), and the frontend on port 5173.

### Prerequisites

- Python 3.12+ (Django 6 requires it)
- Node.js 20.19+ or 22.12+ (required by Vite 7)
- MySQL 8.x
- For the chatbot only: a Pinecone API key, plus an OpenRouter API key or a local Ollama model

### 1. Create the database

In a MySQL shell:

```sql
CREATE DATABASE the_restaurant;
```

### 2. Start the API (port 8000)

```bash
cd backend
python -m venv env
source env/bin/activate            # Windows: env\Scripts\activate
pip install -r requirements.txt    # requirements.txt is in backend/, not backend/restaurantAPI/
cd restaurantAPI
```

Create `backend/restaurantAPI/.env` (next to `manage.py`):

```dotenv
SECRET_KEY=any-long-random-string
STAGE=DEV
TAX=0.08
ALLOWED_ORIGINS=http://localhost:5173
DB_NAME=the_restaurant
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Then set up the tables and start the server:

```bash
python manage.py migrate
python manage.py shell < scripts.py    # optional: adds a sample menu
python manage.py runserver             # check http://127.0.0.1:8000/api/items/
```

### 3. Start the chatbot (port 8001, optional)

In a new terminal:

```bash
cd chatbot_backend
python -m venv env
source env/bin/activate            # Windows: env\Scripts\activate
pip install -r requirements.txt
```

Create `chatbot_backend/.env`:

```dotenv
# True = OpenRouter (cloud); anything else = local Ollama
CLOUD=True
OPENROUTER_MODEL=google/gemini-3-flash-preview
OPENROUTER_API_KEY=your-openrouter-key
PINECONE_API_KEY=your-pinecone-key
INDEX_NAME=your-pinecone-index
MODEL_CONTEXT=32000
MEMORY_LENGTH=70
DEBUG=False
DB_NAME=the_restaurant
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Then start it (it creates its own tables on startup):

```bash
python server.py
```

### 4. Start the frontend (port 5173)

In a new terminal:

```bash
cd frontend/restaurant
npm install
```

Create `frontend/restaurant/.env`. `VITE_BACKEND_URL` must **not** end with `/`:

```dotenv
VITE_BACKEND_URL=http://localhost:8000/api
VITE_CHATBOT_URL=ws://localhost:8001
VITE_DEBUG=true
```

Then start it and open http://localhost:5173:

```bash
npm run dev
```

Each service's README has more detail: [backend](backend/README.md), [chatbot](chatbot_backend/README.md), [frontend](frontend/restaurant/README.md).

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

> The tests need a running MySQL server, and the user in `.env` must be allowed to create a `test_<DB_NAME>` database. There is no SQLite fallback.

GitHub Actions also runs these tests on every pull request, against a temporary MySQL 8.4 container.

## CI/CD (GitHub Actions)

The workflow in [`.github/workflows/main_test_build_deploy.yaml`](.github/workflows/main_test_build_deploy.yaml) does the following:

| When | What happens |
|---|---|
| A pull request into `main` is opened or updated | Runs the Django tests. Nothing is built or deployed. |
| A commit lands on `main` (for example, you merge a PR) | Runs the tests. If they pass, it builds both Docker images tagged with the commit SHA, pushes them to Docker Hub, updates the AWS stacks to the new images, and builds and uploads the frontend. |
| You click **Run workflow** on `main` in the Actions tab | Same as a commit on `main`. |

Only one deploy runs at a time; a newer one waits for the current one to finish.

> **Tip:** in Settings → Branches, add a rule for `main` with **Require status checks to pass before merging** and select `Test`. Then a PR can't be merged until its tests pass.

The one-time setup (GitHub environment variables and secrets, AWS permissions) is in [deploy/README.md](deploy/README.md#option-a-automatic-deploys-with-github-actions).

## Deployment (AWS)

Everything runs on AWS, defined as code in `deploy/` as **two CloudFormation stacks**:

1. **VPC stack** (`vpc_dev.yaml`): VPC, public/private subnets across 2 AZs, Internet Gateway, and a NAT gateway.
2. **Application stack** (`backend_infra.yaml`): an HTTPS load balancer that sends `/api/*` to Django and `/chat*` to the chatbot, an Auto Scaling group of EC2 servers running both containers, RDS MySQL, and S3 + CloudFront for the frontend.

You can deploy automatically (merge to `main`) or manually with the scripts. **See [deploy/README.md](deploy/README.md)** for the one-time setup, both deploy options, updating and rolling back, and troubleshooting.

## License

No license specified yet.
