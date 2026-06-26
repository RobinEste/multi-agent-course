# Customer Support Agent — Quick Start

Multi-agent customer support CLI built with Google ADK, MCP Toolbox, A2A security microservices, Mem0 memory, and Arize Phoenix observability. Runs entirely locally — no GCP credentials required.

## Prerequisites

| Tool | Version | Purpose |
|:-----|:--------|:--------|
| Python | 3.12+ | Runtime |
| conda | any | PostgreSQL server |
| Node.js | 18+ | MCP Toolbox via npx |

---

## 1 — Clone / Unzip

```bash
unzip advance-customer-support-agent.zip
cd advance-customer-support-agent-feature-A2A-MCP-ADK
```

---

## 2 — Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set these two keys (everything else can stay blank):

```env
GOOGLE_GENAI_USE_ENTERPRISE=false
PYTHONWARNINGS=ignore

GOOGLE_API_KEY=<your Google AI Studio key>   # aistudio.google.com/apikey
MEM0_API_KEY=<your Mem0 key>                 # mem0.ai
```

> **Note** — do not set `GOOGLE_GENAI_USE_VERTEXAI`. That variable is deprecated and will produce warnings.

---

## 3 — Python Dependencies

```bash
pip install -r requirements.txt

# Observability (Phoenix + OpenTelemetry)
pip install arize-phoenix openinference-instrumentation-google-genai \
    opentelemetry-sdk opentelemetry-exporter-otlp-proto-http \
    openinference-semantic-conventions

# Pin OTel back to ADK-compatible version
pip install opentelemetry-sdk==1.33.1 \
    opentelemetry-exporter-otlp-proto-http==1.33.1
```

---

## 4 — PostgreSQL (via conda)

```bash
# Install postgres in your conda env (once)
conda install -c conda-forge postgresql -y

# Initialise a data directory (once)
initdb -D ~/postgres_data

# Start the server
pg_ctl -D ~/postgres_data -l ~/postgres_data/logfile start

# Create DB and user (once)
createdb toolbox_db
psql -d toolbox_db -c "CREATE USER toolbox_user WITH PASSWORD 'mysecretpassword';"
psql -d toolbox_db -c "GRANT ALL PRIVILEGES ON DATABASE toolbox_db TO toolbox_user;"
```

### Seed the database

Run the following SQL once inside `psql -U toolbox_user -d toolbox_db`:

<details>
<summary><strong>Show SQL — click to expand</strong></summary>

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    is_premium_customer BOOLEAN DEFAULT FALSE,
    total_items_purchased INTEGER DEFAULT 0,
    password VARCHAR(255) NOT NULL
);

INSERT INTO users (email, full_name, is_premium_customer, total_items_purchased, password) VALUES
    ('hannah.m@school.edu',       'Hannah M',    TRUE,  94, 'hannah'),
    ('charlie.d@webmail.com',     'Charlie D',   TRUE,  88, 'charlie'),
    ('julia.child@kitchen.com',   'Julia Child', TRUE,  75, 'julia'),
    ('evan.g@bizcorp.com',        'Evan G',      TRUE,  56, 'evan'),
    ('alice.jones@example.com',   'Alice Jones', FALSE, 42, 'alice'),
    ('ian.malcolm@chaos.com',     'Ian Malcolm', FALSE, 31, 'ian'),
    ('diana.prince@hero.net',     'Diana Prince',FALSE, 23, 'diana'),
    ('george.j@jungle.com',       'George J',    FALSE, 19, 'george'),
    ('bob.smith@techmail.com',    'Bob Smith',   FALSE, 15, 'bob'),
    ('fiona.shrek@swamp.com',     'Fiona Shrek', FALSE, 12, 'fiona');

CREATE TABLE customer_orders (
    order_id SERIAL PRIMARY KEY,
    customer_email VARCHAR(100) NOT NULL,
    delivery_address VARCHAR(255),
    status VARCHAR(20) CHECK (status IN ('PROCESSING','SHIPPED','DELIVERED','CANCELLED','RETURNED')),
    items JSONB,
    order_date TIMESTAMPTZ DEFAULT NOW(),
    total_amount DECIMAL(10,2)
);

