# Order Generator

Order Generator is a full-stack application that turns a natural-language
order request into generated sample customer orders. The FastAPI backend uses
an OpenAI model to interpret the request, retrieves matching historical order
data from Cloudflare D1 (SQLite), analyzes the results, and generates orders that follow
the existing JSON order schema. The React/Vite frontend provides the user
interface.

It is deployed and public — see "Where everything lives" below — and also runs
locally.

```text
request -> OpenAI parameter extraction -> D1 data extraction
        -> order analysis -> sample order generation -> React UI
```

## Where everything lives

| Part | Runs on | Address | Cost |
|---|---|---|---|
| Frontend (`frontend/`) | Cloudflare Pages | <https://orders.mauriceneme.com> | free |
| API (`backend/`) | Fly.io, region `sjc` | <https://orders-api.mauriceneme.com> | ~$1/mo |
| Database | Cloudflare D1 `order-generator`, location `wnam` | REST API, ids in `CF_*` | free |
| Model | OpenAI `gpt-5-nano` | — | ~$0.00035/request |

The platform addresses still work underneath: `erp-test-data-generator.pages.dev` and
`order-generator-api.fly.dev`. The custom names mean a future host change is a
DNS edit rather than a new URL to hand out.

Every push to `main` redeploys the frontend automatically. The API is deployed
manually with `fly deploy` from `backend/`.

**How the pieces connect.** The browser only ever talks to Cloudflare. The
frontend calls a relative `/api/...` path, and the Pages Function in
`frontend/functions/api/[[path]].js` forwards it to Fly — so the call stays
same-origin and no CORS is involved. Pages cannot proxy to an external origin
through `_redirects`, which is why that Function exists.

The API reaches D1 through Cloudflare's REST API (`backend/src/order_generator/d1.py`),
since a Worker binding is only available to code running on Cloudflare. D1 is
SQLite: `query.sql` uses `:name` parameters, rewritten to D1's positional `?N`
at import time.

**DNS** for `mauriceneme.com` is in the same Cloudflare account. `orders` is a
proxied CNAME to Pages; `orders-api` is an A/AAAA pair to Fly's IPs, set to
**DNS only** so Fly can issue and terminate its own certificate.

**Configuration lives in three places:** `backend/fly.toml` for the API's
region, port and scaling; Fly secrets for `CF_ACCOUNT_ID`, `CF_D1_DATABASE_ID`, `CF_API_TOKEN`
and `OPENAI_API_KEY`
(`fly secrets list --app order-generator-api`); and the Cloudflare Pages
project settings for the build (root `frontend`, `npm ci && npm run build`,
output `dist`).

**Previously on Render.** `render.yaml` and the two suspended Render services
are kept as a rollback: resume them in the Render dashboard and the blueprint
still works. Delete both once Fly has proven itself.

## Local setup (Windows)

The backend and frontend run separately and should be kept open in two
PowerShell terminals.

### 1. Required access

Before starting, obtain:

- Access to the GitHub repository.
- A Cloudflare account with a D1 database and an API token with D1 Edit (see
  "Create the database" below).
- An OpenAI API key with access to the model configured by the application.

Never commit credentials, connection strings, or the local `.env` file.

### 2. Install the development tools

Install Git, `uv`, and the Node.js LTS release:

```powershell
winget install --id Git.Git -e
winget install --id astral-sh.uv -e
winget install --id OpenJS.NodeJS.LTS -e
```

Node.js includes `npm`. Vite should not be installed globally; it will be
installed from this project's lockfile.

Close and reopen PowerShell after installation, then verify the tools:

```powershell
git --version
uv --version
node --version
npm --version
```

The frontend requires Node.js 20.19+ or 22.12+. A separate Python installation
is normally unnecessary because `uv` can download a compatible Python version.

### 3. Clone the repository

```powershell
git clone <repository-url>
cd Test_App
```

Replace `<repository-url>` with the repository's GitHub clone URL.

### 4. Configure the backend

```powershell
cd backend
Copy-Item .env.example .env
notepad .env
```

Complete `backend/.env` with the values provided by the project owner:

