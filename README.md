# CartCare AI

An AI customer support assistant for an online electronics store. It answers
policy questions from the store's own documents, looks up products and orders,
and hands the conversation to a human agent when it cannot help. A separate
admin area lets the support team manage tickets, documents, invoices and
analytics.

**Live demo:** https://cartcare-ai-ivory.vercel.app  
**API docs:** https://cartcare-ai-api.onrender.com/docs

> The demo store runs on sample data. Nothing here is connected to a real shop.

### Trying the live demo

- The backend runs on a free hosting plan and goes to sleep when idle. **The
  first request can take about a minute**; after that it responds normally.
- Create an account on the sign-in page and start chatting. Try:
  - `Which air conditioners do you have under $800?`
  - `What is your return policy?`
  - `Where is my order number 2? My email is daniel.carter@example.com`
  - `I want to speak to a human agent.`
- The admin pages (tickets, knowledge base, invoices, analytics) need an admin
  account, which is not public. Ask me for access if you would like to see them.

## What it does

- **Policy answers (RAG).** Returns, shipping, warranty and similar questions
  are answered only from uploaded documents. If the documents do not cover it,
  the assistant says so instead of guessing.
- **Product search.** Filters by category, brand, price and stock.
- **Order status.** Returned only when the order number and the customer's
  email both match.
- **Human handoff.** Creates a support ticket with the recent conversation
  attached. A customer never gets more than one open ticket at a time.
- **Reply checks.** Replies that look broken (for example leaked internal
  text or repeated output) are blocked, retried once, and replaced with a safe
  message if they still fail.
- **Per-user history.** Each user only sees their own conversation.

### Admin area

| Page | Purpose |
|---|---|
| Support tickets | Open and resolved queue, with the attached conversation |
| Knowledge base | Upload, replace and remove documents (PDF or text) |
| Invoices | Reads a supplier PDF into structured data, then re-checks the totals in code and flags anything that does not add up |
| Analytics | Conversations, handoff rate, response times, tool usage, and a list of questions that need attention |

Admin routes are protected by an admin role, not only by login.

## How it works

```
React (Vite)  ->  FastAPI  ->  LLM with tools (Groq)
                     |             |- search_products
                     |             |- get_order_status
                     |             |- request_human_handoff
                     |
                     |->  SQLAlchemy (users, messages, shop data, tickets, invoices, chat logs)
                     |->  ChromaDB (document sections for retrieval)
```

The model decides which tool to call. Tools run as normal Python functions
against the database, and their results are sent back to the model. Order
lookups, ticket creation and invoice checks are done in code, not by the model.

## Tech stack

- **Backend:** Python, FastAPI, SQLAlchemy, ChromaDB, pypdf
- **LLM:** Groq API (model set in `backend/app/core/config.py`)
- **Frontend:** React (Vite), React Router, plain CSS
- **Auth:** JWT with an admin role
- **Hosting:** backend in Docker on Render, PostgreSQL on Neon, frontend on Vercel

## Project layout

```
backend/
  app/
    api/         routes (auth, chat, admin)
    core/        settings and security
    db/          database setup and models
    schemas/     request and response shapes
    services/    agent, retrieval, orders, shop, tickets, invoices, analytics
    bootstrap.py first-start setup (admin, demo store, policies)
  data/          policy document loaded on first start
  scripts/       seed data, admin setup, sample invoices, evals
  Dockerfile
frontend/
  src/           pages (login, chat, tickets, knowledge base, invoices, analytics)
docs/
  store_policies.txt     sample policy document
  sample_invoices/       sample invoices used for testing
```

## Run it locally

You need Python 3.12 or newer, Node.js, and a Groq API key.

### 1. Backend

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `backend/.env` and fill in the values:

| Variable | Meaning |
|---|---|
| `GROQ_API_KEY` | Your Groq key |
| `JWT_SECRET` | A long random string |
| `DATABASE_URL` | Optional. Defaults to a local SQLite file |
| `CORS_ORIGINS` | Optional. Comma-separated frontend addresses, defaults to `http://localhost:5173` |

Create the demo store, then start the server:

```powershell
python -m scripts.seed
uvicorn app.main:app --reload
```

The API is at `http://127.0.0.1:8000`, with interactive docs at `/docs`.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` (use `localhost`, not `127.0.0.1`).

### 3. Create an admin and add the policies

1. Register an account on the sign-in page.
2. Make it an admin (run from `backend`, with the virtual environment active):

   ```powershell
   python -m scripts.make_admin your_username
   ```

3. Sign in, open **Knowledge base**, and upload `docs/store_policies.txt`.

Demo orders belong to the sample customers in `backend/scripts/seed.py`. To try
an order lookup, use order number `2` with the email `daniel.carter@example.com`.

## Deployment

The live demo uses three free services.

**Backend (Render, Docker).** Create a web service from this repository with
the root directory set to `backend`. Environment variables:

| Variable | Meaning |
|---|---|
| `ENVIRONMENT` | `production`. The server refuses to start without a real `JWT_SECRET` |
| `DATABASE_URL` | PostgreSQL connection string (Neon) |
| `JWT_SECRET` | A long random string |
| `GROQ_API_KEY` | Your Groq key |
| `CORS_ORIGINS` | The frontend address, for example `https://your-app.vercel.app` |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | Optional. Creates an admin on first start if it does not exist |

On every start, `app/bootstrap.py` creates the admin (if configured), loads the
demo store when the database is empty, and loads the sample policy document when
the knowledge base is empty. This matters on free hosting, where the document
index is not persistent and is rebuilt after a restart.

**Frontend (Vercel).** Import the repository with the root directory set to
`frontend`, and set `VITE_API_URL` to the backend address.

## Scripts

Run these from the `backend` folder with the virtual environment active.

| Command | What it does |
|---|---|
| `python -m scripts.seed` | Creates the sample store (skips if products already exist) |
| `python -m scripts.reset_demo_data` | Clears shop data, tickets and chat history, then reseeds. User accounts are kept |
| `python -m scripts.make_admin <username>` | Makes a user an admin |
| `python -m scripts.delete_user <username>` | Deletes a user with their messages, tickets and logs |
| `python -m scripts.make_sample_invoices` | Generates sample invoice PDFs and the expected results |
| `python -m scripts.test_invoices` | Checks invoice extraction against the expected results |
| `python -m scripts.run_evals` | Runs a set of sample questions against the assistant and checks the replies |

The evals call the live model, so results can vary slightly between runs.

## Known limitations

- Runs on sample data. It is not connected to a real shop platform.
- Free hosting: the backend sleeps when idle, so the first request is slow.
- Registration is open and there is no rate limiting, so the public demo uses
  my model quota. It is not hardened for real traffic.
- Invoice reading works on text-based PDFs, not scanned images.
- Document retrieval is simple and tuned for a small knowledge base.
- One store only. There is no multi-tenant separation.
- Model replies can occasionally vary or be wrong. The reply checks reduce
  this, but they do not remove it.
- No compliance claims (for example GDPR) are made.

## What I would do next

- A chat widget that can be embedded on any website
- Rate limiting and a stricter sign-up flow
- A larger set of evals, run automatically