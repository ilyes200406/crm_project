# Insomea CRM Frontend

Feature-based React frontend aligned with your current DRF backend (`authentication` + `users`).

## Stack
- React + Vite
- React Router
- Zustand
- TanStack Query
- Axios
- React Hook Form

## Run
```bash
npm install
npm run dev
```

## Build
```bash
npm run build
```

## Environment
Copy `.env.example` to `.env.development` and adjust values:

- `VITE_API_BASE_URL` (default: `http://localhost:8000/api`)
- `VITE_APP_NAME`

## Implemented Scope
- Auth flow: login, setup, forgot/reset password, logout, token refresh
- User flow: me/profile update, admin create user, list users, activate/deactivate, user stats
- Role-protected routes for admin user management

## Architecture
```text
src/
  app/
    router.jsx
    providers.jsx
    store.js
  features/
    auth/
    users/
    clients/
    catalogue/
    ventes/
    notifications/
  shared/
    components/
    hooks/
    utils/
  services/
    axios.js
    queryClient.js
  layouts/
    DashboardLayout.jsx
    AuthLayout.jsx
  routes/
    ProtectedRoute.jsx
```

Each feature includes `api/`, `hooks/`, `components/`, and `pages/`.
