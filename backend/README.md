# Backend — Restaurant REST API

A Django 6 + Django REST Framework API backing the restaurant ordering platform.
It serves the menu, categories, carts and orders, and provides a custom
JWT authentication flow (access token in the JSON body, refresh token in an
httpOnly cookie). MySQL is the datastore.

> Part of the [Restaurant full-stack project](../README.md). See the frontend
> (`frontend/restaurant`), the AI chatbot (`chatbot_backend`), and the
> infrastructure-as-code (`deploy`) for the other services.

## Tech stack

- **Django 6.0** + **Django REST Framework 3.16**
- **MySQL** — connected through the `pymysql` shim (`restaurantAPI/__init__.py`
  calls `pymysql.install_as_MySQLdb()`; do not remove that import)
- **djangorestframework-simplejwt** for JWT access/refresh tokens
- **django-environ** for `.env`-driven configuration
- **django-cors-headers** for cross-origin requests (credentials enabled)
- **gunicorn** (`gthread` workers) for production serving
- **djangorestframework-xml** content negotiation; `djoser` + simplejwt token
  endpoints are mounted but unused by the app

## Project layout

```
backend/
├── requirements.txt          # <-- deps live HERE, not in restaurantAPI/
├── setup.sh                  # EC2 provisioning script (venv, .env, migrate, systemd)
└── restaurantAPI/            # Django project root (contains manage.py)
    ├── manage.py
    ├── .env                  # not committed — create this (see Configuration)
    ├── .env_template_for_deploy
    ├── gunicorn.conf.py      # production gunicorn config (bind 0.0.0.0:8000)
    ├── scripts.py            # menu seed data (3 categories, 16 items)
    ├── restaurantAPI/        # settings, urls, wsgi/asgi, pymysql shim
    └── api/                  # models, serializers, views, urls, tests
```

## Getting started

> **Footgun:** `requirements.txt` is in `backend/`, **not** `backend/restaurantAPI/`.

```bash
# 1. Install dependencies (from backend/)
cd backend
pip install -r requirements.txt

# 2. Create backend/restaurantAPI/.env (see Configuration below)

# 3. From backend/restaurantAPI/, run migrations and the dev server
cd restaurantAPI
python manage.py migrate
python manage.py runserver            # http://127.0.0.1:8000

# 4. (optional) seed the menu — 3 categories + 16 items
python manage.py shell < scripts.py
```

Production server:

```bash
gunicorn restaurantAPI.wsgi:application -c gunicorn.conf.py   # binds 0.0.0.0:8000
```

## Configuration

All configuration is read from `backend/restaurantAPI/.env` (next to
`manage.py`) at **import time** — a missing required variable breaks startup.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `STAGE` | `DEV` / `PRE_PROD` / `PROD`. Drives everything below |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | MySQL connection |
| `TAX` | Tax rate as a `Decimal` (e.g. `0.1`) — applied to prices and orders |
| `ALLOWED_ORIGINS` | Comma-separated CORS/allowed origins (read in `api/views.py` at import) |
| `ALLOWED_HOSTS` | Only required when `STAGE=PROD` |

`STAGE` behavior:

- `DEBUG = (STAGE != "PROD")`
- Only `PROD` reads `ALLOWED_HOSTS` from env, enables env-driven CORS origins,
  sets `SECURE_PROXY_SSL_HEADER`, and turns on gunicorn keepalive tuning
  (see `gunicorn.conf.py`). Otherwise `ALLOWED_HOSTS=['*']` and all CORS origins
  are allowed.

## Data model (`api/models.py`)

- **Category** — `title` (unique), `slug`
- **MenuItem** — `title`, `price`, `stock`, `featured`, `description`,
  `category` (FK, `PROTECT`), `image_paths`
- **CartItem** — `user`, `menuitem`, `quantity`; unique per `(user, menuitem)`
- **Order** — `user`, `status`, `total_price_after_tax`, `datetime`, and the
  customer contact/shipping fields (`first_name`, `last_name`, `email`,
  `phone_number`, `address`)
