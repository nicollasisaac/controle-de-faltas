
# SSTM Attendance API

API simples em **FastAPI + SQLModel** para gestão de grupos, eventos e presenças, com
autenticação JWT e integração pronta para PostgreSQL (Supabase / Render).

---

## ✨ Funcionalidades

- **Grupos** (ex.: `SSTM`) → **Pessoas** → **Eventos**
- Controle de presença/falta por evento
- Regras automáticas  
  - **3** faltas ⇒ `warning =True`  
  - **5** faltas ⇒ `suspended =True`
- Admin (único) com login e edição protegidos
- Swagger UI automático (`/docs`)
- Suite de testes Pytest (inclui base SQLite in-memory)
- Dockerfile pronto para deploy no **Render.com**

---

## 🖇️ Pré-requisitos

| Item            | Versão mínima |
|-----------------|---------------|
| Python          | 3.10          |
| PostgreSQL      | 12            |
| [docker](https://docs.docker.com/get-docker/) _(opcional)_ | 20.10 |

Crie um arquivo **`.env`** na raiz com:

```env
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
JWT_SECRET=uma-string-muito-segura
ADMIN_EMAIL=admin@sstm.app
ADMIN_PWD_HASH=$2b$12$9kw...          # gere com:
# python -m passlib.hash bcrypt --rounds 12 "suaSenha"
````

---

## 🚀 Rodando localmente

```bash
# 1. ambiente virtual
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 2. dependências
pip install -r requirements.txt

# 3. iniciar servidor (auto-reload)
uvicorn main:app --reload
# → http://localhost:8000/docs
```

---

## ✅ Testes

```bash
pytest         # executa 100 % da suíte
pytest --cov   # + relatório de cobertura
```

---

## 🐳 Docker

```bash
# construir imagem
docker build -t sstm-api .

# executar (usa .env)
docker run --env-file .env -p 8000:8000 sstm-api
```

---

## ☁️ Deploy no Render

1. **New ➜ Web Service ➜ Deploy from GitHub**
2. *Environment* → **Docker**
3. Variáveis → copie as do `.env`
4. Health check → `/docs` ou `/groups`
5. Salvar. A cada *push* o Render faz *build* e publica.

---

## 📚 Endpoints principais

| Método | Rota                       | Protegido | Descrição                |
| ------ | -------------------------- | --------- | ------------------------ |
| POST   | `/login`                   | ❌         | obtém *token* JWT        |
| GET    | `/groups`                  | ❌         | lista grupos             |
| POST   | `/groups`                  | ✅         | cria grupo               |
| DELETE | `/groups/{gid}`            | ✅         | remove grupo (cascata)   |
| GET    | `/groups/{gid}/summary`    | ❌         | resumo presenças/faltas  |
| POST   | `/groups/{gid}/persons`    | ✅         | adiciona pessoa ao grupo |
| POST   | `/groups/{gid}/events`     | ✅         | cria evento no grupo     |
| DELETE | `/events/{eid}`            | ✅         | remove evento            |
| POST   | `/events/{eid}/attendance` | ✅         | marca presença/falta     |

---

### Licença

MIT © 2025 — SSTM
