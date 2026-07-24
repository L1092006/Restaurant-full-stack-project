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
└── frontend/restaurant/      # React + Vite SPA
    └── src/
        ├── contexts/          # Auth, Cart, Chatbot state
        ├── pages/              # Route-level pages
        └── components/        # Reusable UI (Chakra UI-based)
```

## Tech Stack

**Backend (API)**
- Django 6 + Django REST Framework
- MySQL (via `mysqlclient`)
- JWT authentication (`djangorestframework-simplejwt`) with refresh-token blacklisting
- `django-environ` for environment-based configuration
- `django-cors-headers` for cross-origin requests

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
- Python 3.11+
- Node.js 18+
- MySQL server
- (Optional, for the chatbot) Pinecone API key and an OpenRouter/OpenAI API key, or a local Ollama model

### Backend setup
```bash
cd backend/restaurantAPI
pip install -r requirements.txt

# Create a .env file with at least:
#   ALLOWED_ORIGINS=http://localhost:5173
#   TAX=0.08
#   (plus your Django SECRET_KEY and MySQL credentials)

python manage.py migrate
python manage.py runserver
```

### Frontend setup
```bash
cd frontend/restaurant
npm install

# Create a .env file with:
#   VITE_BACKEND_URL=http://localhost:8000/api

npm run dev
```

### Chatbot service setup
```bash
cd chatbot_backend
pip install -r requirements.txt

# Create a .env file with:
#   OPENROUTER_MODEL=<model name>
#   OPENROUTER_API_KEY=<key>
#   PINECONE_API_KEY=<key>
#   INDEX_NAME=<pinecone index name>
#   MODEL_CONTEXT=<context window size>
#   MEMORY_LENGTH=<max words per memory chunk>

python server.py
```

## API Overview

| Endpoint | Description |
|---|---|
| `POST /api/auth/signup/` | Create a new user account |
| `POST /api/auth/login/` | Authenticate, returns access token + sets refresh cookie |
| `POST /api/auth/refresh/` | Rotate access token using the refresh cookie |
| `POST /api/auth/logout/` | Blacklist refresh token and clear cookie |
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

## License

No license specified yet.
