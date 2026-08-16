# SafeConnect — Community Network Security & Real-Time Emergency Response

SafeConnect is a high-fidelity, real-time community safety and emergency response web application. It enables users in distress to trigger instant emergency broadcasts, stream live GPS tracking updates over WebSockets to authorized community responders, view real-time interactive maps, receive Web Push notifications, and maintain connection-failure safety handling during offline scenarios.

---

## 1. Project Overview & Problem Solved

During personal emergencies, individuals need immediate, reliable assistance from nearby community members and trusted contacts. Traditional emergency apps suffer from complex setups, lack of real-time location visibility for responders, or broken offline handling.

SafeConnect solves this by providing:
- **One-Tap Emergency Broadcast**: Instantly alerts all active community members when help is needed.
- **Authorized Real-Time GPS Tracking**: Streams continuous location fixes over WebSockets exclusively to authorized responders and emergency owners.
- **Interactive Live Map**: Displays real-time location markers, accuracy radiuses, and movement trails.
- **Responder & Resolution Workflows**: Allows community members to offer help (`I CAN HELP`) and emergency owners to confirm safety (`REACHED SAFELY`).
- **Web Push & Offline Resilience**: Delivers Web Push notifications and buffers location updates in a local retry queue when offline.

---

## 2. Key Features

- 🛡️ **JWT Security & Authorization**: Strict IDOR isolation ensuring location data is accessible only to authorized emergency owners and responders.
- 🆘 **All-User Emergency Broadcast**: Creates in-app and Web Push alerts for community members without revealing private GPS coordinates in generic payloads.
- 📍 **Continuous Live Location**: Continuous GPS tracking via `navigator.geolocation.watchPosition()`.
- ⚡ **WebSocket Location Stream**: High-efficiency WebSocket room streaming (`emergency:<id>`).
- 🗺️ **Live Emergency Map**: Leaflet OpenStreetMap rendering with dynamic marker updates and stale location indicators (>2 mins).
- 🤝 **Responder Workflow**: `I CAN HELP` authorization flow granting responders live location access.
- 🏁 **Emergency Resolution**: `REACHED SAFELY` flow that terminates continuous GPS tracking, shuts down WebSocket rooms, and notifies community members of safe arrival.
- 🔔 **Web Push Notifications**: Standardized VAPID Web Push delivery and Service Worker handling (`sw.js`).
- 📶 **Offline & Connection Resilience**: `useOnlineStatus` hook, bounded local retry queue (max 10 items), and offline resolution retry.

---

## 3. Architecture & Technology Stack

```
   Emergency Owner Device                   Community Responders
 ┌───────────────────────────┐           ┌───────────────────────────┐
 │ React Frontend + PWA      │           │ React Frontend + PWA      │
 │  - watchPosition() GPS    │           │  - Leaflet Live Map       │
 │  - Bounded Retry Queue    │           │  - Socket.IO Client       │
 └─────────────┬─────────────┘           └─────────────▲─────────────┘
               │                                       │
     REST API / WebSocket                    WebSocket Location Stream
               │                                       │
 ┌─────────────▼───────────────────────────────────────┴─────────────┐
 │ Flask Backend (Python 3.13 + Flask-SocketIO + Gunicorn/Eventlet)  │
 │  - Authentication & JWT Middleware                                │
 │  - Security Headers & CORS Controls                               │
 │  - WebSocket Room Authorization (emergency:<id>)                  │
 └─────────────┬─────────────────────────────────────────────────────┘
               │
   ┌───────────┴───────────┐
   ▼                       ▼
SQLite / PostgreSQL    Web Push Service (VAPID)
(Persisted Storage)    (Browser Push Delivery)
```

- **Backend**: Python 3.13, Flask 3.0, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-SocketIO 5.6, PyWebPush 2.4, Gunicorn / Eventlet.
- **Frontend**: React 18, Vite 5, Leaflet / React-Leaflet, Socket.IO Client, Vanilla CSS design system.
- **Database**: SQLite (Development) / PostgreSQL (Production).

---

## 4. Repository Structure

