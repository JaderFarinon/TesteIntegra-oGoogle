# Jarvis Web Backend (FastAPI + SQLite)

## Onde o SQLite é salvo

Por padrão, a aplicação usa:

- `DATABASE_URL=sqlite:///./jarvis_web.db`

Como essa URL é relativa, o arquivo final fica em:

- `jarvis_web/backend/jarvis_web.db` (quando você executa o backend dentro de `jarvis_web/backend`)

Você pode alterar o local editando a variável `DATABASE_URL` no `.env`.

## Inicialização automática do banco

Ao subir o backend, a API:

1. cria automaticamente a pasta do banco (se necessário);
2. cria o arquivo SQLite (se não existir);
3. cria todas as tabelas mapeadas no SQLAlchemy;
4. aplica seed inicial opcional (`DATABASE_SEED_ENABLED=true`) **apenas se o banco estiver vazio**.

## Rodando localmente (Debian/Ubuntu)

### 1) Pré-requisitos

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 2) Criar e ativar venv

```bash
cd jarvis_web/backend
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Configurar variáveis

```bash
cp .env.example .env
```

### 4) Instalar dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5) Subir o backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Documentação interativa:

- http://localhost:8000/docs
