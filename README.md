# jarvis_web

Projeto fullstack com **frontend (Vue 3 + Vite + Tailwind)** e **backend (FastAPI + SQLAlchemy + SQLite)** para um assistente pessoal web com módulos organizacionais.

## Funcionalidades

- Assistente/chat com persistência de histórico
- Tarefas
- Compromissos
- Notas
- Gastos
- Lembretes
- Configurações do sistema

## Estrutura de pastas

```text
jarvis_web/
├── .env.example
├── backend/
│   ├── requirements.txt
│   └── app/
│       ├── core/
│       │   └── config.py
│       ├── routers/
│       │   ├── chat.py
│       │   ├── modules.py
│       │   └── settings.py
│       ├── services/
│       │   └── openai_client.py
│       ├── db.py
│       ├── main.py
│       ├── models.py
│       └── schemas.py
└── frontend/
    ├── package.json
    ├── index.html
    ├── postcss.config.js
    ├── tailwind.config.js
    ├── vite.config.js
    └── src/
        ├── router/
        │   └── index.js
        ├── services/
        │   └── api.js
        ├── views/
        │   ├── ChatView.vue
        │   ├── ModuleView.vue
        │   └── SettingsView.vue
        ├── App.vue
        ├── main.js
        └── style.css
```

## Pré-requisitos (Debian/Ubuntu)

- Python 3.11+
- Node.js 20+
- npm

Instalação sugerida:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm
```

## Configuração

1. Clone/acesse o projeto.
2. Copie as variáveis de ambiente:

```bash
cp jarvis_web/.env.example jarvis_web/backend/.env
cp jarvis_web/.env.example jarvis_web/frontend/.env
```

3. Ajuste `OPENAI_API_KEY` no `jarvis_web/backend/.env`.

> Se a chave não for definida, o chat responde em modo fallback local para facilitar testes.

## Rodando o backend

```bash
cd jarvis_web/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- O banco SQLite (`jarvis_web.db`) é criado automaticamente na primeira execução.
- Swagger: `http://localhost:8000/docs`

## Rodando o frontend

Em outro terminal:

```bash
cd jarvis_web/frontend
npm install
npm run dev
```

- A aplicação estará em `http://localhost:5173`

## Rotas principais da API

### Sistema
- `GET /` - health simples
- `GET /api/settings` - informações de configuração pública

### Chat
- `GET /api/chat/history` - lista histórico
- `POST /api/chat` - envia mensagem para o assistente

Body exemplo:

```json
{
  "message": "Me ajude a priorizar minhas tarefas de hoje"
}
```

### CRUD genérico dos módulos
Para cada módulo abaixo, existem as rotas:
- `GET /api/{module}`
- `POST /api/{module}`
- `PUT /api/{module}/{item_id}`
- `DELETE /api/{module}/{item_id}`

Módulos disponíveis:
- `tasks`
- `appointments`
- `notes`
- `expenses`
- `reminders`

## Telas principais do frontend

- **Assistente**: conversa com histórico persistido
- **Tarefas**: cadastro/listagem/edição/exclusão
- **Compromissos**: cadastro/listagem/edição/exclusão
- **Notas**: cadastro/listagem/edição/exclusão
- **Gastos**: cadastro/listagem/edição/exclusão
- **Lembretes**: cadastro/listagem/edição/exclusão
- **Configurações**: leitura de dados da API

## Observações de arquitetura

- Frontend e backend separados para facilitar evolução e deploy independente.
- API REST em JSON com CORS habilitado.
- Organização inicial simples, pronta para escalar com novos routers/services.
