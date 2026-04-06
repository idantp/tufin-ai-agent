# tufin-ai-agent

Multi-tool agent with async SQLite persistence.

## Database Setup

This project uses two separate SQLite databases:

### 1. Agent Database (`./data/agent.db`)

Stores agent task runs and execution traces. Created automatically on first run when `init_db()` is called from `app/database.py`.

**Manual initialization (optional):**

```bash
python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"
```

Or with `uv`:

```bash
uv run python -c "import asyncio; from app.database import init_db; asyncio.run(init_db())"
```

This creates:
- `./data/` directory (if it doesn't exist)
- `tasks` table (task_id, input, final_answer, status, token_usage, latency_ms, created_at)
- `trace_steps` table (id, task_id, step_index, type, content, tool_name, tool_input, tool_output, timestamp)

### 2. Catalog Database (`./data/catalog.db`)

Sample database for the `database_query` tool. Contains products and orders tables with realistic fake data.

**To seed:**

```bash
python scripts/seed_db.py
```

Or with `uv`:

```bash
uv run python scripts/seed_db.py
```

Output:
```
✓ Seeded 15 products and 20 orders into ./data/catalog.db
```

This creates:
- `products` table (15 rows: Electronics, Furniture, Kitchen, Sports, Stationery)
- `orders` table (20 rows with statuses: pending, shipped, delivered)

The script is idempotent — running it multiple times will drop and recreate the tables with fresh data.