INSERT INTO customer_orders (customer_email, delivery_address, status, items, order_date, total_amount) VALUES
('alice.jones@example.com','123 Market St, Springfield','DELIVERED','[{"product":"Ergonomic Office Chair","qty":1,"price":250.00}]',NOW()-INTERVAL '6 months',250.00),
('alice.jones@example.com','123 Market St, Springfield','DELIVERED','[{"product":"Wireless Mouse","qty":1,"price":25.00}]',NOW()-INTERVAL '3 months',25.00),
('alice.jones@example.com','123 Market St, Springfield','SHIPPED','[{"product":"Mechanical Keyboard","qty":1,"price":120.00}]',NOW()-INTERVAL '2 days',120.00),
('alice.jones@example.com','123 Market St, Springfield','PROCESSING','[{"product":"USB-C Hub","qty":1,"price":45.00}]',NOW()-INTERVAL '1 hour',45.00),
('bob.smith@techmail.com','88 Tech Ave, Seattle','DELIVERED','[{"product":"Gaming Laptop 15-inch","qty":1,"price":1500.00}]',NOW()-INTERVAL '1 year',1500.00),
('bob.smith@techmail.com','88 Tech Ave, Seattle','CANCELLED','[{"product":"VR Headset","qty":1,"price":400.00}]',NOW()-INTERVAL '10 days',400.00),
('bob.smith@techmail.com','88 Tech Ave, Seattle','PROCESSING','[{"product":"Curved Monitor 34-inch","qty":1,"price":450.00}]',NOW()-INTERVAL '4 hours',450.00),
('charlie.d@webmail.com','12 Oak Rd, Denver','DELIVERED','[{"product":"AA Batteries (Pack of 12)","qty":2,"price":15.00}]',NOW()-INTERVAL '45 days',30.00),
('diana.prince@hero.net','5 Hero Ln, Metropolis','DELIVERED','[{"product":"Smart Watch Gen 5","qty":1,"price":299.00}]',NOW()-INTERVAL '60 days',299.00),
('diana.prince@hero.net','5 Hero Ln, Metropolis','RETURNED','[{"product":"Running Shoes","qty":1,"price":120.00}]',NOW()-INTERVAL '15 days',120.00),
('evan.g@bizcorp.com','200 Business Pkwy, Austin','SHIPPED','[{"product":"Office Desk","qty":2,"price":300.00}]',NOW()-INTERVAL '1 day',600.00),
('fiona.shrek@swamp.com','7 Swamp Rd, Bayou','CANCELLED','[{"product":"Skincare Gift Set","qty":1,"price":85.00}]',NOW()-INTERVAL '5 days',85.00),
('george.j@jungle.com','9 Jungle Path, Amazonia','PROCESSING','[{"product":"Bluetooth Speaker","qty":1,"price":60.00}]',NOW()-INTERVAL '30 minutes',60.00),
('hannah.m@school.edu','4 Campus Dr, Boston','DELIVERED','[{"product":"Notebook Pack","qty":5,"price":12.00}]',NOW()-INTERVAL '4 months',60.00),
('ian.malcolm@chaos.com','22 Chaos Blvd, San Diego','DELIVERED','[{"product":"Professional Camera Lens","qty":1,"price":2200.00}]',NOW()-INTERVAL '8 months',2200.00),
('julia.child@kitchen.com','10 Kitchen St, Portland','DELIVERED','[{"product":"Coffee Beans 1kg","qty":1,"price":25.00}]',NOW()-INTERVAL '3 months',25.00),
('julia.child@kitchen.com','10 Kitchen St, Portland','PROCESSING','[{"product":"Descaling Kit","qty":1,"price":15.00}]',NOW()-INTERVAL '3 hours',15.00);

CREATE TABLE actions_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_email VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO toolbox_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO toolbox_user;
```

</details>

---

## 5 — Run (4 terminals)

Open four terminal tabs from the project root.

**Terminal 1 — MCP Toolbox**
```bash
npx @toolbox-sdk/server --tools-file mcp_toolbox/tools.yaml --enable-api
```
Starts on `http://127.0.0.1:5000`. Wait for `Serving on ...` before continuing.

**Terminal 2 — A2A Security Servers**
```bash
python -m cs_agent.a2a.run_servers
```
Starts Judge (`:10002`) and Mask (`:10003`). Wait for both `Started server on ...` lines.

**Terminal 3 — Phoenix Observability** *(optional)*
```bash
python - <<'EOF'
import phoenix as px
app = px.launch_app()
print("Phoenix running at http://localhost:6006")
while True:
    __import__("time").sleep(60)
EOF
```
Dashboard at `http://localhost:6006`.

**Terminal 4 — Agent**
```bash
cd cs_agent
python agent_cli.py
```

The CLI will display the user list, ask you to pick a user, then start the conversation.

---

## Startup order matters

```
PostgreSQL  →  MCP Toolbox  →  A2A Servers  →  (Phoenix)  →  Agent
```

---

## Test users & passwords

| Email | Password | Tier |
|:------|:---------|:-----|
| alice.jones@example.com | alice | Standard |
| bob.smith@techmail.com | bob | Standard |
| hannah.m@school.edu | hannah | Premium |
| julia.child@kitchen.com | julia | Premium |

---

## Sample queries to try

```
What's the status of my latest order?
Show me all my orders
Cancel order 3
I want to return order 1
```

---

## Project structure

```
├── cs_agent/
│   ├── agent_cli.py          # Entry point
│   ├── telemetry.py          # OpenTelemetry → Phoenix
│   ├── memory.py             # Mem0 integration
│   ├── prompts.py            # System prompts
│   ├── greet.py              # Login flow
│   ├── a2a/                  # A2A microservice infrastructure
│   ├── agents/               # Judge + Mask ADK agents
│   └── security/             # Regex blocker + sanitizer
├── mcp_toolbox/
│   └── tools.yaml            # DB tool definitions (Postgres)
├── .env                      # Your keys (not committed)
├── .env.example              # Template
└── requirements.txt
```

---

## Troubleshooting

**A2A servers not reachable** — start Terminal 2 first and wait for both `Started server` lines before running the agent.

**MCP Toolbox connection refused** — ensure Terminal 1 shows `Serving on` before running the agent.

**PostgreSQL not running** — run `pg_ctl -D ~/postgres_data status`; if stopped, run `pg_ctl -D ~/postgres_data start`.

**Warnings in terminal** — make sure `.env` has `PYTHONWARNINGS=ignore` and does not contain `GOOGLE_GENAI_USE_VERTEXAI`. If you previously ran `export GOOGLE_GENAI_USE_VERTEXAI=false` in your shell, run `unset GOOGLE_GENAI_USE_VERTEXAI` before starting the agent.
