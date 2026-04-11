"""
Async SQLite persistence layer for the multi-tool agent.

Uses aiosqlite for all DB operations. Three tables are managed here:
  - conversations: groups related tasks into a multi-turn thread
  - tasks: top-level agent run records (each belongs to a conversation)
  - trace_steps: ordered steps emitted during a run
"""

import os

import aiosqlite


async def init_db(db_path: str) -> None:
    """
    Create the data directory and both tables (tasks, trace_steps) if they do
    not already exist. Must be called once on application startup.

    Args:
        db_path: Path to the SQLite database file.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys = ON")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id  TEXT     PRIMARY KEY,
                title            TEXT,
                created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id         TEXT    PRIMARY KEY,
                conversation_id TEXT    NOT NULL REFERENCES conversations(conversation_id),
                input           TEXT    NOT NULL,
                final_answer    TEXT,
                status          TEXT    NOT NULL,
                token_usage     INTEGER,
                latency_ms      INTEGER,
                created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS trace_steps (
                id          INTEGER  PRIMARY KEY AUTOINCREMENT,
                task_id     TEXT     NOT NULL REFERENCES tasks(task_id),
                step_index  INTEGER  NOT NULL,
                type        TEXT     NOT NULL,
                description TEXT,
                tool_name   TEXT,
                tool_input  TEXT,
                tool_output TEXT
            )
        """)

        await db.commit()


async def create_conversation(db_path: str, conversation_id: str) -> None:
    """
    Insert a new conversation row.

    Args:
        db_path:         Path to the SQLite database file.
        conversation_id: UUID string that uniquely identifies the conversation.
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO conversations (conversation_id) VALUES (?)",
            (conversation_id,),
        )
        await db.commit()


async def get_conversation(db_path: str, conversation_id: str) -> dict | None:
    """
    Fetch a conversation row by its ID.

    Args:
        db_path:         Path to the SQLite database file.
        conversation_id: The UUID of the conversation.

    Returns:
        A dict of column values, or None if no such conversation exists.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT conversation_id, title, created_at FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row is not None else None


async def create_task(db_path: str, task_id: str, conversation_id: str, input: str) -> None:
    """
    Insert a new task row with status='pending'.

    Args:
        db_path:         Path to the SQLite database file.
        task_id:         UUID string that uniquely identifies the run.
        conversation_id: The parent conversation UUID.
        input:           The user's original task text.
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO tasks (task_id, conversation_id, input, status) VALUES (?, ?, ?, 'pending')",
            (task_id, conversation_id, input),
        )
        await db.commit()


async def update_task(
    db_path: str,
    task_id: str,
    final_answer: str | None,
    status: str,
    token_usage: int | None,
    latency_ms: int | None,
) -> None:
    """
    Update a task row after the agent run completes (or fails).

    Args:
        db_path:      Path to the SQLite database file.
        task_id:      The task to update.
        final_answer: The agent's final answer text, or None if failed.
        status:       One of 'completed' or 'failed'.
        token_usage:  Total tokens consumed across all LLM calls.
        latency_ms:   Total wall-clock milliseconds for the run.
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            UPDATE tasks
               SET final_answer = ?,
                   status       = ?,
                   token_usage  = ?,
                   latency_ms   = ?
             WHERE task_id = ?
            """,
            (final_answer, status, token_usage, latency_ms, task_id),
        )
        await db.commit()


async def get_task(db_path: str, task_id: str) -> dict | None:
    """
    Fetch a single task row by its ID.

    Args:
        db_path: Path to the SQLite database file.
        task_id: The UUID of the task to retrieve.

    Returns:
        A dict of column→value, or None if no such task exists.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT task_id, conversation_id, input, final_answer, status, token_usage, latency_ms, created_at FROM tasks WHERE task_id = ?",
            (task_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row is not None else None


async def insert_trace_step(
    db_path: str,
    task_id: str,
    step_index: int,
    type: str,
    tool_name: str | None,
    tool_input: str | None,
    tool_output: str | None,
    description: str | None = None,
) -> None:
    """
    Insert a single trace step for a task.

    Args:
        db_path:     Path to the SQLite database file.
        task_id:     The parent task UUID.
        step_index:  0-based ordering index within the run.
        type:        One of 'llm_reasoning', 'tool_call', or 'final_answer'.
        tool_name:   Name of the tool invoked (only for tool_call).
        tool_input:  JSON string of tool arguments (may be None).
        tool_output: JSON string of tool return value (may be None).
        description: Short human-readable summary of this step (may be None).
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """
            INSERT INTO trace_steps
                (task_id, step_index, type, tool_name, tool_input, tool_output, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (task_id, step_index, type, tool_name, tool_input, tool_output, description),
        )
        await db.commit()


async def get_trace_steps(db_path: str, task_id: str) -> list[dict]:
    """
    Return all trace steps for a task, ordered by step_index ascending.

    Args:
        db_path: Path to the SQLite database file.
        task_id: The parent task UUID.

    Returns:
        A list of dicts, one per step, in execution order.
    """
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, task_id, step_index, type, tool_name, tool_input, tool_output, description FROM trace_steps WHERE task_id = ? ORDER BY step_index ASC",
            (task_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


