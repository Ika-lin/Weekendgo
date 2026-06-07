"""
Structured user profile service.

Mock data is fine, but the agent should still consume stable product data
instead of re-summarizing preferences in every prompt.
"""
from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from models import ConsumptionRecord, User, UserProfile


VISIT_SOURCES = {"dinein", "deal", "review", "movie", "hotel"}
TASTE_SOURCES = {"dinein", "deal", "review", "delivery"}
SPENDING_SOURCES = {"dinein", "deal", "review", "delivery", "movie", "hotel"}
INTEREST_SOURCES = {"search"}
MOBILITY_SOURCES = {"bike"}
CATEGORY_WEIGHTS = {
    "dinein": 1.0,
    "deal": 1.0,
    "review": 1.0,
    "movie": 0.8,
    "hotel": 0.7,
    "delivery": 0.45,
    "search": 0.25,
    "bike": 0.0,
}


def get_structured_profile(user_id: str = "u_demo_001") -> dict[str, Any]:
    user_id = user_id or "u_demo_001"
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    user = User.query.filter_by(user_id=user_id).first()
    records = (
        ConsumptionRecord.query.filter_by(user_id=user_id)
        .order_by(ConsumptionRecord.date.desc())
        .limit(80)
        .all()
    )

    inferred = _infer_from_records(records)
    stored = profile.to_dict() if profile else {}

    return {
        "userId": user_id,
        "nickname": stored.get("nickname") or (user.nickname if user else user_id),
        "location": user.location if user else "上海",
        "favoriteCategories": stored.get("favoriteCategories") or inferred["favoriteCategories"],
        "favoriteDistricts": stored.get("favoriteDistricts") or inferred["favoriteDistricts"],
        "favoriteTags": stored.get("favoriteTags") or inferred["favoriteTags"],
        "avgSpending": stored.get("avgSpending") or inferred["avgSpending"],
        "totalVisits": stored.get("totalVisits") or inferred["totalVisits"],
        "preferredTime": stored.get("preferredTime") or inferred["preferredTime"],
        "soloRatio": stored.get("soloRatio", inferred["soloRatio"]),
        "socialRatio": stored.get("socialRatio", inferred["socialRatio"]),
        "ratingAvg": stored.get("ratingAvg") or inferred["ratingAvg"],
        "personaSummary": stored.get("personaSummary") or inferred["personaSummary"],
        "personaTags": stored.get("personaTags") or inferred["personaTags"],
        "socialStyle": stored.get("socialStyle") or inferred["socialStyle"],
        "groupSizePreference": stored.get("groupSizePreference") or inferred["groupSizePreference"],
        "dietary": stored.get("dietary") or [],
        "mobility": stored.get("mobility") or "",
        "budgetComfort": stored.get("budgetComfort") or 0,
        "freeSlots": stored.get("freeSlots") or [],
        "rawRecordCount": len(records),
        "interestCategories": inferred.get("interestCategories", []),
        "sourceBreakdown": inferred.get("sourceBreakdown", {}),
        "mobilitySignals": inferred.get("mobilitySignals", {}),
        "homeArea": stored.get("homeArea") or _infer_location_area(records, "家"),
        "workArea": stored.get("workArea") or _infer_location_area(records, "公司"),
    }


def compact_profile_text(profile: dict[str, Any]) -> str:
    cats = _label_counts(profile.get("favoriteCategories", []), "category")
    districts = _label_counts(profile.get("favoriteDistricts", []), "district")
    tags = "、".join((profile.get("favoriteTags") or [])[:5]) or "暂无明显标签"
    return (
        f"{profile.get('nickname')}：偏好 {cats or '未明'}，常去 {districts or '未明'}，"
        f"人均约{int(profile.get('avgSpending') or 0)}元，常在{profile.get('preferredTime') or '下午'}出门，"
        f"标签 {tags}。{profile.get('personaSummary') or ''}"
    ).strip()


def merge_group_profiles(user_ids: list[str]) -> dict[str, Any]:
    profiles = [get_structured_profile(uid) for uid in user_ids]
    category_counter: Counter[str] = Counter()
    district_counter: Counter[str] = Counter()
    budgets = []
    conflicts = []

    for p in profiles:
        for item in p.get("favoriteCategories", []):
            category_counter[item.get("category", "")] += item.get("count", 1)
        for item in p.get("favoriteDistricts", []):
            district_counter[item.get("district", "")] += item.get("count", 1)
        if p.get("avgSpending"):
            budgets.append(float(p["avgSpending"]))

    social_styles = {p.get("socialStyle") for p in profiles if p.get("socialStyle")}
    if len(social_styles) > 1:
        conflicts.append("成员社交偏好不同，需要安排可聊天但不吵闹的空间")

    avg_budget = int(mean(budgets)) if budgets else 150
    preferred_categories = [c for c, _ in category_counter.most_common(3) if c]
    preferred_areas = [d for d, _ in district_counter.most_common(3) if d]

    return {
        "profiles": profiles,
        "preferredCategories": preferred_categories,
        "preferredAreas": preferred_areas,
        "avgBudget": avg_budget,
        "conflicts": conflicts,
        "summary": "；".join(compact_profile_text(p) for p in profiles),
    }


