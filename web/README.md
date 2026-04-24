# AutoScholarLoop Web Console

This directory contains the Vue single-page console for launching and observing AUTO Research loops.

## Development

Start the Python API from the repository root:

```bash
pip install -e ".[web]"
uvicorn open_research_agent.web.server:app --reload
```

Start the Vue app:

```bash
cd web
npm install
npm run dev
```

The UI expects the API at `http://127.0.0.1:8000` by default. Override it with:

```bash
VITE_API_BASE=http://127.0.0.1:8000 npm run dev
```
