# Nova-AI

A production-grade AI platform combining conversational AI, document intelligence, and real-time collaboration — built as a full-stack monorepo.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4, Zustand, Framer Motion |
| **Backend** | Node.js, Express 5, MongoDB (Mongoose), Socket.io, JWT |
| **AI Service** | Python, FastAPI, OpenAI API, Gemini API, Uvicorn |

---

## Project Structure

```
Nova-AI/
├── frontend/        # Next.js app (UI)
├── backend/         # Node.js + Express REST API
├── ai/              # Python FastAPI AI microservice
├── database/        # DB schema & models
└── README.md
```

---

## Prerequisites

Make sure you have the following installed:

- [Node.js](https://nodejs.org/) v18+
- [Python](https://www.python.org/) 3.10+
- [Git](https://git-scm.com/)

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Nova-AI.git
cd Nova-AI
```

### 2. Set up environment variables

Each service has its own `.env` file. Copy the examples and fill in your keys:

```bash
# AI service
cp ai/.env.example ai/.env
```

**`ai/.env`**
```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
```

**`backend/.env`** *(create manually)*
```env
PORT=5000
MONGODB_URI=mongodb+srv://...
JWT_SECRET=your_jwt_secret
```

**`frontend/.env.local`** *(create manually)*
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_AI_URL=http://localhost:8000
```

---

### 3. Run the AI Service

```bash
cd ai
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

> AI service runs at `http://localhost:8000`

---

### 4. Run the Backend

```bash
cd backend
npm install
npm run dev
```

> Backend runs at `http://localhost:5000`

---

### 5. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

> Frontend runs at `http://localhost:3000`

---

## Features

- **AI Chat** — Streaming chat completions via OpenAI / Gemini
- **Document Intelligence** — RAG-based PDF Q&A using embeddings
- **Computer Vision** — Image upload, analysis & OCR
- **Voice AI** — Whisper speech-to-text integration
- **Code Assistant** — Syntax highlighting & bug detection
- **Semantic Search** — Vector database powered search
- **Real-time Collaboration** — Live cursors & comments via WebSockets

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/chat` | AI chat completion |
| `POST` | `/api/auth/login` | User login |
| `POST` | `/api/auth/register` | User registration |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is licensed under the [MIT License](LICENSE).