```
SafeConnect/
├── backend/
│   ├── app/
│   │   ├── config/          # Environment settings & configuration
│   │   ├── middleware/      # Error handlers & security middleware
│   │   ├── models/          # SQLAlchemy ORM models (User, Emergency, Location, etc.)
│   │   ├── routes/          # API Blueprints (auth, emergency, location, response, etc.)
│   │   ├── services/        # Core business logic & Web Push service
│   │   ├── sockets.py       # Flask-SocketIO event handlers
│   │   └── extensions.py    # Database, JWT, CORS, SocketIO extensions
│   ├── tests/               # Pytest suite (86 automated test cases)
│   ├── wsgi.py              # Production WSGI startup entry point
│   ├── gunicorn_config.py   # Production Gunicorn configuration
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variable template
├── frontend/
│   ├── public/
│   │   └── sw.js            # Web Push Service Worker
│   ├── src/
│   │   ├── components/      # React components (Map, AuthLayout, Navigation, etc.)
│   │   ├── hooks/           # Custom hooks (useLocationTracking, useOnlineStatus, etc.)
│   │   ├── pages/           # Application pages (Dashboard, EmergencyDetails, Login, etc.)
│   │   └── services/        # Axios API client & Web Push service helper
│   └── package.json         # Dependencies & Vite build scripts
├── SECURITY_AUDIT.md        # Complete Security & Privacy Audit Report
├── PROJECT_STATUS.md        # Phase-by-phase completion report
└── README.md                # Main documentation
```

---

## 5. Local Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python run.py
```
Backend server runs at: `http://localhost:5000`

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Frontend development server runs at: `http://localhost:5173`

---

## 6. Environment Variables

### Backend (`backend/.env`)
| Variable | Description | Example / Default |
|----------|-------------|-------------------|
| `FLASK_ENV` | Environment mode | `development` / `production` |
| `SECRET_KEY` | Flask application secret key | `change-me-in-production` |
| `JWT_SECRET_KEY` | JWT signing key | `change-me-jwt-secret` |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///safeconnect.db` / `postgresql://user:pass@localhost:5432/safeconnect` |
| `FRONTEND_URL` | Primary allowed frontend origin | `http://localhost:5173` |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:5173,https://safeconnect.app` |
| `VAPID_PUBLIC_KEY` | Public key for Web Push VAPID authentication | `your-vapid-public-key` |
| `VAPID_PRIVATE_KEY` | Private key for Web Push VAPID signing | `your-vapid-private-key` |
| `VAPID_CLAIM_EMAIL` | Contact email for Web Push VAPID claims | `mailto:security@safeconnect.local` |

### Frontend (`frontend/.env`)
| Variable | Description | Example / Default |
|----------|-------------|-------------------|
| `VITE_API_URL` | Backend REST API base URL | `http://localhost:5000/api` |
| `VITE_SOCKET_URL` | WebSocket server URL | `http://localhost:5000` |
| `VITE_VAPID_PUBLIC_KEY` | Public VAPID key for Web Push registration | `your-vapid-public-key` |

---

## 7. Testing Suite

### Running Backend Pytest
```bash
cd backend
python -m pytest tests/ -q
```
*Result*: All **86 test cases pass** covering Phase 1 through Phase 11.

### Running Frontend Build Verification
```bash
cd frontend
npm run build
```
*Result*: Vite production build succeeds without errors.

---

## 8. Production Deployment & Configuration

For production deployment:
1. **WSGI Server**: Launch Flask + SocketIO using Gunicorn with Eventlet worker:
   ```bash
   gunicorn -c gunicorn_config.py wsgi:app
   ```
2. **Reverse Proxy (Nginx / Cloudflare)**:
   - Route `/api` and `/socket.io` to backend.
   - Enforce HTTPS and WSS (`wss://`).
   - Configure security headers at proxy or backend level.
3. **Database**: Use PostgreSQL via `DATABASE_URL=postgresql://user:password@db-host:5432/safeconnect`. Run `db.create_all()` or Flask-Migrate schema initialization.

---

## 9. Browser GPS Limitations Statement

> **Important Architecture Notice**:
> The React web application cannot guarantee continuous GPS tracking after the browser application or mobile operating system completely suspends or terminates the application process.
> 
> SafeConnect web application provides:
> - Active browser tab tracking.
> - Supported background/PWA behavior where allowed by browser permissions.
> - Network disconnection recovery and bounded retry queueing (max 10 position fixes).
> 
> Guaranteed OS-level background GPS tracking requires a native mobile application (e.g. React Native / Android / iOS).

---

## 10. Security Considerations

- **Strict IDOR Isolation**: All location API endpoints verify emergency ownership or active responder status.
- **WebSocket Room Authorization**: Users cannot eavesdrop on room channels (`emergency:<id>`) without valid JWT authentication and server-side verification.
- **Zero Sensitive Data in Push Payloads**: Web Push payloads contain alert metadata only (`url: "/emergency/<id>"`). Coordinates and tokens are never included.
- **Security Headers**: Standard response headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`) active on all responses.
