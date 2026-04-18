# Course Recommendation System

This project is a full-stack web application designed to recommend academic courses to students based on their previous academic history, personal workload preferences, and industry demands.

## Prerequisites
- **Docker & Docker Compose** (to run the PostgreSQL database)
- **Python 3.8+** (for the FastAPI backend)
- **Node.js & npm** (for the React/Vite frontend)

---

## 1. Start the Database
The project uses PostgreSQL running inside a Docker container.
1. Open a terminal in the root folder (`Course-Recommendation-System`).
2. Run the following command to start the database in the background:
   ```bash
   docker-compose up -d
   ```

---

## 2. Setup & Run the Backend (Server)
1. Open a new terminal and navigate to the `server` directory:
   ```bash
   cd server
   ```
2. *(Optional but recommended)* Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Seed the database with the initial Afeka courses, skills, and jobs:
   ```bash
   python seed.py
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```
   *The backend is now running at `http://localhost:8000`*

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
