# jarvis_web

Projeto fullstack com **frontend (Vue 3 + Vite + Tailwind)** e **backend (FastAPI + SQLAlchemy + SQLite)**.

## Estrutura

```text
jarvis_web/
├── .env.example
├── backend/
│   ├── .env.example
│   ├── README.md
│   ├── requirements.txt
│   └── app/
└── frontend/
```

## Backend rápido (Debian/Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

cd jarvis_web/backend
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## SQLite: criação automática

Ao iniciar o backend, o sistema:

- cria automaticamente o caminho do banco SQLite;
- cria o arquivo do banco quando não existe;
- cria todas as tabelas SQLAlchemy;
- aplica seed inicial opcional quando `DATABASE_SEED_ENABLED=true` **somente se o banco estiver vazio**.

Local padrão do arquivo:

- `jarvis_web/backend/jarvis_web.db` (com `DATABASE_URL=sqlite:///./jarvis_web.db`)

Para detalhes, veja `jarvis_web/backend/README.md`.
