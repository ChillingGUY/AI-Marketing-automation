# -*- coding: utf-8 -*-
"""
数据库表定义与操作
表：trends, scripts, videos, agents_log
"""

import sqlite3
from typing import Any, Optional

from .session import get_connection


def init_tables(conn: Optional[sqlite3.Connection] = None) -> None:
    """创建所有表"""
    owns = conn is None
    conn = conn or get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT DEFAULT 'TikTok',
            video_url TEXT,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            topic TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS scripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            hook TEXT,
            script TEXT,
            scene TEXT,
            industry TEXT,
            trend_id INTEGER,
            score REAL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (trend_id) REFERENCES trends(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            script_id INTEGER,
            video_url TEXT,
            score REAL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (script_id) REFERENCES scripts(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS agents_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT,
            task TEXT,
            result TEXT,
            time TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    if owns:
        conn.close()


def insert_trend(
    platform: str = "TikTok",
    video_url: str = "",
    likes: int = 0,
    comments: int = 0,
    views: int = 0,
    topic: str = "",
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """插入趋势记录，返回 id"""
    owns = conn is None
    conn = conn or get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO trends (platform, video_url, likes, comments, views, topic)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (platform, video_url, likes, comments, views, topic),
    )
    conn.commit()
    rid = cur.lastrowid
    if owns:
        conn.close()
    return rid or 0


def insert_script(
    title: str = "",
    hook: str = "",
    script: str = "",
    scene: str = "",
    industry: str = "",
    trend_id: Optional[int] = None,
    score: Optional[float] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """插入脚本记录，返回 id"""
    owns = conn is None
    conn = conn or get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO scripts (title, hook, script, scene, industry, trend_id, score)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (title, hook, script, scene, industry, trend_id, score),
    )
    conn.commit()
    rid = cur.lastrowid
    if owns:
        conn.close()
    return rid or 0


def insert_video(
    script_id: int,
    video_url: str = "",
    score: Optional[float] = None,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """插入视频记录，返回 id"""
    owns = conn is None
    conn = conn or get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO videos (script_id, video_url, score) VALUES (?, ?, ?)""",
        (script_id, video_url, score),
    )
    conn.commit()
    rid = cur.lastrowid
    if owns:
        conn.close()
    return rid or 0


def insert_agent_log(
    agent_name: str,
    task: str,
    result: Any,
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """插入 Agent 日志"""
    owns = conn is None
    conn = conn or get_connection()
    cur = conn.cursor()
    res_str = str(result) if not isinstance(result, str) else result
    cur.execute(
        """INSERT INTO agents_log (agent_name, task, result) VALUES (?, ?, ?)""",
        (agent_name, task[:500] if task else "", res_str[:2000] if res_str else ""),
    )
    conn.commit()
    rid = cur.lastrowid
    if owns:
        conn.close()
    return rid or 0


def list_trends(limit: int = 50, conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    """列出趋势记录"""
    owns = conn is None
    conn = conn or get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trends ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    out = [dict(r) for r in rows]
    if owns:
        conn.close()
    return out


def list_scripts(limit: int = 50, conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    """列出脚本记录"""
    owns = conn is None
    conn = conn or get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scripts ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    out = [dict(r) for r in rows]
    if owns:
        conn.close()
    return out


def list_scripts_with_scores(limit: int = 50, conn: Optional[sqlite3.Connection] = None) -> list[dict]:
    """列出脚本及其评分（score 非空优先）"""
    owns = conn is None
    conn = conn or get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT id, title, hook, script, scene, industry, trend_id, score, created_at
           FROM scripts ORDER BY score IS NULL, score DESC, id DESC LIMIT ?""",
        (limit,),
    )
    rows = cur.fetchall()
    out = [dict(r) for r in rows]
    if owns:
        conn.close()
    return out


def update_script_score(script_id: int, score: float, conn: Optional[sqlite3.Connection] = None) -> None:
    """更新脚本评分"""
    owns = conn is None
    conn = conn or get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE scripts SET score = ? WHERE id = ?", (score, script_id))
    conn.commit()
    if owns:
        conn.close()


def update_script_content(
    script_id: int,
    title: str | None = None,
    hook: str | None = None,
    script: str | None = None,
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """更新脚本内容（脚本编辑）"""
    owns = conn is None
    conn = conn or get_connection()
    cur = conn.cursor()
    updates = []
    params = []
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if hook is not None:
        updates.append("hook = ?")
        params.append(hook)
    if script is not None:
        updates.append("script = ?")
        params.append(script)
    if not updates:
        return
    params.append(script_id)
    cur.execute(f"UPDATE scripts SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    if owns:
        conn.close()
