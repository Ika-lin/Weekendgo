"""
Deterministic planning service for Weekendgo.

The agent remains conversational, but itinerary construction is product logic:
retrieve candidates, rank them, calculate budget/time, and return a stable
trip schema the frontend can render and save.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

import json as _json
from agent.response_schema import safe_json_result, tool_log
from models import db, POI, Trip, TripStop


DEFAULT_START = "14:00"


def find_places(slots: dict[str, Any], profile: dict[str, Any], limit: int = 8) -> tuple[list[dict], list[dict]]:
    query = POI.query.filter(POI.business_status == "open")
    category = slots.get("category")
    area = slots.get("area")
    budget = slots.get("budget")

    if category:
        if category == "亲子":
            # 亲子不是独立类别，筛选有儿童设施或亲子标签的 POI
            from sqlalchemy import or_
            query = query.filter(or_(
                POI.facilities.contains("儿童区"),
                POI.tags.contains("亲子"),
                POI.suitable_for.contains("亲子"),
                POI.category.in_(["户外", "美食", "甜品"]),
            ))
        else:
            query = query.filter(POI.category == category)
    if area:
        query = query.filter((POI.district == area) | (POI.neighborhood == area))
    if budget:
        query = query.filter(POI.price_per_capita <= max(int(budget), 60))

    candidates = query.limit(80).all()
    if len(candidates) < 3:
        candidates = POI.query.filter(POI.business_status == "open").limit(120).all()

    ranked = sorted(
        (p for p in candidates),
        key=lambda poi: _score_poi(poi, slots, profile),
        reverse=True,
    )

    places = [_place_card(p, _score_poi(p, slots, profile)) for p in ranked[:limit]]
    tool_calls = [tool_log(
        "rank_pois",
        args={"slots": slots, "profileUserId": profile.get("userId"), "limit": limit},
        result={"count": len(places), "topPoiIds": [p["poiId"] for p in places[:5]]},
    )]
    return places, tool_calls


def build_trip_plan(
    user_id: str,
    message: str,
    slots: dict[str, Any],
    profile: dict[str, Any],
    *,
    group_context: dict[str, Any] | None = None,
) -> tuple[dict, list[dict]]:
    places, tool_calls = find_places(slots, profile, limit=10)
    selected = _select_route(places, slots)

    if len(selected) < 2:
        return _empty_plan(slots), tool_calls

    start_time = _start_time(slots)
    stops = []
    total_minutes = _to_minutes(start_time)
    walk_pattern = [0, 8, 10, 12]

    for index, place in enumerate(selected[:4], start=1):
        duration = _duration_for(place["category"])
        walk = walk_pattern[min(index - 1, len(walk_pattern) - 1)]
        if index > 1:
            total_minutes += walk
        begin = _format_minutes(total_minutes)
        end = _format_minutes(total_minutes + duration)
        total_minutes += duration
        stops.append({
            "order": index,
            "time": begin,
            "endTime": end,
            "name": place["name"],
            "poiId": place["poiId"],
            "category": place["category"],
            "address": place["address"],
            "lat": place.get("lat"),
            "lng": place.get("lng"),
            "pricePerCapita": place["pricePerCapita"],
            "rating": place["rating"],
            "durationMinutes": duration,
            "walkFromPrevious": walk,
            "tags": place.get("tags", [])[:4],
            "reason": _stop_reason(place, profile, group_context),
            "queueInfo": _queue_check(place, begin, slots.get("partySize", 2)),
        })

    total_budget = sum(s["pricePerCapita"] for s in stops)
    total_walk = sum(s["walkFromPrevious"] for s in stops)
    title = _plan_title(stops, slots, group_context)
    risk_reminders = _risk_reminders(stops, slots, total_budget, total_walk, group_context)
    execution_actions = _execution_actions(stops, slots)
    plan = {
        "planId": f"plan_{uuid.uuid4().hex[:8]}",
        "userId": user_id,
        "title": title,
        "type": _plan_type(stops),
        "city": profile.get("location", "上海"),
        "status": "draft",
        "source": "agent_state_machine",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "totalDuration": _duration_text(_to_minutes(start_time), total_minutes),
        "totalBudget": f"人均约{total_budget}元",
        "budgetValue": total_budget,
        "transportMode": "步行 + 必要时短途打车" if total_walk > 24 else "全程步行",
        "totalWalkMinutes": total_walk,
        "stops": stops,
        "fitReasons": _fit_reasons(profile, slots, group_context),
        "conflicts": (group_context or {}).get("conflicts", []),
        "riskReminders": risk_reminders,
        "executionActions": execution_actions,
        "confirmMessage": _confirm_message(stops, slots, execution_actions),
        "request": message,
    }

    tool_calls.append(tool_log(
        "generate_structured_trip",
        args={"selectedPoiIds": [s["poiId"] for s in stops], "startTime": start_time},
        result={"planId": plan["planId"], "totalBudget": plan["totalBudget"]},
    ))
    tool_calls.append(tool_log(
        "check_plan_risks",
        args={"partySize": slots.get("partySize", 2), "totalWalkMinutes": total_walk},
        result={"riskCount": len(risk_reminders), "executionActionCount": len(execution_actions)},
    ))
    return plan, tool_calls


def save_plan(user_id: str, plan: dict[str, Any]) -> tuple[dict | None, list[dict]]:
    if not plan or not plan.get("stops"):
        return None, [tool_log(
            "save_trip",
            args={"userId": user_id},
            result={},
            status="failed",
            error="没有可保存的行程草稿",
        )]

    trip_id = f"t_{uuid.uuid4().hex[:8]}"
    trip = Trip(
        trip_id=trip_id,
        user_id=user_id,
        plan_id=plan.get("planId", ""),
        title=plan.get("title", "周末出行"),
        city=plan.get("city", "上海"),
        date=time.strftime("%Y-%m-%d"),
        total_budget=plan.get("totalBudget", ""),
        status="planned",
        overview={
            "duration": plan.get("totalDuration"),
            "budgetValue": plan.get("budgetValue"),
            "transportMode": plan.get("transportMode"),
            "totalWalkMinutes": plan.get("totalWalkMinutes"),
            "source": plan.get("source"),
        },
        route_map={"markers": _markers_for(plan.get("stops", []))},
    )
    db.session.add(trip)

    for stop in plan.get("stops", []):
        db.session.add(TripStop(
            stop_id=f"ts_{uuid.uuid4().hex[:8]}",
            trip_id_fk=trip_id,
            poi_id=stop.get("poiId", ""),
            index=stop.get("order", 0),
            time=stop.get("time", ""),
            name=stop.get("name", ""),
            desc=stop.get("reason", ""),
            duration_minutes=stop.get("durationMinutes", 50),
            alternatives={
                "endTime": stop.get("endTime", ""),
                "category": stop.get("category", ""),
                "address": stop.get("address", ""),
                "lat": stop.get("lat"),
                "lng": stop.get("lng"),
                "pricePerCapita": stop.get("pricePerCapita"),
                "rating": stop.get("rating"),
                "walkFromPrevious": stop.get("walkFromPrevious", 0),
                "tags": stop.get("tags", []),
                "queueInfo": stop.get("queueInfo"),
            },
        ))

    db.session.commit()
    saved = trip.to_detail_dict()
    return saved, [tool_log(
        "save_trip",
        args={"userId": user_id, "planId": plan.get("planId")},
        result={"tripId": trip_id, "saved": True},
    )]


def build_plan_reply(plan: dict[str, Any], profile: dict[str, Any]) -> str:
    if not plan.get("stops"):
        return "我暂时没找到足够合适的地点。你可以告诉我想去的区域、预算，或者偏好的活动类型。"

    lines = [
        f"我给你排了一个「{plan['title']}」。",
        f"总时长{plan['totalDuration']}，{plan['totalBudget']}，{plan['transportMode']}。",
        "",
    ]
    for stop in plan["stops"]:
        line = (
            f"{stop['order']}. {stop['time']}-{stop['endTime']} {stop['name']} "
            f"({stop['category']}，¥{stop['pricePerCapita']}/人)"
        )
        qi = stop.get("queueInfo")
        if qi and qi.get("queueRisk") == "high":
            line += f" ⚠️预计排队{qi.get('waitMinutes',0)}分钟"
        elif qi and qi.get("queueRisk") == "medium":
            line += f" ⏳可能等{qi.get('waitMinutes',0)}分钟"
        lines.append(line)
        reason = stop.get("reason", "")
        if qi and qi.get("tip"):
            reason += f" {qi['tip']}"
        lines.append(f"   {reason}")

    if plan.get("conflicts"):
        lines.append("")
        lines.append("我也顺手处理了这些冲突：" + "；".join(plan["conflicts"]))

    lines.append("")
    lines.append("你说“就这个”我就帮你保存到行程里；也可以说“换一家咖啡”或“少走路”。")
    return "\n".join(lines)


def build_places_reply(places: list[dict], slots: dict[str, Any]) -> str:
    if not places:
        return "这次没筛到合适地点，换个区域或放宽预算我再找。"

    target = slots.get("category") or slots.get("area") or "附近"
    lines = [f"我先帮你挑了 {len(places[:5])} 个{target}好去处：", ""]
    for i, place in enumerate(places[:5], start=1):
        lines.append(
            f"{i}. {place['name']} | {place['category']} | ¥{place['pricePerCapita']} | "
            f"{place['rating']}分 | {place.get('district','')}{place.get('neighborhood','')}"
        )
    lines.append("")
    lines.append("想直接变成路线的话，可以说“帮我把前几个安排成下午行程”。")
    return "\n".join(lines)


def _score_poi(poi: POI, slots: dict[str, Any], profile: dict[str, Any]) -> float:
    score = float(poi.rating or 4.0) * 18
    category = slots.get("category")
    area = slots.get("area")
    budget = slots.get("budget") or profile.get("budgetComfort") or profile.get("avgSpending") or 150

    if category and poi.category == category:
        score += 28
    preferred_cats = {c.get("category") for c in profile.get("favoriteCategories", [])}
    if poi.category in preferred_cats:
        score += 16

    if area and (poi.district == area or poi.neighborhood == area):
        score += 22
    preferred_areas = {d.get("district") for d in profile.get("favoriteDistricts", [])}
    if poi.district in preferred_areas:
        score += 10

    favorite_tags = set(profile.get("favoriteTags") or [])
    score += min(12, len(favorite_tags & set(poi.tags or [])) * 4)

    if budget:
        diff = max(0, poi.price_per_capita - int(budget))
        score -= min(25, diff / 8)
        if poi.price_per_capita <= int(budget):
            score += 8

    return round(score, 2)


def _place_card(poi: POI, score: float) -> dict[str, Any]:
    return {
        "poiId": poi.poi_id,
        "name": poi.name,
        "category": poi.category,
        "address": poi.address,
        "lat": poi.lat,
        "lng": poi.lng,
        "district": poi.district,
        "neighborhood": poi.neighborhood,
        "pricePerCapita": poi.price_per_capita,
        "rating": poi.rating,
        "tags": poi.tags or [],
        "score": score,
    }


def _select_route(places: list[dict], slots: dict[str, Any]) -> list[dict]:
    if not places:
        return []

    area = slots.get("area")
    if area:
        same_area = [p for p in places if p.get("district") == area or p.get("neighborhood") == area]
        if len(same_area) >= 2:
            return same_area[:4]

    anchor_area = places[0].get("neighborhood") or places[0].get("district")
    same_area = [p for p in places if p.get("neighborhood") == anchor_area or p.get("district") == places[0].get("district")]
    route = same_area[:4]
    if len(route) < 2:
        route = places[:4]
    return route


def _duration_for(category: str) -> int:
    return {
        "美食": 75,
        "咖啡": 50,
        "艺术": 70,
        "户外": 55,
        "市集": 60,
        "书店": 50,
        "酒吧": 70,
        "甜品": 35,
    }.get(category, 50)


def _stop_reason(place: dict, profile: dict[str, Any], group_context: dict[str, Any] | None) -> str:
    tags = "、".join(place.get("tags", [])[:2])
    if group_context:
        return f"兼顾小组共同偏好，{tags or '评分稳定'}，路线也比较顺。"
    if place["category"] in {c.get("category") for c in profile.get("favoriteCategories", [])}:
        return f"符合你常去的{place['category']}偏好，{tags or '口碑不错'}。"
    return f"评分和位置都合适，{tags or '适合作为这一站'}。"


def _fit_reasons(profile: dict, slots: dict, group_context: dict | None) -> list[str]:
    if group_context:
        reasons = ["根据所有成员画像做了共同偏好聚合"]
        reasons.extend(group_context.get("conflicts", []))
        return reasons
    reasons = [f"参考了{profile.get('nickname')}的消费画像"]
    if slots.get("budget"):
        reasons.append(f"控制在人均{slots['budget']}元左右")
    if slots.get("area"):
        reasons.append(f"优先选择{slots['area']}附近")
    return reasons


def _risk_reminders(
    stops: list[dict],
    slots: dict,
    total_budget: int,
    total_walk: int,
    group_context: dict | None,
) -> list[dict[str, Any]]:
    reminders: list[dict[str, Any]] = []
    party_size = int(slots.get("partySize") or 2)

    for stop in stops:
        qi = stop.get("queueInfo") or {}
        risk = qi.get("queueRisk")
        if risk in ("high", "medium"):
            wait = qi.get("waitMinutes") or 15
            reminders.append({
                "type": "queue",
                "level": "high" if risk == "high" else "medium",
                "title": f"{stop.get('name', '餐厅')}可能需要等位",
                "detail": f"预计等位约{wait}分钟，建议提前排队/预约，或保留同区域备选。",
                "action": "提前排队或预约",
            })

    if total_walk >= 28:
        reminders.append({
            "type": "mobility",
            "level": "medium",
            "title": "步行时间偏长",
            "detail": f"全程步行约{total_walk}分钟，带孩子或老人时建议中间安排休息点，必要时短途打车。",
            "action": "加入休息点",
        })
    elif total_walk >= 18:
        reminders.append({
            "type": "mobility",
            "level": "low",
            "title": "注意体力分配",
            "detail": f"步行约{total_walk}分钟，路线不算远，但最好把咖啡/甜品点作为缓冲。",
            "action": "保留缓冲时间",
        })

    if party_size >= 5:
        reminders.append({
            "type": "party_size",
            "level": "medium",
            "title": "多人同行要确认座位",
            "detail": f"这次预计{party_size}人同行，餐厅最好提前确认大桌和儿童座椅。",
            "action": "确认大桌",
        })

    dietary = "、".join(slots.get("dietary") or [])
    if dietary:
        reminders.append({
            "type": "dietary",
            "level": "medium",
            "title": "饮食偏好需要提前确认",
            "detail": f"已识别到{dietary}诉求，点餐时优先选择清淡/低脂菜，避免重油重辣。",
            "action": "标注口味",
        })

    if slots.get("category") == "亲子" or party_size >= 3:
        reminders.append({
            "type": "child_friendly",
            "level": "medium",
            "title": "亲子场景要留出机动时间",
            "detail": "孩子可能临时累或饿，建议每60-75分钟安排一次可坐下的点位。",
            "action": "加入亲子缓冲",
        })

    if group_context and group_context.get("conflicts"):
        reminders.append({
            "type": "group_conflict",
            "level": "medium",
            "title": "成员偏好存在差异",
            "detail": "已把预算、活动类型和出门节奏做了折中，确认前最好发给群里看一眼。",
            "action": "发给群确认",
        })

    if total_budget >= 260:
        reminders.append({
            "type": "budget",
            "level": "low",
            "title": "预算略高",
            "detail": f"当前人均约{total_budget}元，如果有人只想轻松逛逛，可以把正餐换成轻食/咖啡。",
            "action": "准备低预算替代",
        })

    if not reminders:
        reminders.append({
            "type": "fallback",
            "level": "low",
            "title": "建议保留一个备选点",
            "detail": "路线整体可执行，但周末客流不稳定，最好保留同区域备选餐厅或咖啡。",
            "action": "保留备选",
        })

    return reminders[:5]


def _execution_actions(stops: list[dict], slots: dict) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    party_size = int(slots.get("partySize") or 2)

    for stop in stops:
        category = stop.get("category")
        if category in ("美食", "咖啡", "酒吧"):
            actions.append({
                "type": "reserve_or_queue",
                "label": f"预约/排队 {stop.get('name', '')}",
                "poiId": stop.get("poiId", ""),
                "time": stop.get("time", ""),
                "partySize": party_size,
                "status": "pending_confirmation",
            })
        elif category in ("艺术", "展览", "亲子", "户外"):
            actions.append({
                "type": "check_ticket",
                "label": f"确认门票/开放时间 {stop.get('name', '')}",
                "poiId": stop.get("poiId", ""),
                "time": stop.get("time", ""),
                "partySize": party_size,
                "status": "pending_confirmation",
            })

    actions.append({
        "type": "share_plan",
        "label": "把计划发给同行人确认",
        "status": "pending_confirmation",
    })
    return actions[:5]


def _confirm_message(stops: list[dict], slots: dict, execution_actions: list[dict[str, Any]]) -> str:
    start = stops[0].get("time") if stops else "待定"
    first = stops[0].get("name") if stops else "第一站"
    count = len(execution_actions)
    return f"搞定了，{start}出发，先去{first}。你确认后我可以继续执行{count}个预约/排队/分享动作。"


def _plan_title(stops: list[dict], slots: dict, group_context: dict | None) -> str:
    area = (slots.get("area") or stops[0].get("neighborhood") or stops[0].get("district") or "本地")
    if group_context:
        return f"{area}多人周末协调路线"
    cats = []
    for stop in stops:
        if stop["category"] not in cats:
            cats.append(stop["category"])
    return f"{area}{' + '.join(cats[:2])}闲逛路线"


def _plan_type(stops: list[dict]) -> str:
    cats = [s["category"] for s in stops]
    if "艺术" in cats:
        return "文艺漫步"
    if cats.count("美食") >= 2:
        return "美食探店"
    if "户外" in cats:
        return "城市探索"
    return "周末闲逛"


def _start_time(slots: dict) -> str:
    text = slots.get("timeText", "")
    if "上午" in text:
        return "10:00"
    if "晚上" in text or "夜" in text:
        return "18:00"
    match = text if ":" in text else ""
    return match or DEFAULT_START


def _to_minutes(value: str) -> int:
    try:
        hour, minute = value.split(":")[:2]
        return int(hour) * 60 + int(minute)
    except (ValueError, AttributeError):
        return 14 * 60


def _format_minutes(value: int) -> str:
    value = value % (24 * 60)
    return f"{value // 60:02d}:{value % 60:02d}"


def _duration_text(start: int, end: int) -> str:
    minutes = max(0, end - start)
    return f"约{minutes // 60}小时{minutes % 60}分钟"


def _markers_for(stops: list[dict]) -> list[dict]:
    markers = []
    for stop in stops:
        poi = POI.query.filter_by(poi_id=stop.get("poiId")).first()
        if poi:
            markers.append({
                "stopId": stop.get("poiId"),
                "order": stop.get("order"),
                "name": stop.get("name"),
                "lat": poi.lat,
                "lng": poi.lng,
            })
    return markers


def _empty_plan(slots: dict) -> dict:
    return {
        "planId": f"plan_{uuid.uuid4().hex[:8]}",
        "title": "待补充偏好的周末路线",
        "status": "needs_input",
        "stops": [],
        "needs": ["preference", "area", "budget"],
        "slots": slots,
    }


def _queue_check(place: dict, time_str: str, party_size: int) -> dict | None:
    """对餐厅/咖啡类站点查排队信息."""
    if place.get("category") not in ("美食", "咖啡", "酒吧"):
        return None
    try:
        from agent.tools import _check_availability
        raw = _check_availability({
            "poi_id": place["poiId"],
            "time": time_str,
            "party_size": max(1, int(party_size or 2)),
        })
        return safe_json_result(raw)
    except Exception:
        return None
