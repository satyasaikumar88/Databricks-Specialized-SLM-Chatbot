# Databricks-Specialized SLM Chatbot

A full-stack local Databricks assistant built with:

- Small Language Model: Qwen2.5-0.5B-Instruct
- Fine-tuning with LoRA
- Retrieval augmented generation using Databricks docs
- FastAPI backend
- Next.js + TypeScript chatbot UI
- Evaluation scripts for base vs fine-tuned vs fine-tuned + RAG

## Project structure

```text
databricks-slm/
├── data/
├── training/
├── rag/
├── model/
├── backend/
├── frontend/
├── evaluation/
├── tests/
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── README.md
└── .gitignore
```

## Quick start

### 1) Create a virtual environment

```bash
cd databricks-slm
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# or .venv\Scripts\activate  # Windows
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Prepare environment variables

```bash
cp .env.example .env
```

### 4) Build the Databricks dataset

```bash
python training/dataset_builder.py
```

### 5) Fine-tune the SLM with LoRA

```bash
python training/train_lora.py --model_name Qwen/Qwen2.5-0.5B-Instruct --dataset_path data/databricks_qa.jsonl --output_dir model/qwen2.5-0.5B-databricks-lora --epochs 1 --batch_size 2 --learning_rate 2e-4 --max_samples 200
```

### 6) Create the RAG document index

```bash
python rag/index_documents.py
```

### 7) Run API backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 8) Run frontend

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:3000 and ask questions like:

- What is Delta Lake?
- Explain Bronze, Silver and Gold architecture.
- Write PySpark code to create a Delta table.
- What is Unity Catalog?
- Why is my Spark job slow?

## API endpoints

- GET /health
- GET /model
- GET /documents
- POST /documents/index
- POST /chat

## Model notes

This project uses Qwen2.5-0.5B-Instruct; it is small enough to run locally on commodity hardware while still being compatible with LoRA-based fine-tuning. If you have a GPU, this will be much faster.

## Evaluation

```bash
python evaluation/evaluate.py
```

This compares:

- Base model
- Fine-tuned model
- Fine-tuned model + RAG

## Troubleshooting

- If the model download is slow, use a GPU-enabled environment or reduce the sequence length.
- If FAISS fails, reinstall `faiss-cpu` in the active Python environment.
- If the frontend cannot reach the API, set `NEXT_PUBLIC_API_URL` in the frontend environment.

## License

MIT
