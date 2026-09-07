# Frontend — Restaurant SPA

A React 18 + Vite single-page app for the restaurant ordering platform. Customers
browse the menu, manage a cart, place and track orders, and chat with an AI
assistant that can drive the app on their behalf. Built with Chakra UI v3.

> Part of the [Restaurant full-stack project](../../README.md). Talks to the
> Django API (`backend/`) over REST and to the AI agent (`chatbot_backend/`)
> over a WebSocket.

## Tech stack

- **React 18** + **Vite 7** (dev server, HMR, `dist/` build)
- **Chakra UI v3** with `next-themes` color mode (see `src/components/ui/`)
- **React Router v7** (`react-router-dom`)
- **React Hook Form** + **Zod** for form state and validation
- **@ryaneewx/react-chat-widget** for the chat UI
- **Context API** for auth, cart and chatbot state (no Redux)
- **ESLint 9** (flat config in `eslint.config.js`)

## Getting started

```bash
cd frontend/restaurant
npm install

# Create frontend/restaurant/.env (see Configuration)

npm run dev        # Vite dev server on http://localhost:5173
npm run build      # production build -> dist/
npm run preview    # preview the built app
npm run lint       # eslint .
```

There is no test runner configured for the frontend.

## Configuration

Client env vars must be prefixed `VITE_` and are read via `import.meta.env`.
Create `frontend/restaurant/.env`:

| Variable | Purpose |
|---|---|
| `VITE_BACKEND_URL` | REST API base URL, e.g. `http://localhost:8000/api` |
| `VITE_CHATBOT_URL` | Chatbot WebSocket URL, e.g. `ws://localhost:8001` |
| `VITE_DEBUG` | `"true"` to enable console debug logging |

> **Footgun:** `VITE_BACKEND_URL` **must not end in a slash.** Requests are built
> as `` `${VITE_BACKEND_URL}${path}` `` and every `path` already starts with `/`,
> so a trailing slash yields `//` and 404s.

## Project structure

```
src/
├── main.jsx              # entry — provider tree (order matters, see below)
├── App.jsx              # routes + persistent <Toaster/> and <ChatWidget/>
├── contexts/
│   ├── AuthContext.jsx      # auth + the real data layer (callAPI)
│   ├── CartContext.jsx      # cart state and mutations
│   └── ChatbotContext.jsx   # WebSocket + in-browser tool execution
├── pages/               # route-level pages (Home, Menu, Cart, Checkout, ...)
├── components/          # Navbar, Footer, Layout, ChatWidget, ui/ (Chakra wrappers)
└── utils/               # see the note below — do not use these
```

### Provider order is load-bearing

`main.jsx` nests providers as
`ChakraProvider → BrowserRouter → AuthProvider → CartProvider → ChatbotProvider → App`.
Cart depends on Auth; Chatbot depends on both; all three need the Router. `App.jsx`
wraps every route in a single `<Layout>` parent route and renders `<Toaster/>` and
`<ChatWidget/>` outside `<Routes>` so they persist across pages.

### Routes

`/`, `/login`, `/signup`, `/menu`, `/menu/:id`, `/cart`, `/checkout`,
`/account`, `/account/orders`, `/account/orders/:id`, `/contact`, `/about`.

## Key concepts

### Auth & the data layer (`AuthContext.jsx`)

`AuthContext.callAPI(path, { options, auth })` is the real data layer used by the
rest of the app:

- Prefixes `VITE_BACKEND_URL`, adds `Authorization: Bearer` when `auth: true`,
  and always sends `credentials: "include"` so the refresh cookie rides along.
- The **access token is kept in memory only** (`useState` + a `useRef` so
  `callAPI` reads it synchronously). On mount it silently restores the session
  via `/auth/refresh/` → `/users/me/`.
- On a non-ok authenticated response it performs a **single-flight** token
  refresh (one in-flight refresh shared across concurrent calls) and retries the
  request once; if refresh fails it logs the user out and redirects to `/login`.

### Cart (`CartContext.jsx`)

`addItem(menuitem_id, amount)` reloads the cart, then PATCHes/DELETEs an existing
line or POSTs a new one (negative amounts subtract; reaching zero deletes the
line). Concurrent adds for the same item are de-duplicated with a `useRef(Set)`,
and stock overruns surface as errors. `cartNumber` is derived from `cartItems`.

### The AI assistant acts inside your browser (`ChatbotContext.jsx`)

The chatbot's tools do **not** run server-side. The context opens a WebSocket to
`VITE_CHATBOT_URL`, and when the server sends a `tool_call` message the browser
executes it against the live app and replies with a `tool_result`:

- `navigate` — React Router `navigate()`, validated against the known route
  patterns with `matchPath`
- `get_items` — fetches categories + items via `callAPI`, grouped by category
- `add_item` — calls `CartContext.addItem`
- `get_cartitems` / `get_orders` — reads current cart / fetches orders

On connect the client sends a `status_update` (user id/username, current URL, and
a `paths_schema` describing the routes the agent may navigate to). The socket
auto-reconnects up to a fixed number of attempts.

## Note: ignore `src/utils/`

`src/utils/callAPI.js` is a **mock** that returns fixtures from `mockData/`, and
`src/utils/baseCallAPI.js` is dead, non-compiling code. The live data layer is
`AuthContext.callAPI` — use that.

## Deployment

The built `dist/` is uploaded to S3 and served through CloudFront (see
`deploy/`). Build and sync:

```bash
npm run build
aws s3 sync dist/ s3://<frontend-bucket> --delete
aws cloudfront create-invalidation --distribution-id <id> --paths "/*"
```
