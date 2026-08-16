# SafeConnect React Frontend Production Deployment Guide (Phase 13B)

This document provides production deployment instructions, environment variable configuration, SPA fallback routing rules, and security guidelines for the **SafeConnect React Frontend**.

---

## 1. Build Overview & Requirements

- **Framework**: React 18 / Vite 5
- **Build Tool**: Vite (`npm run build`)
- **Output Directory**: `frontend/dist`
- **Protocol Requirements**: HTTPS & WSS (Secure WebSockets)
- **Service Worker**: `public/sw.js` (Web Push Notifications)

---

## 2. Environment Variables (.env / Hosting Dashboard)

Configure environment variables in your hosting provider dashboard (e.g. Vercel, Netlify, Cloudflare Pages, AWS Amplify):

```ini
# Production Backend REST API URL (Must use HTTPS)
VITE_API_URL=https://api.safeconnect.example.com/api

# Production WebSocket Endpoint (Must use WSS or HTTPS)
VITE_SOCKET_URL=https://api.safeconnect.example.com
VITE_WS_URL=wss://api.safeconnect.example.com

# Web Push Notification VAPID Public Key (Safe for client exposure)
VITE_VAPID_PUBLIC_KEY=your_vapid_public_key_string
```

> **Security Rule**: `VITE_*` variables are bundled into client-side JavaScript. **NEVER** expose database credentials, JWT secrets, or VAPID private keys in frontend environment variables.

---

## 3. Build & Test Commands

From the `frontend` folder:

```bash
# 1. Install dependencies
npm install

# 2. Production Build
npm run build

# 3. Preview Production Build Locally
npm run preview
```

Output static files will be generated in `frontend/dist/`.

---

## 4. SPA Fallback Routing Configuration

Because SafeConnect is a Single Page Application (React Router v6), direct navigation to deep links (e.g. `https://safeconnect.example.com/emergency/123` or `/dashboard`) must route to `index.html`.

### Option A: Vercel (`vercel.json`)
Create `vercel.json` in root or `frontend/` directory:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### Option B: Nginx Static Server
```nginx
server {
    listen 443 ssl http2;
    server_name safeconnect.example.com;

    root /var/www/safeconnect-frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 5. Web Push Notification & Service Worker

- The Service Worker is automatically copied from `public/sw.js` to `dist/sw.js` during Vite build.
- Browser notifications require HTTPS context.
- Service worker handles `push` and `notificationclick` events without storing authorization secrets in client code.

---

## 6. HTTPS & Geolocation Security

Browser HTML5 `navigator.geolocation.watchPosition` requires a **secure context (HTTPS)**.
If accessed over unencrypted `http://`, browsers will deny geolocation permission.

---

## 7. Deployment Steps (e.g., Vercel / Netlify / Static Host)

1. Connect Git repository to hosting provider.
2. Set Root Directory to `frontend`.
3. Set Build Command to `npm run build`.
4. Set Output Directory to `dist`.
5. Add Environment Variables (`VITE_API_URL`, `VITE_SOCKET_URL`, `VITE_VAPID_PUBLIC_KEY`).
6. Deploy application.

---

## 8. Rollback Procedure

1. Navigate to hosting provider deployment history.
2. Select previous stable deployment build artifact.
3. Promote previous build to Production.
4. Verify `/api/health` connectivity and WebSocket status.