def _infer_from_records(records: list[ConsumptionRecord]) -> dict[str, Any]:
    if not records:
        return {
            "favoriteCategories": [],
            "favoriteDistricts": [],
            "favoriteTags": [],
            "avgSpending": 120,
            "totalVisits": 0,
            "preferredTime": "下午",
            "soloRatio": 0.5,
            "socialRatio": 0.5,
            "ratingAvg": 4.3,
            "personaSummary": "新用户画像还在建立中，可以先根据本次输入推荐。",
            "personaTags": ["新用户"],
            "socialStyle": "中等",
            "groupSizePreference": 2,
            "interestCategories": [],
            "sourceBreakdown": {},
            "mobilitySignals": {},
        }

    cats: Counter[str] = Counter()
    interest_cats: Counter[str] = Counter()
    times: Counter[str] = Counter()
    tags: Counter[str] = Counter()
    districts: Counter[str] = Counter()
    source_breakdown: Counter[str] = Counter()
    mobility_signals: Counter[str] = Counter()
    amounts = []
    ratings = []
    social_count = 0
    visit_count = 0

    poi_district_by_name = _poi_district_lookup([r.poi_id for r in records])

    for record in records:
        source = record.source or "dinein"
        source_breakdown[source] += 1
        weight = CATEGORY_WEIGHTS.get(source, 0.5)

        if record.category:
            if source in INTEREST_SOURCES:
                interest_cats[record.category] += 1
            elif weight > 0:
                cats[record.category] += weight

        if record.time_of_day and source not in INTEREST_SOURCES and source not in MOBILITY_SOURCES:
            times[record.time_of_day] += 1

        for tag in record.tags or []:
            if source in TASTE_SOURCES or source in INTEREST_SOURCES:
                tags[tag] += weight or 0.2

        district = poi_district_by_name.get(record.poi_id)
        if district and source in VISIT_SOURCES:
            districts[district] += 1

        if source in SPENDING_SOURCES and record.amount and record.amount > 0:
            amounts.append(record.amount)

        if record.rating:
            ratings.append(record.rating)

        if source in VISIT_SOURCES:
            visit_count += 1
            if record.with_friends:
                social_count += 1

        if source in MOBILITY_SOURCES:
            mobility_signals["bikeTrips"] += 1
            if record.location_context:
                mobility_signals[record.location_context] += 1

    total = max(visit_count, 1)
    favorite_categories = [
        {"category": name, "count": round(count, 1), "avgAmount": _avg_amount(records, name)}
        for name, count in cats.most_common(5)
    ]

    top_cat = cats.most_common(1)[0][0] if cats else "本地生活"
    top_area = districts.most_common(1)[0][0] if districts else "上海"
    avg_spending = round(mean(amounts), 1) if amounts else 120

    return {
        "favoriteCategories": favorite_categories,
        "favoriteDistricts": [{"district": k, "count": v} for k, v in districts.most_common(5)],
        "favoriteTags": [k for k, _ in tags.most_common(8)],
        "interestCategories": [{"category": k, "count": v} for k, v in interest_cats.most_common(5)],
        "avgSpending": avg_spending,
        "totalVisits": visit_count,
        "preferredTime": times.most_common(1)[0][0] if times else "下午",
        "soloRatio": round((total - social_count) / total, 2),
        "socialRatio": round(social_count / total, 2),
        "ratingAvg": round(mean(ratings), 1) if ratings else 4.3,
        "personaSummary": f"常在{top_area}活动，偏好{top_cat}，人均消费约{int(avg_spending)}元。",
        "personaTags": [top_cat, f"{top_area}常客"],
        "socialStyle": "社交型" if social_count / total >= 0.6 else "独处友好",
        "groupSizePreference": 3 if social_count / total >= 0.6 else 2,
        "sourceBreakdown": dict(source_breakdown),
        "mobilitySignals": dict(mobility_signals),
    }


def _avg_amount(records: list[ConsumptionRecord], category: str) -> int:
    values = [
        r.amount for r in records
        if r.category == category
        and (r.source or "dinein") in SPENDING_SOURCES
        and r.amount
        and r.amount > 0
    ]
    return int(mean(values)) if values else 0


def _poi_district_lookup(poi_ids: list[str]) -> dict[str, str]:
    from models import POI

    pois = POI.query.filter(POI.poi_id.in_(poi_ids)).all() if poi_ids else []
    return {p.poi_id: p.district for p in pois}


def _label_counts(items: list[dict], key: str) -> str:
    return "、".join(item.get(key, "") for item in items[:3] if item.get(key))


def _infer_location_area(records, keyword: str) -> str:
    """从消费记录的 location_context 推断家/公司所在区域"""
    from collections import Counter
    areas = Counter()
    # 匹配 location_context 含有关键词的记录
    matching = [r for r in records if keyword in (r.location_context or "").lower()]
    # 从匹配记录的 POI 中提取区域
    for r in matching:
        poi = _lookup_poi(r.poi_id)
        if poi and poi.district:
            areas[poi.district] += 1
    # 如果匹配记录没有 POI 区域（外卖等），用所有记录的 POI 区域作为参考
    if not areas:
        for r in records:
            poi = _lookup_poi(r.poi_id)
            if poi and poi.district:
                areas[poi.district] += 0.5  # 弱权重
    return areas.most_common(1)[0][0] if areas else ""


def _lookup_poi(poi_id: str):
    if not poi_id:
        return None
    from models import POI
    return POI.query.filter_by(poi_id=poi_id).first()