```dotenv
CF_ACCOUNT_ID=<cloudflare-account-id>
CF_D1_DATABASE_ID=<d1-database-id>
CF_API_TOKEN=<api-token-with-d1-edit>

OPENAI_API_KEY=<openai-api-key>

ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ALLOWED_HOSTS=localhost,127.0.0.1
```

Do not put spaces between comma-separated origins or hosts.

### 5. Create the database

The application reads order data from a Cloudflare D1 database. To create one:

1. Create the database close to the API (`wnam` is western North America):
   `npx wrangler d1 create order-generator --location=wnam`. Copy the printed
   `database_id` into `CF_D1_DATABASE_ID`, and your account id
   (`npx wrangler whoami`) into `CF_ACCOUNT_ID`.
2. In the Cloudflare dashboard, **My Profile -> API Tokens -> Create Token ->
   Custom token**, with the single permission **Account / D1 / Edit**. Put it in
   `CF_API_TOKEN`.
3. From `backend/`, create the tables and load sample data:

```powershell
uv sync --frozen
uv run python db\load.py
```

`db\schema.sql` creates the order tables and `db\seed.py` generates the
sample data (seeded, so every run produces the same rows). Safe to re-run;
re-running replaces the existing contents.

### 6. Install and run the backend

From `backend/`, create the virtual environment and install the locked
dependencies:

```powershell
uv sync --frozen
```

`uv sync` creates `backend/.venv`, selects or downloads a compatible Python
version (Python 3.11 or newer), and installs the backend dependencies.

Start the backend:

```powershell
uv run python .\src\order_generator\api.py
```

The API will be available at:

- API: <http://127.0.0.1:4555>
- Interactive documentation: <http://127.0.0.1:4555/docs>

For automatic restart after Python code changes, use this alternative:

```powershell
uv run uvicorn order_generator.api:app --reload --port 4555
```

### 7. Install and run the frontend

Open a second PowerShell terminal, enter the frontend directory, and install the
locked dependencies:

```powershell
cd <path-to-Test_App>\frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. The Vite development server proxies frontend
`/api` requests to the backend at `http://127.0.0.1:4555`.

## Verification

Run the backend checks from `backend/`:

```powershell
uv run python -m unittest discover -s tests -p "test_*.py"
```

Verify a production frontend build from `frontend/`:

```powershell
npm run build
```

## Daily startup

After the first-time setup, start the backend:

```powershell
cd Test_App\backend
uv run python .\src\order_generator\api.py
```

Then start the frontend in a second terminal:

```powershell
cd Test_App\frontend
npm run dev
```

Run `uv sync --frozen` or `npm ci` again after pulling dependency-file changes.

## API rate limits

The deployed API is public and every order request costs an OpenAI call, so
usage is capped in two layers:

- **Per client**, in `rate_limit.py`: 10 requests per minute, 30 per hour,
  counted in memory. Burst control only, and best effort — behind Render's
  proxy the caller is identified by the first address in `X-Forwarded-For`,
  which can be forged. A restart resets these, which costs nothing because the
  extra requests still count against the global cap below.
- **Across all clients**, in `usage_limit.py`: 100 requests per hour and 500
  per day, counted in the `api_usage` table in D1 so the cap survives
  restarts, redeploys and idle shutdowns. This is the layer that bounds spend.

Exceeding either returns HTTP 429 with a readable message and **no model call
is made**. If the database cannot be reached the request is refused with 503
rather than served, since a request that cannot reach the database would spend
a model call and then fail anyway.

Limits are overridable per environment: `RATE_LIMIT_PER_CLIENT`,
`LIMIT_GLOBAL_HOURLY`, `LIMIT_GLOBAL_DAILY`. The `api_usage` table is created
automatically on startup and is deliberately not part of `db/schema.sql`, so
re-running `db\load.py` to reseed demo data does not wipe the counter.

## Common setup problems

- If `uv`, `node`, or `npm` is not recognized, close and reopen PowerShell.
- If the database cannot be reached, check the three `CF_*` values in
  `backend/.env`, and that the API token is active and has D1 Edit.
- If the query fails with a missing table or column, re-run
  `uv run python db\load.py`.
- If OpenAI requests fail, verify the API key and model access.
- If the API reports an invalid host, verify `ALLOWED_HOSTS` in `backend/.env`.
- If port 4555 or 5173 is unavailable, stop the process already using that port.
