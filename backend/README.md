# ViTIP Backend – FastAPI

AI backend for the **Vietnamese Traditional Instrument Preservation** system.  
Frontend: [vietnamese-traditional-instrument-a.vercel.app](https://vietnamese-traditional-instrument-a.vercel.app)

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/health` | Health check |
| `GET`  | `/api/instruments/` | List all instruments |
| `POST` | `/api/detect/image` | YOLO + LeNet image detection |
| `GET`  | `/api/ontology/{class_name}` | Ontology info for an instrument |
| `POST` | `/api/chatbot/rag` | RAG chatbot (FAISS + OpenAI) |
| `POST` | `/api/video/detect` | Video detection + music description |
| `GET`  | `/docs` | Swagger UI |

---

## Project Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI app + CORS + router registration
│   ├── core/
│   │   ├── config.py         # Settings (pydantic-settings, reads .env)
│   │   ├── lifespan.py       # Startup model loading (YOLO, LeNet, Ontology, RAG)
│   │   ├── database.py       # MongoDB client
│   │   └── logging.py        # Logging setup
│   ├── api/routes/
│   │   ├── instruments.py    # GET /api/instruments/
│   │   ├── detection.py      # POST /api/detect/image
│   │   ├── ontology.py       # GET /api/ontology/{class_name}
│   │   ├── rag.py            # POST /api/chatbot/rag
│   │   └── video.py          # POST /api/video/detect
│   ├── services/
│   │   ├── ml.py             # LeNet builder + shared ML utilities
│   │   ├── detection.py      # Image detection logic
│   │   ├── ontology.py       # OWL ontology queries
│   │   ├── video.py          # Video processing + audio merge + LLM description
│   │   └── video_db.py       # MongoDB persistence + similarity search
│   └── schemas/
│       └── schemas.py        # Pydantic request/response models
├── tests/
│   └── test_api.py
├── nginx/
│   └── nginx.conf
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Local Development

```bash
# 1. Clone and enter directory
cd backend

# 2. Create virtual environment
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment
cp .env.example .env
# Edit .env: set OPENAI_API_KEY, etc.

# 5. Put model files in place
#    models/model_yolo/best.pt
#    models/model_lenet/lenet5_model_300.h5
#    models/ontology/nhaccu.owl
#    models/RAG/vectorstores/db_faiss_pdf/

# 6. Run
uvicorn app.main:app --reload --port 8000
```

---

## VPS Deployment with Docker

```bash
# 1. Copy project to VPS
scp -r backend/ user@your-vps:/opt/vitip/

# 2. SSH into VPS
ssh user@your-vps
cd /opt/vitip/backend

# 3. Copy model files
#    Place your model files under ./models/ (see .env.example for paths)

# 4. Configure environment
cp .env.example .env
nano .env   # Set OPENAI_API_KEY, CORS_ORIGINS, SECRET_KEY

# 5. Build and start
docker compose up -d --build

# 6. View logs
docker compose logs -f api
```

The API will be available at `http://your-vps-ip/api/`.  
Swagger docs at `http://your-vps-ip/docs`.

### SSL / HTTPS (recommended)

Install Certbot on the VPS and mount certificates into the nginx container:
```bash
certbot certonly --standalone -d yourdomain.com
# Then uncomment the SSL cert volume in docker-compose.yml
```

---

## Model Files Layout

```
models/
├── model_yolo/
│   └── best.pt
├── model_lenet/
│   └── lenet5_model_300.h5
├── ontology/
│   └── nhaccu.owl
└── RAG/
    └── vectorstores/
        └── db_faiss_pdf/
```

Place the `models/` directory next to `docker-compose.yml`.  
It is mounted read-only into the container via the volume in `docker-compose.yml`.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | – | Required for RAG and music description |
| `MONGODB_URI` | `mongodb://mongo:27017/` | MongoDB connection string |
| `CORS_ORIGINS` | `[...]` | JSON array of allowed origins |
| `LLM_MODEL` | `gpt-3.5-turbo` | OpenAI model for RAG + description |
| `EMBEDDING_MODEL_NAME` | `BAAI/bge-m3` | HuggingFace embedding model |
| `DEBUG` | `false` | Enable FastAPI debug mode |

---

## Running Tests

```bash
pip install pytest httpx
pytest tests/ -v
```