- **OrderItem** — `order`, `menuitem`, `quantity`; unique per `(order, menuitem)`

## API

Routes are registered by a DRF `DefaultRouter` in `api/urls.py`, mounted under
`/api/`, plus manual auth and user routes.

| Endpoint | Method(s) | Auth | Notes |
|---|---|---|---|
| `/api/auth/signup/` | POST | anon | Create a user (password validated) |
| `/api/auth/login/` | POST | anon | Returns `{access_token, user}`; sets `refresh_token` cookie |
| `/api/auth/refresh/` | POST | cookie | Rotates access token + refresh cookie |
| `/api/auth/logout/` | POST | cookie | Clears cookie, attempts to blacklist token |
| `/api/users/<pk or "me">/` | GET | JWT | `me` = self; other ids need `auth.view_user` |
| `/api/items/` | GET / POST / PUT / PATCH / DELETE | anon read; model perms to write | Menu items |
| `/api/categories/` | GET / POST / PUT / PATCH / DELETE | anon read; model perms to write | Categories |
| `/api/carts/` | GET / POST / PATCH / DELETE | JWT | Current user's cart (admins with perms see all) |
| `/api/orders/` | GET / POST / PATCH | JWT | Place / list / update orders |

### Authentication flow

Custom, hand-rolled JWT (not `djoser`):

- **Login** returns the access token in the JSON body and sets the **refresh
  token as an httpOnly, `Secure`, `SameSite=None` cookie** (`refresh_token`,
  path `/api/auth/`, 7-day max-age).
- **Refresh** reads that cookie, rotates a new access token and cookie
  (`ROTATE_REFRESH_TOKENS=True`). Access-token lifetime is 5 minutes; refresh
  lifetime is 1 day.
- The frontend keeps the access token in memory only and calls every endpoint
  with `credentials: "include"` so the cookie rides along.

### Permissions & order lifecycle

- Menu/Category viewsets: `DjangoModelPermissionsOrAnonReadOnly` (anonymous read,
  Django model permissions to write).
- Cart/Order viewsets: `IsAuthenticated`; ownership is enforced in
  `get_queryset` (users see only their own rows; admins with the relevant model
  permission see all).
- Order status lifecycle: `processing → preparing → shipping → completed`
  (or `canceled`). A regular customer may only `PATCH` `status` to `canceled`;
  staff with `api.change_order` can change anything.
- Order placement (`OrderView.create`) reads the user's cart, applies `TAX`,
  and writes the `Order` + `OrderItem`s inside `transaction.atomic()`, then
  deletes the cart. **Stock is not decremented.**

Default throttle rates are configured (`anon` 2/min, `user` 5/min).

## Testing

```bash
cd backend/restaurantAPI
python manage.py test                                 # full suite
python manage.py test api.tests.CartViewTests         # one class
python manage.py test api.tests.CartViewTests.test_create_sets_user_and_computes_totals
```

The suite (`api/tests.py`) covers signup validation, menu/category permission
gating, and cart ownership/total computation
(`SignUpViewTests`, `MenuItemViewCorrectedBehaviorTests`, `CategoryApiTests`,
`CartViewTests`).

> **Tests require a live MySQL server** with privileges to create a
> `test_<DB_NAME>` database. There is no SQLite/test-settings fallback.

## Known limitations

- **Refresh-token blacklisting is a silent no-op.** `token_blacklist` is not in
  `INSTALLED_APPS`, so `RefreshToken.blacklist()` raises and is swallowed;
  logged-out/rotated refresh tokens stay valid until they expire. Add
  `rest_framework_simplejwt.token_blacklist` to `INSTALLED_APPS` and migrate to
  enable it.
- `scripts.py` is intended for seeding empty tables (it skips rows whose
  `title` already exists, but is not otherwise idempotent for edits).
- `djoser` and the simplejwt `TokenObtainPair`/`TokenRefresh` endpoints are
  mounted in `restaurantAPI/urls.py` but are not used by the frontend.
