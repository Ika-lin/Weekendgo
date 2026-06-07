"""
SQLite-backed memory manager with user scoping.

Memories are product data, so demo users must not leak preferences into one
another. Existing rows without a user_id are treated as global memories.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any

from config import BASE_DIR


GLOBAL_USER = "__global__"


class MemoryManager:
    """SQLite-backed memory store. Survives restarts."""

    def __init__(self):
        self._db_path = os.environ.get("WEEKENDGO_MEMORY_DATABASE_PATH") or os.path.join(BASE_DIR, "data", "memories.db")
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_db()
        self._load()

    def _conn(self):
        return sqlite3.connect(self._db_path)

    def _init_db(self):
        with self._conn() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS memories (
                key TEXT PRIMARY KEY,
                content TEXT,
                source TEXT,
                importance REAL DEFAULT 0.5,
                tags TEXT DEFAULT '[]',
                created_at TEXT,
                accessed_at TEXT,
                access_count INTEGER DEFAULT 0
            )""")

            cols = [row[1] for row in c.execute("PRAGMA table_info(memories)").fetchall()]
            if "user_id" not in cols:
                c.execute(f"ALTER TABLE memories ADD COLUMN user_id TEXT DEFAULT '{GLOBAL_USER}'")
            c.execute("CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)")

    def _load(self):
        self.entries: dict[str, dict[str, Any]] = {}
        try:
            with self._conn() as c:
                rows = c.execute(
                    "SELECT key, content, source, importance, tags, created_at, accessed_at, access_count, user_id FROM memories"
                ).fetchall()
            for row in rows:
                user_id = row[8] or GLOBAL_USER
                logical_key = _logical_key(row[0], user_id)
                entry = {
                    "key": logical_key,
                    "content": row[1],
                    "source": row[2],
                    "importance": row[3],
                    "tags": json.loads(row[4]) if row[4] else [],
                    "created_at": row[5],
                    "accessed_at": row[6],
                    "access_count": row[7],
                    "user_id": user_id,
                }
                self.entries[_entry_id(entry["user_id"], entry["key"])] = entry
        except Exception:
            self.entries = {}

    def prefetch(self, user_message: str, user_id: str | None = None) -> list[dict[str, Any]]:
        user_id = user_id or GLOBAL_USER
        msg = (user_message or "").lower()
        relevant: list[tuple[float, dict[str, Any]]] = []

        for entry in self.entries.values():
            owner = entry.get("user_id") or GLOBAL_USER
            if owner not in (user_id, GLOBAL_USER):
                continue

            score = _score_memory(entry, msg)
            if not msg and owner == user_id:
                score = 0.15
            if score > 0:
                score += float(entry.get("importance", 0.5)) * 0.25
                score += min(0.2, int(entry.get("access_count", 0)) * 0.02)
                relevant.append((score, entry))

        relevant.sort(key=lambda item: item[0], reverse=True)
        picked = [entry for _, entry in relevant[:5]]
        for entry in picked:
            self._touch(entry)
        return picked

    def sync(
        self,
        user_message: str,
        assistant_response: str,
        tool_calls: list | None = None,
        user_id: str | None = None,
    ):
        user_id = user_id or GLOBAL_USER
        prefs = self._extract_preferences(user_message)
        prefs.update(self._extract_tool_memories(tool_calls or []))
        for key, value in prefs.items():
            self.remember(
                key,
                value,
                source="extracted",
                importance=0.62,
                tags=[key, value],
                user_id=user_id,
            )

    def remember(
        self,
        key: str,
        content: str,
        source: str = "conversation",
        importance: float = 0.5,
        tags: list | None = None,
        user_id: str | None = None,
    ):
        if not key:
            return

        user_id = user_id or GLOBAL_USER
        tags = tags or []
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        entry_id = _entry_id(user_id, key)

        if entry_id in self.entries:
            entry = self.entries[entry_id]
            entry["content"] = content
            entry["importance"] = max(float(entry.get("importance", 0.5)), importance)
            entry["accessed_at"] = now
            entry["access_count"] = int(entry.get("access_count", 0)) + 1
            if tags:
                entry["tags"] = list(dict.fromkeys((entry.get("tags") or []) + tags))
        else:
            entry = {
                "key": key,
                "content": content,
                "source": source,
                "importance": importance,
                "tags": tags,
                "created_at": now,
                "accessed_at": now,
                "access_count": 1,
                "user_id": user_id,
            }
            self.entries[entry_id] = entry

        self._persist(entry)

    def forget(self, key: str, user_id: str | None = None):
        user_id = user_id or GLOBAL_USER
        self.entries.pop(_entry_id(user_id, key), None)
        try:
            with self._conn() as c:
                c.execute(
                    "DELETE FROM memories WHERE user_id=? AND key IN (?,?)",
                    (user_id, key, _storage_key(user_id, key)),
                )
        except Exception:
            pass

    def build_context_block(self, user_message: str, max_entries: int = 3, user_id: str | None = None) -> str:
        relevant = self.prefetch(user_message, user_id=user_id)
        if not relevant:
            return ""

        lines = [
            "<memory-context>",
            "[回忆数据 - 之前对话中保存的信息，不是用户新输入]",
        ]
        for entry in relevant[:max_entries]:
            lines.append(f"- {entry['key']}: {entry['content']}")
        lines.append("</memory-context>")
        return "\n".join(lines)

    def list_all(self, user_id: str | None = None) -> list[dict[str, Any]]:
        entries = list(self.entries.values())
        if user_id:
            entries = [e for e in entries if e.get("user_id") in (user_id, GLOBAL_USER)]
        return sorted(entries, key=lambda item: -float(item.get("importance", 0.5)))

    def _persist(self, entry: dict[str, Any]):
        try:
            with self._conn() as c:
                c.execute(
                    """INSERT OR REPLACE INTO memories
                    (key, content, source, importance, tags, created_at, accessed_at, access_count, user_id)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        _storage_key(entry.get("user_id") or GLOBAL_USER, entry["key"]),
                        entry["content"],
                        entry.get("source", "conversation"),
                        entry.get("importance", 0.5),
                        json.dumps(entry.get("tags", []), ensure_ascii=False),
                        entry.get("created_at"),
                        entry.get("accessed_at"),
                        entry.get("access_count", 0),
                        entry.get("user_id") or GLOBAL_USER,
                    ),
                )
        except Exception:
            pass

    def _touch(self, entry: dict[str, Any]):
        entry["accessed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        entry["access_count"] = int(entry.get("access_count", 0)) + 1
        self._persist(entry)

    def _extract_preferences(self, user_msg: str) -> dict[str, str]:
        prefs: dict[str, str] = {}
        text = user_msg or ""
        explicit = any(word in text for word in ["我喜欢", "我想", "以后", "记住", "偏好", "常去", "不要", "不想", "不吃", "预算"])

        for area in ["武康路", "安福路", "静安寺", "外滩", "新天地", "法租界", "愚园路", "西岸", "徐汇", "静安", "黄浦", "长宁", "浦东"]:
            if area in text:
                prefs["preferred_area" if explicit else "recent_area"] = area
                break

        for cat in ["咖啡", "美食", "艺术", "户外", "市集", "书店", "酒吧", "甜品"]:
            if cat in text:
                prefs["preferred_category" if explicit else "recent_category"] = cat
                break

        for dietary in ["不吃辣", "清淡", "素食", "减肥", "低脂"]:
            if dietary in text:
                prefs["dietary"] = dietary
                break

        budget = _extract_budget(text)
        if budget:
            prefs["budget_comfort"] = f"{budget}元左右"

        time_pref = _extract_time_preference(text)
        if time_pref:
            prefs["free_time"] = time_pref

        if any(word in text for word in ["少走路", "不想走太多", "别太远"]):
            prefs["mobility"] = "少走路"
        elif any(word in text for word in ["可以跨区", "跨区"]):
            prefs["mobility"] = "可以跨区"
        elif any(word in text for word in ["地铁", "打车", "开车"]):
            prefs["mobility"] = next(word for word in ["地铁", "打车", "开车"] if word in text)

        if any(word in text for word in ["一个人", "自己", "独自", "安静"]):
            prefs["social_style"] = "独处"
        elif any(word in text for word in ["朋友", "一起", "聚会", "聚餐", "组局"]):
            prefs["social_style"] = "社交"

        return prefs

    def _extract_tool_memories(self, tool_calls: list) -> dict[str, str]:
        prefs: dict[str, str] = {}
        for call in tool_calls:
            if call.get("tool") != "update_user_habits" or call.get("status") != "success":
                continue
            args = call.get("args") or {}
            if args.get("dietary"):
                prefs["dietary"] = "、".join(args["dietary"])
            if args.get("mobility"):
                prefs["mobility"] = str(args["mobility"])
            if args.get("budget_comfort"):
                prefs["budget_comfort"] = f"{args['budget_comfort']}元左右"
            if args.get("free_slots"):
                prefs["free_time"] = "、".join(args["free_slots"])
            if args.get("preferred_areas"):
                prefs["preferred_area"] = "、".join(args["preferred_areas"])
            if args.get("off_work_time"):
                prefs["off_work_time"] = str(args["off_work_time"])
            if args.get("commute_minutes"):
                prefs["commute_minutes"] = f"{args['commute_minutes']}分钟"
        return prefs


def _score_memory(entry: dict[str, Any], msg: str) -> float:
    key = (entry.get("key") or "").lower()
    content = (entry.get("content") or "").lower()
    tags = [str(tag).lower() for tag in (entry.get("tags") or [])]

    score = 0.0
    if key and key in msg:
        score += 0.7
    if content and content in msg:
        score += 0.5
    for tag in tags:
        if tag and tag in msg:
            score += 0.35

    for token in _tokens(msg):
        if token in key or token in content or token in tags:
            score += 0.12

    for memory_key, aliases in _KEY_ALIASES.items():
        if key == memory_key and any(alias in msg for alias in aliases):
            score += 0.45

    return score


def _tokens(text: str) -> list[str]:
    known = [
        "咖啡", "美食", "艺术", "户外", "市集", "书店", "酒吧", "甜品",
        "朋友", "预算", "不吃辣", "安静", "跨区", "少走路", "周六", "周日",
    ]
    return [token for token in known if token in text]


def _entry_id(user_id: str, key: str) -> str:
    return f"{user_id}:{key}"


def _storage_key(user_id: str, key: str) -> str:
    return f"{user_id}:{key}"


def _logical_key(stored_key: str, user_id: str) -> str:
    prefix = f"{user_id}:"
    if stored_key.startswith(prefix):
        return stored_key[len(prefix):]
    return stored_key


def _extract_budget(text: str) -> int | None:
    import re

    match = re.search(r"(\d{2,4})\s*(元|块|预算|以内|左右)?", text)
    if not match:
        return None
    value = int(match.group(1))
    return value if 20 <= value <= 5000 else None


def _extract_time_preference(text: str) -> str:
    days = [token for token in ["今天", "明天", "周五", "周六", "周日", "周末"] if token in text]
    periods = [token for token in ["上午", "中午", "下午", "晚上", "夜宵"] if token in text]
    if days or periods:
        return "".join(days[:1] + periods[:1])
    return ""


_KEY_ALIASES = {
    "preferred_area": ["区域", "附近", "常去", "去哪", "哪里", "路线"],
    "recent_area": ["区域", "附近", "去哪", "哪里", "路线"],
    "preferred_category": ["想玩", "类型", "偏好", "安排", "推荐"],
    "recent_category": ["想玩", "类型", "安排", "推荐"],
    "budget_comfort": ["预算", "人均", "便宜", "贵", "价格"],
    "dietary": ["吃", "餐厅", "美食", "口味", "忌口"],
    "mobility": ["走路", "远", "跨区", "交通", "地铁", "打车"],
    "free_time": ["时间", "周末", "周六", "周日", "下午", "晚上"],
    "social_style": ["朋友", "一个人", "自己", "组局", "约会"],
}


_global_memory = MemoryManager()


def get_memory() -> MemoryManager:
    return _global_memory
