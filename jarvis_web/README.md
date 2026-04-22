# Jarvis

README final, direto e completo para rodar o projeto localmente em **Debian/Ubuntu**.

## 1) Requisitos

Instale os pacotes básicos do sistema:

```bash
sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  curl ca-certificates gnupg
```

> O frontend usa Node.js. Se sua distro já tiver Node recente, pode usar `sudo apt install -y nodejs npm`.
> Caso contrário, instale Node LTS pelo repositório oficial do NodeSource.

---

## 2) Versão recomendada do Python

- **Python 3.11** (recomendado)
- Mínimo prático: Python 3.10+

Verifique:

```bash
python3 --version
```

---

## 3) Versão recomendada do Node.js

- **Node.js 20 LTS** (recomendado)
- npm 10+

Verifique:

```bash
node -v
npm -v
```

Se precisar instalar Node 20 no Debian/Ubuntu:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## 4) Criação do ambiente virtual Python

No diretório do backend:

```bash
cd jarvis_web/backend
python3 -m venv .venv
source .venv/bin/activate
```

---

## 5) Instalação das dependências do backend

Ainda em `jarvis_web/backend`:

```bash
cp .env.example .env
pip install --upgrade pip
pip install -r requirements.txt
```

Dependências principais: FastAPI, SQLAlchemy, Uvicorn e OpenAI SDK.

---

## 6) Instalação das dependências do frontend

Em outro terminal:

```bash
cd jarvis_web/frontend
cp .env.example .env
npm install
```

---

## 7) Como rodar o backend

Com o virtualenv ativo:

```bash
cd jarvis_web/backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend/API:

- `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

---

## 8) Como rodar o frontend

Em outro terminal:

```bash
cd jarvis_web/frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

---

## 9) Endereço local de acesso

- **Aplicação web (frontend):** `http://localhost:5173`
- **API backend:** `http://localhost:8000`
- **Documentação da API:** `http://localhost:8000/docs`

---

## 10) Arquitetura resumida

- **Frontend (Vue 3 + Vite):** interface do usuário e telas de módulos (tarefas, notas, gastos, etc.).
- **Backend (FastAPI):** expõe APIs REST em `/api/*`, valida dados e aplica regras de negócio.
- **Banco (SQLite):** persistência local de tarefas, lembretes, conversas e configurações.
- **Assistente IA:** backend lê a configuração OpenAI salva no banco e chama a API da OpenAI no endpoint de chat.

Fluxo:

1. Usuário interage no frontend.
2. Frontend chama backend (`/api/...`).
3. Backend lê/grava no SQLite.
4. No chat, backend usa chave OpenAI salva em configurações.

---

## 11) Localização do arquivo SQLite

Por padrão, o backend usa:

- `sqlite:///./jarvis_web.db`

Na prática, executando a API a partir de `jarvis_web/backend`, o arquivo fica em:

- `jarvis_web/backend/jarvis_web.db`

---

## 12) Como configurar a chave OpenAI pela interface

1. Abra o frontend em `http://localhost:5173`.
2. Vá para a tela **Configurações**.
3. Informe:
   - `openai_api_key`
   - `openai_model` (opcional; padrão recomendado do projeto já é aplicado)
4. Salve.

Essa configuração é enviada para `PUT /api/settings/openai` e fica persistida no SQLite.

---

## 13) Problemas comuns e como resolver

### Erro: `python3 -m venv` não funciona

Instale o pacote de venv:

```bash
sudo apt install -y python3-venv
```

### Erro: `uvicorn: command not found`

Você provavelmente não ativou o virtualenv:

```bash
cd jarvis_web/backend
source .venv/bin/activate
pip install -r requirements.txt
```

### Erro de CORS no frontend

Confirme:

- Frontend em `http://localhost:5173`
- Backend em `http://localhost:8000`
- `VITE_API_BASE_URL` apontando para o backend no `.env` do frontend.

### Porta ocupada (8000 ou 5173)

Troque a porta:

```bash
# backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# frontend
npm run dev -- --host 0.0.0.0 --port 5174
```

### Chat não responde / erro de autenticação OpenAI

- Verifique se a chave foi salva em **Configurações**.
- Teste o endpoint `GET /api/settings/openai`.
- Confira se há saldo/permissão na conta OpenAI e se o modelo configurado é válido.

### Banco não criado

- Verifique permissões de escrita na pasta `jarvis_web/backend`.
- Confirme que o backend subiu sem erro na inicialização.

---

## Execução rápida (resumo)

Terminal 1 (backend):

```bash
cd jarvis_web/backend
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
pip install -U pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (frontend):

```bash
cd jarvis_web/frontend
cp .env.example .env
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Acesse: **http://localhost:5173**
