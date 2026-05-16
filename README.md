# Course Recommendation System

This project is a full-stack web application designed to recommend academic courses to students based on their previous academic history, personal workload preferences, and industry demands.

## Prerequisites
- **Docker & Docker Compose** (to run the PostgreSQL database)
- **Python 3.8+** (for the FastAPI backend)
- **Node.js & npm** (for the React/Vite frontend)

---

## 1. Start the Database
The project uses PostgreSQL in Docker on **host port 5433** (container port 5432) to avoid conflicting with a local Postgres on 5432.

1. Open a terminal in the project root (`Course-Recommendation-System`).
2. **First time or after port/volume issues** — wipe and recreate containers + volumes:
   ```bash
   docker-reset.bat
   ```
   On Mac/Linux: `chmod +x docker-reset.sh && ./docker-reset.sh`

   Manual equivalent:
   ```bash
   docker compose down -v
   docker compose up -d
   ```

3. **pgAdmin** (optional): open [http://localhost:8080](http://localhost:8080) — login `admin@admin.com` / `admin`.  
   The server **course_db (Docker)** is pre-registered. When prompted for the DB password, use `password123`.  
   (pgAdmin uses hostname `db` and port **5432** on the Docker network, not 5433.)

---

## 2. Setup & Run the Backend
1. Open a new terminal and navigate to the `server` directory:
   ```bash
   cd server
   ```
2. Create the virtual environment and install dependencies:
   ```bash
   setup.bat
   ```
   On Mac/Linux:
   ```bash
   chmod +x setup.sh run_server.sh
   ./setup.sh
   ```
3. Copy environment variables:
   ```bash
   copy .env.example .env
   ```
   On Mac/Linux: `cp .env.example .env`  
   Edit `.env` and set your `ANTHROPIC_API_KEY`.
4. Seed the database (from the `server` directory, uses `server/.venv` and `server/.env`):
   ```bash
   seed.bat
   ```
   On Mac/Linux: `chmod +x seed.sh && ./seed.sh`

   Equivalent manual command:
   ```bash
   .venv\Scripts\python scripts\seed.py
   ```
   On Mac/Linux: `.venv/bin/python scripts/seed.py`
5. Start the server:
   ```bash
   run_server.bat
   ```
   On Mac/Linux: `./run_server.sh`

   *The backend runs at `http://localhost:8000` (API version: `/api/v1`)*

---

## 3. Setup & Run the Frontend (Client)
1. Open a new terminal and navigate to the `client` directory:
   ```bash
   cd client
   ```
2. Install the Node dependencies (if you haven't already):
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The frontend is now running at `http://localhost:5173`*

---

## Accessing the App
Once everything is running, open your browser and go to:
**[http://localhost:5173](http://localhost:5173)**

You will see the amazing glassmorphism authentication screen. You can create an account and log in!
