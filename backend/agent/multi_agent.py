"""
Group coordinator agent.

The coordinator is code-led: build member profiles, resolve conflicts, then
call the same deterministic planner used by the single-user agent.
"""
from __future__ import annotations

from typing import Any

from agent.intent_router import route_intent
from agent.planning_service import build_plan_reply, build_trip_plan
from agent.profile_service import compact_profile_text, merge_group_profiles


def plan_for_group(user_ids: list[str], message: str, session_id: str | None = None) -> dict[str, Any]:
    user_ids = _dedupe(user_ids)
    if not user_ids:
        return {"reply": "无成员数据", "members": [], "trip": None, "actions": []}

    group = merge_group_profiles(user_ids)
    routed = route_intent(message)
    slots = dict(routed.get("slots", {}))

    if not slots.get("category") and group.get("preferredCategories"):
        slots["category"] = group["preferredCategories"][0]
    if not slots.get("area") and group.get("preferredAreas"):
        slots["area"] = group["preferredAreas"][0]
    if not slots.get("budget"):
        slots["budget"] = max(80, int(group.get("avgBudget") or 150))
    slots["partySize"] = slots.get("partySize") or len(user_ids)

    planning_profile = _group_profile(group)
    group_context = {
        "memberCount": len(user_ids),
        "conflicts": _resolve_conflicts(group),
        "profiles": group["profiles"],
    }
    plan, tool_calls = build_trip_plan(
        user_ids[0],
        message,
        slots,
        planning_profile,
        group_context=group_context,
    )

    reply = _group_reply(plan, group, planning_profile)
    return {
        "reply": reply,
        "members": [
            {
                "userId": p["userId"],
                "nickname": p.get("nickname"),
                "profile": p,
                "summary": compact_profile_text(p),
            }
            for p in group["profiles"]
        ],
        "trip": plan,
        "actions": [
            {"type": "save_group_plan", "label": "确认方案", "status": "ready"},
            {"type": "modify_group_plan", "label": "调整路线", "status": "ready"},
            {"type": "share", "label": "发到群里", "status": "ready"},
        ],
        "toolCalls": tool_calls,
        "intent": "group_plan",
        "metadata": {
            "router": routed,
            "sessionId": session_id,
            "groupPreferences": {
                "preferredCategories": group.get("preferredCategories", []),
                "preferredAreas": group.get("preferredAreas", []),
                "avgBudget": group.get("avgBudget"),
                "conflicts": group_context["conflicts"],
            },
        },
    }


def _group_reply(plan: dict[str, Any], group: dict[str, Any], profile: dict[str, Any]) -> str:
    lines = [
        f"我先把 {len(group['profiles'])} 位成员的画像合并了：",
    ]
    for p in group["profiles"]:
        lines.append(f"- {compact_profile_text(p)}")

    conflicts = _resolve_conflicts(group)
    if conflicts:
        lines.append("")
        lines.append("冲突处理：" + "；".join(conflicts))

    lines.append("")
    lines.append(build_plan_reply(plan, profile))
    return "\n".join(lines)


def _group_profile(group: dict[str, Any]) -> dict[str, Any]:
    categories = [{"category": c, "count": 3} for c in group.get("preferredCategories", [])]
    districts = [{"district": d, "count": 3} for d in group.get("preferredAreas", [])]
    tags = []
    for p in group.get("profiles", []):
        tags.extend(p.get("favoriteTags", [])[:3])

    return {
        "userId": "group",
        "nickname": "群组",
        "location": "上海",
        "favoriteCategories": categories,
        "favoriteDistricts": districts,
        "favoriteTags": list(dict.fromkeys(tags))[:8],
        "avgSpending": group.get("avgBudget") or 150,
        "personaSummary": "多人共同偏好画像",
        "personaTags": ["群规划", "多人协调"],
        "socialStyle": "社交型",
        "groupSizePreference": len(group.get("profiles", [])),
    }


def _resolve_conflicts(group: dict[str, Any]) -> list[str]:
    conflicts = list(group.get("conflicts", []))
    profiles = group.get("profiles", [])
    budgets = [p.get("avgSpending") for p in profiles if p.get("avgSpending")]
    if budgets and max(budgets) - min(budgets) > 120:
        conflicts.append("成员预算差异较大，优先选择可丰俭由人的地点")

    preferred_times = {p.get("preferredTime") for p in profiles if p.get("preferredTime")}
    if len(preferred_times) > 1:
        conflicts.append("成员常用出门时段不同，安排下午到傍晚的折中节奏")

    if not conflicts:
        conflicts.append("成员偏好比较接近，优先保证路线顺和体验差异")
    return conflicts


def _dedupe(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
