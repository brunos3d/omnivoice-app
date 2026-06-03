# Dev Profile for Docker Compose

## Goal

Add a `dev` Docker Compose profile and `scripts/start-dev.sh` helper that lets developers run the backend stack in Docker while running the frontend locally via `npm run dev` (for Fast Refresh). Production behavior (`docker compose up -d`) must remain unchanged.

## Design

### Problem

Docker Compose profiles are additive (include-only). There is no "exclude this service" mechanism. Since `frontend` must start with `docker compose up -d` (no flags), it cannot have a profile — but then profiles can't exclude it.

### Solution

Put ALL services behind named profiles and activate a default profile via the `COMPOSE_PROFILES` environment variable in `.env` (which Docker Compose reads automatically).

### Changes

#### `docker-compose.yml`

Add `profiles` to each service:

| Service   | Profiles                  | Rationale                             |
|-----------|---------------------------|---------------------------------------|
| `backend` | `["production", "dev"]`   | Always needed in both modes           |
| `minio`   | `["production", "dev"]`   | Always needed in both modes           |
| `frontend`| `["production"]`          | Only in production; excluded from dev |

No other fields change.

#### `.env` (gitignored) and `.env.example` (tracked)

Add one line:

```env
COMPOSE_PROFILES=production
```

This makes `docker compose up -d` activate the `production` profile, starting all three services — identical to today's behavior.

#### `scripts/start-dev.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  echo "Shutting down..."
  docker compose down
  exit 0
}
trap cleanup EXIT INT TERM

echo "Starting dev infrastructure..."
COMPOSE_PROFILES=dev docker compose up -d

echo "Waiting for backend to be ready..."
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
  sleep 1
done

echo "Starting frontend dev server..."
cd frontend && npm run dev
```

- `COMPOSE_PROFILES=dev` overrides the `.env` default, activating only the `dev` profile → backend + minio start, frontend is excluded.
- Waits for the backend health endpoint before starting the frontend.
- Trap handles cleanup: `docker compose down` stops containers on exit/Ctrl+C.

### Behavior Summary

| Command                                   | Frontend | Backend | Minio |
|-------------------------------------------|----------|---------|-------|
| `docker compose up -d`                    | ✓        | ✓       | ✓     |
| `COMPOSE_PROFILES=dev docker compose up -d` | ✗      | ✓       | ✓     |
| `./scripts/start-dev.sh`                  | npm run  | ✓       | ✓     |

### Non-goals

- No `docker-compose.dev.yml` or second compose file.
- No duplicate Dockerfiles.
- No alternative deployment paths.

### Acceptance Criteria

- [ ] `docker compose up -d` starts all three services (unchanged from today).
- [ ] `./scripts/start-dev.sh` starts backend + minio in Docker and frontend via `npm run dev`.
- [ ] Fast Refresh works (frontend runs locally).
- [ ] Ctrl+C in `start-dev.sh` stops both the frontend dev server and Docker containers.
- [ ] Only one `docker-compose.yml` exists.
