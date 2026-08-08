"""SQLite 存储层：替代原 MongoDB（pymongo）。

原仓库用 pymongo 存 dance3.songs 集合。本模块改为 SQLite 单文件
dance3.sqlite3，每首歌一条记录（完整 JSON），并用 info_done /
beatmaps_done / downloaded 三个标记支持断点续跑（各步只处理未完成的记录）。
"""
from __future__ import annotations

import json
import sqlite3
import time

DB_PATH = "dance3.sqlite3"


def get_conn(path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS songs (
            music_id      INTEGER PRIMARY KEY,
            goods_id      INTEGER,
            goods_name    TEXT,
            data          TEXT NOT NULL,
            info_done     INTEGER NOT NULL DEFAULT 0,
            beatmaps_done INTEGER NOT NULL DEFAULT 0,
            downloaded    INTEGER NOT NULL DEFAULT 0,
            updated_at    TEXT
        )
        """
    )
    conn.commit()
    return conn


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def upsert_song(conn: sqlite3.Connection, record: dict) -> bool:
    """1 步：按 MusicID 去重写入/更新歌曲列表数据。返回 True 表示新增。"""
    mid = int(record["MusicID"])
    exists = conn.execute("SELECT 1 FROM songs WHERE music_id=?", (mid,)).fetchone()
    conn.execute(
        """
        INSERT INTO songs(music_id, goods_id, goods_name, data, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(music_id) DO UPDATE SET
            goods_id=excluded.goods_id,
            goods_name=excluded.goods_name,
            data=excluded.data,
            updated_at=excluded.updated_at
        """,
        (mid, record.get("GoodsID"), record.get("GoodsName"),
         json.dumps(record, ensure_ascii=False), _now()),
    )
    conn.commit()
    return exists is None


def load(conn: sqlite3.Connection, music_id: int) -> dict:
    row = conn.execute("SELECT data FROM songs WHERE music_id=?", (music_id,)).fetchone()
    return json.loads(row["data"]) if row else None


def save(conn: sqlite3.Connection, music_id: int, record: dict, *,
         info_done=None, beatmaps_done=None, downloaded=None) -> None:
    """更新记录 data 及可选进度标记。"""
    sets, args = ["data=?", "updated_at=?"], [json.dumps(record, ensure_ascii=False), _now()]
    if info_done is not None:
        sets.append("info_done=?"); args.append(1 if info_done else 0)
    if beatmaps_done is not None:
        sets.append("beatmaps_done=?"); args.append(1 if beatmaps_done else 0)
    if downloaded is not None:
        sets.append("downloaded=?"); args.append(1 if downloaded else 0)
    args.append(music_id)
    conn.execute(f"UPDATE songs SET {', '.join(sets)} WHERE music_id=?", args)
    conn.commit()


_FLAG_COLS = {"info_done": "info_done", "beatmaps_done": "beatmaps_done",
              "downloaded": "downloaded"}


def iter_pending(conn: sqlite3.Connection, flag: str):
    """迭代 flag=0 的记录，yield (music_id, record_dict)。"""
    col = _FLAG_COLS[flag]
    for row in conn.execute(f"SELECT music_id, data FROM songs WHERE {col}=0 ORDER BY music_id"):
        yield int(row["music_id"]), json.loads(row["data"])


def count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]


def dump_all(conn: sqlite3.Connection) -> dict:
    """导出 {GoodsID: record}，与原 dumps_infos.py 一致。"""
    out = {}
    for row in conn.execute("SELECT data FROM songs ORDER BY music_id"):
        rec = json.loads(row["data"])
        out[rec.get("GoodsID")] = rec
    return out