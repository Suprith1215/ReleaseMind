"""
ReleaseMind — Database Layer (SQLite)
Phase 4: Historical Failure Learning
"""

import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "releasemind.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS deployments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            risk_score  REAL    NOT NULL,
            strategy    TEXT    NOT NULL,
            outcome     TEXT    DEFAULT 'pending',   -- pending | success | failure
            service     TEXT    NOT NULL,
            developer   TEXT    NOT NULL DEFAULT 'unknown',
            repo_owner  TEXT,
            repo_name   TEXT,
            branch      TEXT,
            commit_sha  TEXT,
            files_changed INTEGER DEFAULT 0,
            lines_added   INTEGER DEFAULT 0,
            lines_deleted INTEGER DEFAULT 0,
            commit_type   TEXT    DEFAULT 'unknown',
            blast_radius  INTEGER DEFAULT 0,
            dep_depth     INTEGER DEFAULT 0,
            cpu_at_deploy REAL    DEFAULT 0.0,
            mem_at_deploy REAL    DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS service_stats (
            service         TEXT    PRIMARY KEY,
            total_deploys   INTEGER DEFAULT 0,
            total_failures  INTEGER DEFAULT 0,
            failure_rate    REAL    DEFAULT 0.0,
            last_updated    TEXT
        );
    """)

    conn.commit()
    conn.close()


def record_deployment(data: dict) -> int:
    """Insert a new deployment record and return its ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO deployments (
            timestamp, risk_score, strategy, outcome,
            service, developer, repo_owner, repo_name, branch,
            commit_sha, files_changed, lines_added, lines_deleted,
            commit_type, blast_radius, dep_depth, cpu_at_deploy, mem_at_deploy
        ) VALUES (
            :timestamp, :risk_score, :strategy, :outcome,
            :service, :developer, :repo_owner, :repo_name, :branch,
            :commit_sha, :files_changed, :lines_added, :lines_deleted,
            :commit_type, :blast_radius, :dep_depth, :cpu_at_deploy, :mem_at_deploy
        )
    """, {
        "timestamp":     data.get("timestamp",      datetime.now(timezone.utc).isoformat()),
        "risk_score":    data.get("risk_score",     0.0),
        "strategy":      data.get("strategy",       "UNKNOWN"),
        "outcome":       data.get("outcome",        "pending"),
        "service":       data.get("service",        "unknown"),
        "developer":     data.get("developer",      "unknown"),
        "repo_owner":    data.get("repo_owner",     None),
        "repo_name":     data.get("repo_name",      None),
        "branch":        data.get("branch",         None),
        "commit_sha":    data.get("commit_sha",     None),
        "files_changed": data.get("files_changed",  0),
        "lines_added":   data.get("lines_added",    0),
        "lines_deleted": data.get("lines_deleted",  0),
        "commit_type":   data.get("commit_type",    "unknown"),
        "blast_radius":  data.get("blast_radius",   0),
        "dep_depth":     data.get("dep_depth",      0),
        "cpu_at_deploy": data.get("cpu_at_deploy",  0.0),
        "mem_at_deploy": data.get("mem_at_deploy",  0.0),
    })

    dep_id = cursor.lastrowid

    # Upsert service stats
    service = data.get("service", "unknown")
    cursor.execute("""
        INSERT INTO service_stats (service, total_deploys, total_failures, failure_rate, last_updated)
        VALUES (?, 1, 0, 0.0, ?)
        ON CONFLICT(service) DO UPDATE SET
            total_deploys = total_deploys + 1,
            last_updated  = excluded.last_updated
    """, (service, datetime.now(timezone.utc).isoformat()))

    conn.commit()
    conn.close()
    return dep_id


def update_outcome(deployment_id: int, outcome: str):
    """Update deployment outcome and recalculate failure rate."""
    if outcome not in ("success", "failure"):
        raise ValueError("outcome must be 'success' or 'failure'")

    conn = get_connection()
    cursor = conn.cursor()

    # Fetch service for this deployment
    cursor.execute("SELECT service FROM deployments WHERE id = ?", (deployment_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Deployment ID {deployment_id} not found")

    service = row["service"]

    cursor.execute(
        "UPDATE deployments SET outcome = ? WHERE id = ?",
        (outcome, deployment_id)
    )

    # Recalculate failure rate from rolling window (last N deployments)
    cursor.execute("""
        SELECT outcome FROM deployments
        WHERE service = ? AND outcome IN ('success', 'failure')
        ORDER BY id DESC LIMIT 10
    """, (service,))
    rows = cursor.fetchall()
    total = len(rows)
    failures = sum(1 for r in rows if r["outcome"] == "failure")
    rate = (failures / total) if total > 0 else 0.0

    cursor.execute("""
        UPDATE service_stats
        SET total_failures = total_failures + ?,
            failure_rate   = ?,
            last_updated   = ?
        WHERE service = ?
    """, (
        1 if outcome == "failure" else 0,
        rate,
        datetime.now(timezone.utc).isoformat(),
        service
    ))

    conn.commit()
    conn.close()


def get_failure_rate(service: str) -> float:
    """Return rolling-window failure rate for a service."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT outcome FROM deployments
        WHERE service = ? AND outcome IN ('success', 'failure')
        ORDER BY id DESC LIMIT 10
    """, (service,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return 0.0

    failures = sum(1 for r in rows if r["outcome"] == "failure")
    return failures / len(rows)


def get_recent_deployments(limit: int = 50) -> list:
    """Return recent deployments as list of dicts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM deployments
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_deployment_by_id(dep_id: int) -> dict | None:
    """Get a single deployment by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deployments WHERE id = ?", (dep_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_service_stats() -> list:
    """Return failure stats for all services."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM service_stats ORDER BY failure_rate DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Initialize DB on import
init_db()
