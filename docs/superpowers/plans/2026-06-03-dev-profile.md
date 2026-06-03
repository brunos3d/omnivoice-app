# Dev Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Docker Compose `dev` profile and `scripts/start-dev.sh` for local development with Fast Refresh.

**Architecture:** All three services (`frontend`, `backend`, `minio`) get `profiles` entries in `docker-compose.yml`. A default `COMPOSE_PROFILES=production` in `.env` preserves existing `docker compose up -d` behavior. The dev script overrides to `COMPOSE_PROFILES=dev` to exclude the frontend container and runs it locally.

**Tech Stack:** Docker Compose profiles, bash (start script)

---

### Task 1: Add `profiles` to all services in `docker-compose.yml`

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add `profiles` to each service**

Edit `docker-compose.yml` to add `profiles: ["production", "dev"]` to `backend`, `profiles: ["production", "dev"]` to `minio`, and `profiles: ["production"]` to `frontend`. No other fields change.

Resulting diff:

```yaml
 services:
   backend:
     build:
       context: ./backend
       dockerfile: Dockerfile
+    profiles: ["production", "dev"]
     ports:
       - "8000:8000"
       ...
 
   minio:
     image: minio/minio:latest
+    profiles: ["production", "dev"]
     command: server /data --console-address ":9001"
       ...
 
   frontend:
     build:
       context: ./frontend
       dockerfile: Dockerfile
+    profiles: ["production"]
     ports:
       - "3000:3000"
```

Place `profiles` right after the `build` block (for `frontend`) or `image` block (for `minio`) — first real config field in each service block for consistency.

- [ ] **Step 2: Verify the YAML is valid**

Run: `docker compose config` (should output merged config with no errors)

- [ ] **Step 3: Commit**

```bash
git add -p docker-compose.yml
git commit -m "feat: add production/dev profiles to all docker services"
```

---

### Task 2: Add `COMPOSE_PROFILES=production` to `.env` and `.env.example`

**Files:**
- Modify: `.env`
- Modify: `.env.example`

- [ ] **Step 1: Append `COMPOSE_PROFILES=production` to `.env`**

Add to end of `.env`:

```
COMPOSE_PROFILES=production
```

- [ ] **Step 2: Append `COMPOSE_PROFILES=production` to `.env.example`**

Same line at end of `.env.example`.

- [ ] **Step 3: Commit**

```bash
git add -p .env .env.example
git commit -m "feat: add COMPOSE_PROFILES default to .env and .env.example"
```

---

### Task 3: Create `scripts/start-dev.sh`

**Files:**
- Create: `scripts/start-dev.sh`

- [ ] **Step 1: Create the script**

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

cleanup() {
  echo ""
  echo "Shutting down development environment..."
  docker compose down
  echo "Done."
}
trap cleanup EXIT INT TERM

echo "Starting dev infrastructure (backend + minio)..."
COMPOSE_PROFILES=dev docker compose up -d

echo "Waiting for backend to be ready..."
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
  sleep 1
done
echo "Backend is ready."

echo "Starting frontend dev server..."
cd frontend && npm run dev
```

- [ ] **Step 2: Make the script executable**

Run: `chmod +x scripts/start-dev.sh`

- [ ] **Step 3: Verify syntax is valid bash**

Run: `bash -n scripts/start-dev.sh` (should exit 0 with no output)

- [ ] **Step 4: Commit**

```bash
git add scripts/start-dev.sh
git commit -m "feat: add start-dev.sh helper for local development"
```

---

### Task 4: Verify acceptance criteria

- [ ] **Step 1: Verify `docker compose config` shows correct profile assignments**

Run: `docker compose config`

Expected output shows all three services with their correct profiles.

- [ ] **Step 2: Verify `docker compose up -d` starts all services (production)**

Run: `docker compose up -d`
Expected: all three containers start.
Run: `docker compose ps`
Expected: `frontend`, `backend`, `minio` all running.

- [ ] **Step 3: Verify `COMPOSE_PROFILES=dev docker compose up -d` excludes frontend**

Run: `COMPOSE_PROFILES=dev docker compose up -d`
Run: `docker compose ps`
Expected: `backend` and `minio` running, `frontend` absent.

```bash
docker compose down
```
