
# Playground: Text-to-Manim

Turn a text prompt into a Manim animation video using LLM codegen.

---

## Quickstart (Local)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (for full parity with production)

### 1. Backend (FastAPI + Manim)

```bash
cd services
cd ..
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
# Set your Groq API key (recommended: use a .env file or environment manager):
# Create a .env file in the project root with:
#   GROQ_API_KEY=sk-...
uvicorn services.api.main:app --reload
```

### 2. Frontend (Vite + React)

```bash
cd frontend
cp .env.example .env
# Edit VITE_API_BASE_URL in .env if backend is remote
npm install
npm run dev
```

---

## Deploy to Render (Backend)
1. Push your repo to GitHub.
2. Go to [render.com](https://render.com), create a new Web Service, connect your repo.
3. Render will auto-detect `render.yaml` and build with Docker.
4. Set the `GROQ_API_KEY` environment variable in Render dashboard.
5. Deploy. Copy the backend URL (e.g., `https://playground-xxxx.onrender.com`).

## Deploy to Vercel (Frontend)
1. Import your repo in [vercel.com](https://vercel.com/new).
2. Set **Root Directory** to `frontend`.
3. Set build command: `npm run build`, output: `dist`.
4. Add env var: `VITE_API_BASE_URL` = your Render backend URL.
5. Deploy.

---

## Example Datasets for Finetuning

- https://huggingface.co/datasets/thanhkt/manim_code
- https://huggingface.co/datasets/generaleoley/manim-codegen

---

## Troubleshooting
- If the backend fails to render, check logs for LLM or Manim errors.
- If the frontend can’t reach the backend, check CORS and VITE_API_BASE_URL.
- For DNS issues, verify CNAME and Vercel domain status.

---

## Credits
- Built with FastAPI, Manim, React, Vite, Groq (provider), Qwen3-32B (model).
- See [frontend/README.md](frontend/README.md) for React/Vite details.