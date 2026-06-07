"""
Agent 工具定义 - Claude 式 Function Calling
每个工具包含: name, description, parameters (JSON Schema), execute 函数
"""
import json
import time
import random
from models import db, POI, Event, Trip, TripStop, ConsumptionRecord, Deal, UserProfile, SocialConnection
from collections import Counter

# ═══════════════════════════════════════════
# 工具定义 (OpenAI/Claude function-calling 格式)
# ═══════════════════════════════════════════

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_pois",
            "description": "搜索上海地点的POI数据库。可按类别、区域、商圈、价格、评分、标签筛选。用于发现符合用户偏好的餐厅、咖啡馆、景点等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "类别: 咖啡/美食/艺术/户外/市集/书店/酒吧/甜品, 留空则不限",
                    },
                    "district": {
                        "type": "string",
                        "description": "区域: 徐汇/静安/黄浦/长宁/浦东/虹口/普陀, 留空则不限",
                    },
                    "neighborhood": {
                        "type": "string",
                        "description": "商圈: 武康路/安福路/法租界/新天地/外滩/愚园路/西岸/陆家嘴/衡山路/淮海中路/打浦桥/巨鹿路/永康路",
                    },
                    "max_price": {
                        "type": "integer",
                        "description": "人均价格上限(元)",
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "最低评分 1.0-5.0",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "标签筛选, 如['约会','拍照','安静']",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数量, 默认15",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_poi_detail",
            "description": "获取指定地点的完整详细信息，包括评价、营业时间、适合场景、注意事项、用户评价等。用于深入了解某个地点。",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_id": {
                        "type": "string",
                        "description": "地点ID, 如 poi_001",
                    },
                },
                "required": ["poi_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_events",
            "description": "获取当前进行中的周末活动、市集、展览、音乐节等信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "活动类别: 市集/音乐/电影/艺术/美食/运动/文化/戏剧",
                    },
                    "min_date": {
                        "type": "string",
                        "description": "最早日期 YYYY-MM-DD",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取上海指定日期的天气预报，用于出行建议。",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "日期 YYYY-MM-DD, 默认今天",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_trip_plan",
            "description": "根据选定的地点列表生成完整的行程方案。包含每个地点的建议停留时间、步行时间、总预算估算、路线顺序。调用此工具前应先用search_pois筛选好地点。",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "选定的地点ID列表，按访问顺序排列",
                    },
                    "title": {
                        "type": "string",
                        "description": "行程标题，如'武康路咖啡漫步'",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "出发时间, 如14:00, 默认14:00",
                    },
                    "user_notes": {
                        "type": "string",
                        "description": "用户备注/特殊需求",
                    },
                },
                "required": ["poi_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_trip",
            "description": "用户确认方案后，保存行程到数据库。仅在用户明确表示确认/满意时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_title": {"type": "string", "description": "行程标题"},
                    "plan_type": {"type": "string", "description": "方案类型: 美食探店/文艺漫步/城市探索/浪漫约会"},
                    "poi_ids": {"type": "array", "items": {"type": "string"}, "description": "地点ID列表"},
                    "total_budget": {"type": "string", "description": "预算文字, 如'人均约168元'"},
                    "duration": {"type": "string", "description": "时长, 如'3小时'"},
                },
                "required": ["plan_title", "poi_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_raw_data",
            "description": "获取用户在美团生态的全部原始元数据：到店消费记录（时间/地点/类别/金额/和谁一起/评价）、外卖订单、团购购买记录。每条都是原始数据，AI 需要自己分析总结。调用后自己根据原始记录推断用户偏好。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户ID"},
                    "limit": {"type": "integer", "description": "返回条数，默认50"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_user_profile",
            "description": "兼容旧工具名。获取用户原始消费元数据，由 Agent 或画像服务分析偏好。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户ID"},
                    "limit": {"type": "integer", "description": "返回条数，默认50"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_consumption_history",
            "description": "获取用户在美团生态的完整消费历史：到店消费、团购购买、外卖订单、点评记录等。按时间倒序排列。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户ID"},
                    "category": {"type": "string", "description": "筛选类别: 美食/咖啡/外卖/团购/艺术, 留空则全部"},
                    "limit": {"type": "integer", "description": "返回数量, 默认20"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_deals",
            "description": "搜索美团/大众点评的团购券和优惠券。可按类别、价格筛选，用于帮用户找到最划算的消费方案。",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "类别: 美食/咖啡/甜品/艺术/酒吧"},
                    "max_price": {"type": "integer", "description": "最高团购价"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "筛选: 周末可用/新客专享/约会推荐/朋友聚会/下午茶"},
                    "limit": {"type": "integer", "description": "返回数量, 默认10"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_social_matches",
            "description": "基于消费数据和兴趣画像，为用户找到最匹配的社交伙伴（陌生人组局/交友）。分析共同去过的店、共同喜好的类别、消费层级匹配度。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户ID"},
                    "category": {"type": "string", "description": "组局类别: 美食/咖啡/户外/艺术/不限"},
                    "group_size": {"type": "integer", "description": "期望组局人数, 默认3"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "查询餐厅/商户的实时可用性：是否有位置、是否需要排队、预计等待时间、最佳到店时段。用于规划前验证可行性。",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_id": {"type": "string", "description": "商户ID，如 poi_001"},
                    "date": {"type": "string", "description": "日期 YYYY-MM-DD，默认今天"},
                    "time": {"type": "string", "description": "预计到店时间，如18:00"},
                    "party_size": {"type": "integer", "description": "人数，默认4"},
                },
                "required": ["poi_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_reviews",
            "description": "读取某商户的真实用户评价摘要。包括好评关键词、差评关键词、典型用户评价、热门菜品/服务标签。基于大众点评评论数据生成。",
            "parameters": {
                "type": "object",
                "properties": {
                    "poi_id": {"type": "string", "description": "商户ID"},
                    "limit": {"type": "integer", "description": "返回评价条数，默认5"},
                },
                "required": ["poi_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_actions",
            "description": "一键执行用户确认后的所有操作：预订餐厅、购买门票、下单配送。用户确认方案后调用此工具完成所有动作。这是最终执行步骤。",
            "parameters": {
                "type": "object",
                "properties": {
                    "actions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string", "description": "动作类型: reserve_restaurant / buy_tickets / order_delivery"},
                                "poi_id": {"type": "string", "description": "商户ID"},
                                "poi_name": {"type": "string", "description": "商户名称"},
                                "time": {"type": "string", "description": "时间"},
                                "party_size": {"type": "integer", "description": "人数"},
                                "delivery_item": {"type": "string", "description": "配送物品，如'生日蛋糕'"},
                                "delivery_to": {"type": "string", "description": "配送到哪个商户"},
                            },
                        },
                        "description": "要执行的动作列表",
                    },
                },
                "required": ["actions"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_habits",
            "description": "更新用户的生活习惯。当用户在对话中透露了工作信息、空闲时间、饮食限制、出行偏好等，调用此工具保存。这些习惯会优化后续推荐。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户ID"},
                    "work_days": {"type": "integer", "description": "每周上班天数"},
                    "off_work_time": {"type": "string", "description": "几点下班，如18:00"},
                    "commute_minutes": {"type": "integer", "description": "通勤时间(分钟)"},
                    "free_slots": {"type": "array", "items": {"type": "string"}, "description": "空闲时段，如['周六下午','周日全天']"},
                    "preferred_areas": {"type": "array", "items": {"type": "string"}, "description": "偏好区域"},
                    "dietary": {"type": "array", "items": {"type": "string"}, "description": "饮食限制，如['不吃辣','减肥中']"},
                    "mobility": {"type": "string", "description": "出行方式: 步行/地铁/开车"},
                    "budget_comfort": {"type": "integer", "description": "舒适预算(元)"},
                    "notes": {"type": "string", "description": "其他备注"},
                },
                "required": ["user_id"],
            },
        },
    },
]


# ═══════════════════════════════════════════
# 工具执行函数
# ═══════════════════════════════════════════

def execute_tool(tool_name: str, arguments: dict) -> str:
    """执行工具并返回 JSON 字符串结果"""
    if tool_name == "search_pois":
        return _search_pois(arguments)
    elif tool_name == "get_poi_detail":
        return _get_poi_detail(arguments)
    elif tool_name == "get_events":
        return _get_events(arguments)
    elif tool_name == "get_weather":
        return _get_weather(arguments)
    elif tool_name == "generate_trip_plan":
        return _generate_trip_plan(arguments)
    elif tool_name == "save_trip":
        return _save_trip(arguments)
    elif tool_name == "get_user_raw_data":
        return _get_user_raw_data(arguments)
    elif tool_name == "analyze_user_profile":
        return _analyze_user_profile(arguments)
    elif tool_name == "get_consumption_history":
        return _get_consumption_history(arguments)
    elif tool_name == "search_deals":
        return _search_deals(arguments)
    elif tool_name == "find_social_matches":
        return _find_social_matches(arguments)
    elif tool_name == "check_availability":
        return _check_availability(arguments)
    elif tool_name == "read_reviews":
        return _read_reviews(arguments)
    elif tool_name == "execute_actions":
        return _execute_actions(arguments)
    elif tool_name == "update_user_habits":
        return _update_user_habits(arguments)
    else:
        return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)


def _search_pois(args):
    category = args.get("category", "")
    district = args.get("district", "")
    neighborhood = args.get("neighborhood", "")
    max_price = args.get("max_price")
    min_rating = args.get("min_rating")
    tags = args.get("tags", [])
    limit = args.get("limit", 15)

    query = POI.query.filter(POI.business_status == "open")

    if category:
        query = query.filter(POI.category == category)
    if district:
        query = query.filter(POI.district == district)
    if neighborhood:
        query = query.filter(POI.neighborhood == neighborhood)
    if max_price:
        query = query.filter(POI.price_per_capita <= max_price)
    if min_rating:
        query = query.filter(POI.rating >= min_rating)

    pois = query.limit(min(limit, 30)).all()

    # 标签二次过滤
    results = []
    for p in pois:
        p_dict = p.to_dict()
        if tags:
            poi_tags = p.tags or []
            if not any(t in poi_tags for t in tags):
                continue
        results.append({
            "poiId": p_dict["poiId"],
            "name": p_dict["name"],
            "category": p_dict["category"],
            "address": p_dict["address"],
            "district": p.district,
            "neighborhood": p.neighborhood,
            "pricePerCapita": p_dict["pricePerCapita"],
            "rating": p_dict["rating"],
            "tags": p_dict["tags"][:5],
            "openHours": p_dict["openHoursText"],
            "suitableFor": p_dict["suitableFor"][:3],
        })

    return json.dumps({
        "count": len(results),
        "pois": results[:limit],
        "tip": "可以继续用 get_poi_detail 查看某个地点的详细信息" if results else "没有找到匹配的地点，建议放宽筛选条件",
    }, ensure_ascii=False, indent=2)


def _get_poi_detail(args):
    poi_id = args.get("poi_id", "")
    poi = POI.query.filter_by(poi_id=poi_id).first()
    if not poi:
        return json.dumps({"error": f"未找到地点 {poi_id}"}, ensure_ascii=False)

    d = poi.to_dict()
    return json.dumps({
        "poiId": d["poiId"],
        "name": d["name"],
        "category": d["category"],
        "address": d["address"],
        "pricePerCapita": d["pricePerCapita"],
        "rating": d["rating"],
        "openHours": d["openHoursText"],
        "phone": d["phone"],
        "tags": d["tags"],
        "about": d["about"],
        "impressionTags": d["impressionTags"],
        "suitableFor": d["suitableFor"],
        "attention": d["attention"],
        "userQuote": d["userQuote"],
        "district": poi.district,
        "neighborhood": poi.neighborhood,
        "lat": d["lat"],
        "lng": d["lng"],
    }, ensure_ascii=False, indent=2)


def _get_events(args):
    city = args.get("city", "上海")
    category = args.get("category", "")
    query = Event.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)

    events = query.limit(8).all()
    results = [{
        "eventId": e.event_id,
        "emoji": e.emoji,
        "title": e.title,
        "subtitle": e.subtitle,
        "badge": e.badge,
        "category": e.category,
        "dateRange": f"{e.start_date} ~ {e.end_date}",
    } for e in events]

    return json.dumps({
        "count": len(results),
        "events": results,
    }, ensure_ascii=False, indent=2)


def _get_weather(args):
    date = args.get("date", time.strftime("%Y-%m-%d"))
    # Mock 天气数据
    weathers = [
        {"condition": "晴天", "temp_high": 28, "temp_low": 20, "rain": "无", "tip": "适合户外活动，注意防晒"},
        {"condition": "多云", "temp_high": 25, "temp_low": 18, "rain": "10%", "tip": "适合出行，建议带薄外套"},
        {"condition": "阵雨", "temp_high": 22, "temp_low": 17, "rain": "60%", "tip": "建议室内活动为主，带伞"},
        {"condition": "阴天", "temp_high": 24, "temp_low": 19, "rain": "30%", "tip": "不影响出行，建议室内外结合"},
    ]
    w = random.choice(weathers)
    return json.dumps({
        "date": date,
        "city": "上海",
        **w,
    }, ensure_ascii=False, indent=2)


def _generate_trip_plan(args):
    poi_ids = args.get("poi_ids", [])
    title = args.get("title", "周末出行")
    start_time_str = args.get("start_time", "14:00")
    user_notes = args.get("user_notes", "")

    pois = []
    for pid in poi_ids:
        poi = POI.query.filter_by(poi_id=pid).first()
        if poi:
            pois.append(poi)

    if len(pois) < 2:
        return json.dumps({
            "error": "至少需要2个地点才能生成行程",
            "tip": "请先用 search_pois 找到更多地点",
        }, ensure_ascii=False)

    # 计算时间
    try:
        start_h, start_m = map(int, start_time_str.split(":"))
    except:
        start_h, start_m = 14, 0

    total_minutes = start_h * 60 + start_m
    stops = []
    walk_times = [0, 5, 8, 10, 12, 15]  # 步间步行时间

    for i, poi in enumerate(pois):
        duration = 50  # 默认每个地点50分钟
        h = total_minutes // 60
        m = total_minutes % 60

        stop = {
            "order": i + 1,
            "time": f"{h:02d}:{m:02d}",
            "name": poi.name,
            "poiId": poi.poi_id,
            "category": poi.category,
            "address": poi.address,
            "pricePerCapita": poi.price_per_capita,
            "durationMinutes": duration,
            "tags": poi.tags[:3] if poi.tags else [],
            "walkFromPrevious": walk_times[min(i, len(walk_times) - 1)],
            "endTime": f"{(h + (m + duration) // 60) % 24:02d}:{(m + duration) % 60:02d}",
        }
        stops.append(stop)
        total_minutes += duration + (walk_times[min(i + 1, len(walk_times) - 1)] if i < len(pois) - 1 else 0)

    total_price = sum(p.price_per_capita for p in pois)
    total_walk = sum(s["walkFromPrevious"] for s in stops)
    end_minutes = total_minutes

    return json.dumps({
        "title": title,
        "totalDuration": f"约{end_minutes // 60 - start_h}小时{end_minutes % 60}分钟",
        "totalBudget": f"人均约{total_price}元",
        "totalDistance": f"约{0.5 * len(pois):.1f}km",
        "transportMode": "全程步行",
        "totalWalkMinutes": total_walk,
        "stops": stops,
        "userNotes": user_notes,
        "tip": "用户确认后调用 save_trip 保存行程。也可以告诉用户哪些地方可以调整。",
    }, ensure_ascii=False, indent=2)


def _save_trip(args):
    import uuid
    plan_title = args.get("plan_title", "周末出行")
    plan_type = args.get("plan_type", "城市探索")
    poi_ids = args.get("poi_ids", [])
    total_budget = args.get("total_budget", "约150元")
    duration = args.get("duration", "3小时")

    trip_id = f"t_{uuid.uuid4().hex[:8]}"
    trip = Trip(
        trip_id=trip_id,
        user_id="u_demo_001",
        title=plan_title,
        total_budget=total_budget,
        status="planned",
        overview={
            "type": plan_type,
            "duration": duration,
            "budgetRange": total_budget,
        },
    )

    db.session.add(trip)

    for i, pid in enumerate(poi_ids):
        poi = POI.query.filter_by(poi_id=pid).first()
        if poi:
            h = 14 + (i * 55) // 60
            m = (i * 55) % 60
            stop = TripStop(
                stop_id=f"ts_{uuid.uuid4().hex[:8]}",
                trip_id_fk=trip_id,
                poi_id=pid,
                index=i + 1,
                time=f"{h:02d}:{m:02d}",
                name=poi.name,
                desc=f"步行约{5 + i * 3}分钟",
                duration_minutes=50,
            )
            db.session.add(stop)

    db.session.commit()

    return json.dumps({
        "success": True,
        "tripId": trip_id,
        "message": f"行程「{plan_title}」已保存！可以在行程页查看。",
        "shareUrl": f"https://weekendgo.example.com/share/{trip_id}",
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════
# 美团生态工具: 用户画像 / 消费历史 / 团购 / 社交匹配
# ═══════════════════════════════════════════

def _get_user_raw_data(args):
    """返回用户原始消费元数据，不做统计。AI 自己分析。"""
    user_id = args.get("user_id", "")
    limit = args.get("limit", 50)
    records = ConsumptionRecord.query.filter_by(user_id=user_id).order_by(ConsumptionRecord.date.desc()).limit(limit).all()
    if not records:
        return json.dumps({"userId": user_id, "totalRecords": 0, "records": [],
            "note": "该用户暂无消费数据。可以询问用户偏好。"}, ensure_ascii=False, indent=2)
    raw = [{"date": r.date, "timeOfDay": r.time_of_day, "poiName": r.poi_name,
        "category": r.category, "amount": r.amount, "rating": r.rating,
        "review": r.review, "withFriends": r.with_friends or [],
        "tags": r.tags or [], "dealUsed": r.deal_used or "",
        "source": r.source, "locationContext": r.location_context,
        "itemDetail": r.item_detail} for r in records]
    return json.dumps({"userId": user_id, "totalRecords": len(raw), "records": raw,
        "dataSource": "美团到店+点评+外卖+团购。AI请自行从原始数据分析偏好。"}, ensure_ascii=False, indent=2)


def _analyze_user_profile(args):
    """[兼容] 返回原始元数据，AI 自己分析"""
    return _get_user_raw_data(args)




def _get_consumption_history(args):
    """获取用户完整消费历史"""
    user_id = args.get("user_id", "")
    category = args.get("category", "")
    limit = args.get("limit", 20)

    query = ConsumptionRecord.query.filter_by(user_id=user_id)
    if category:
        query = query.filter_by(category=category)

    records = query.order_by(ConsumptionRecord.date.desc()).limit(limit).all()
    results = [r.to_dict() for r in records]

    return json.dumps({
        "userId": user_id,
        "totalRecords": len(results),
        "records": results,
        "dataSources": "模拟数据来源: 美团到店消费 + 大众点评 + 美团外卖 + 团购核销",
    }, ensure_ascii=False, indent=2)


def _search_deals(args):
    """搜索团购券"""
    category = args.get("category", "")
    max_price = args.get("max_price")
    tags = args.get("tags", [])
    limit = args.get("limit", 10)

    query = Deal.query
    if category:
        query = query.filter_by(category=category)
    if max_price:
        query = query.filter(Deal.deal_price <= max_price)

    deals = query.limit(limit).all()

    # 标签二次过滤
    results = []
    for d in deals:
        dic = d.to_dict()
        if tags:
            deal_tags = dic.get("tags", [])
            if not any(t in deal_tags for t in tags):
                continue
        # 计算省钱金额
        dic["saveAmount"] = dic["originalPrice"] - dic["dealPrice"]
        results.append(dic)

    return json.dumps({
        "count": len(results),
        "deals": results[:limit],
        "tip": "团购券可以帮用户省钱，记得推荐时带上价格对比",
        "source": "数据来源: 美团/大众点评团购",
    }, ensure_ascii=False, indent=2)


def _find_social_matches(args):
    """社交匹配 - 找到志同道合的人"""
    user_id = args.get("user_id", "")
    target_category = args.get("category", "")
    group_size = args.get("group_size", 3)

    # 获取当前用户画像
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        # 动态生成
        _analyze_user_profile({"user_id": user_id})
        profile = UserProfile.query.filter_by(user_id=user_id).first()

    if not profile:
        return json.dumps({"error": f"无法获取用户 {user_id} 的画像"}, ensure_ascii=False)

    user_cats = [c["category"] for c in (profile.favorite_categories or [])]
    user_tags = set(profile.favorite_tags or [])

    # 找所有其他用户
    other_profiles = UserProfile.query.filter(UserProfile.user_id != user_id).all()
    matches = []

    for op in other_profiles:
        op_cats = [c["category"] for c in (op.favorite_categories or [])]
        op_tags = set(op.favorite_tags or [])

        # 共同类别
        common_cats = set(user_cats) & set(op_cats)
        # 共同标签
        common_tags = user_tags & op_tags
        # 消费水平匹配 (越接近分越高)
        spending_diff = abs((profile.avg_spending or 50) - (op.avg_spending or 50))
        spending_match = max(0, 1 - spending_diff / 200)

        # 目标类别加权
        target_bonus = 0
        if target_category and target_category in common_cats:
            target_bonus = 0.3

        match_score = min(1.0, len(common_cats) * 0.2 + len(common_tags) * 0.1 + spending_match * 0.3 + target_bonus)

        matches.append({
            "userId": op.user_id,
            "nickname": op.nickname or op.user_id,
            "commonCategories": list(common_cats),
            "commonTags": list(common_tags),
            "matchScore": round(match_score, 2),
            "personaTags": op.persona_tags or [],
            "socialStyle": op.social_style or "未知",
            "avgSpending": round(op.avg_spending or 0),
            "reason": f"共同喜欢{'、'.join(list(common_cats)[:2])}，{'消费水平相近' if spending_match > 0.7 else '消费风格不同但可互补'}",
        })

    # 按匹配分数排序
    matches.sort(key=lambda x: x["matchScore"], reverse=True)

    return json.dumps({
        "userId": user_id,
        "groupSize": group_size,
        "category": target_category or "不限",
        "totalCandidates": len(matches),
        "topMatches": matches[:5],
        "tip": "可以基于这些匹配结果发起组局，邀请共同兴趣的人一起",
    }, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════
# 赛题专用工具: 可用性 / 评论 / 一键执行
# ═══════════════════════════════════════════

def _check_availability(args):
    """查询餐厅实时状态"""
    poi_id = args.get("poi_id", "")
    party_size = args.get("party_size", 4)
    time_str = args.get("time", "18:00")

    poi = POI.query.filter_by(poi_id=poi_id).first()
    if not poi:
        return json.dumps({"error": f"商户 {poi_id} 不存在"}, ensure_ascii=False)

    # Mock 逻辑：评分高的店周末会排队
    hour = int(time_str.split(":")[0]) if ":" in time_str else 18
    is_peak = 11 <= hour <= 13 or 17 <= hour <= 19
    is_weekend = True  # 默认周末场景
    is_popular = poi.rating >= 4.5

    if not is_peak:
        available, wait, risk = True, 0, "low"
        tip = "非高峰时段，直接到店即可"
    elif is_popular and is_weekend:
        available, wait, risk = True, 15 + int(poi.rating * 3), "high"
        tip = f"周末高峰期，建议提前{wait}分钟到店取号。17:30前到可以避开排队"
    elif is_popular:
        available, wait, risk = True, 5 + int(poi.rating * 2), "medium"
        tip = "建议提前10分钟到店"
    else:
        available, wait, risk = True, 0, "low"
        tip = "一般不用排队，直接去就行"

    # 大桌/包间
    if party_size >= 6 and poi.category == "美食":
        available = is_popular  # 热门店大桌紧张
        tip += "。6人以上建议提前1天电话预订"

    return json.dumps({
        "poiId": poi_id,
        "poiName": poi.name,
        "available": available,
        "queueRisk": risk,
        "waitMinutes": wait,
        "bestArrivalWindow": f"{hour-1}:00-{hour}:00" if is_peak else f"{hour}:00-{hour+1}:00",
        "partySize": party_size,
        "tip": tip,
        "phone": poi.phone or "021-xxxx-xxxx",
    }, ensure_ascii=False, indent=2)


def _read_reviews(args):
    """读取商户评论"""
    poi_id = args.get("poi_id", "")
    limit = args.get("limit", 5)

    poi = POI.query.filter_by(poi_id=poi_id).first()
    if not poi:
        return json.dumps({"error": f"商户 {poi_id} 不存在"}, ensure_ascii=False)

    # 基于 POI 数据生成模拟评论
    tags = poi.tags or []
    impression = poi.impression_tags or tags[:3]

    positive_keywords = impression[:3]
    negative_keywords = ["排队久", "价格偏高"] if poi.rating < 4.5 else ["周末人多"]

    # 生成风格的模拟评论
    mock_reviews = [
        {"rating": 5, "user": "大众点评用户***明", "date": "2026-06-01",
         "content": f"{poi.name}真的太棒了！{' '.join(positive_keywords[:2])}，强烈推荐。{poi.user_quote or '下次还会再来'}", "tags": positive_keywords[:2]},
        {"rating": 4, "user": "美团用户***红", "date": "2026-05-28",
         "content": f"整体不错，{' '.join(tags[:2])}都很满意。就是{negative_keywords[0]}，建议避开高峰。", "tags": tags[:2]},
        {"rating": 5, "user": "匿名用户", "date": "2026-05-20",
         "content": f"人均¥{poi.price_per_capita}，性价比{'很高' if poi.price_per_capita < 80 else '还行'}。{poi.about or ''}"[:80], "tags": impression[:2]},
    ]

    # 适合亲子/减肥等特殊需求的关键词
    special_tags = []
    if any(t in str(tags) for t in ["亲子", "儿童", "家庭"]):
        special_tags.append("亲子友好")
    if any(t in str(tags) for t in ["轻食", "沙拉", "有机", "健康"]):
        special_tags.append("减肥友好")
    if any(t in str(tags) for t in ["安静", "独立", "小众"]):
        special_tags.append("适合独处")
    if poi.price_per_capita < 60:
        special_tags.append("性价比高")

    return json.dumps({
        "poiId": poi_id,
        "poiName": poi.name,
        "rating": poi.rating,
        "reviewCount": 200 + int(poi.rating * 50),
        "positiveKeywords": positive_keywords,
        "negativeKeywords": negative_keywords,
        "specialTags": special_tags,
        "reviews": mock_reviews[:limit],
        "summary": f"用户普遍认为{poi.name}{' '.join(positive_keywords[:2])}。需要注意{negative_keywords[0]}。{'适合' + '、'.join(special_tags) if special_tags else ''}",
    }, ensure_ascii=False, indent=2)


def _execute_actions(args):
    """一键执行所有预订/下单动作"""
    actions = args.get("actions", [])
    if not actions:
        return json.dumps({"error": "没有要执行的动作"}, ensure_ascii=False)

    results = []
    all_success = True

    for i, action in enumerate(actions):
        action_type = action.get("type", "")
        poi_name = action.get("poi_name", "未知商户")
        result = {"action": action_type, "poiName": poi_name}

        if action_type == "reserve_restaurant":
            result.update({
                "status": "confirmed",
                "detail": f"已预订 {poi_name}，{action.get('party_size',4)}人，{action.get('time','18:00')}",
                "bookingId": f"BK{int(time.time())}{i}",
                "note": "到店报手机号即可，座位保留15分钟",
            })
        elif action_type == "buy_tickets":
            result.update({
                "status": "confirmed",
                "detail": f"已购买 {poi_name} 门票 ×{action.get('count',2)}张",
                "ticketId": f"TK{int(time.time())}{i}",
                "note": "电子票已发送到手机，扫码入园",
            })
        elif action_type == "order_delivery":
            result.update({
                "status": "confirmed",
                "detail": f"已下单「{action.get('delivery_item','物品')}」配送至 {action.get('delivery_to','指定地址')}",
                "orderId": f"OD{int(time.time())}{i}",
                "note": f"预计{action.get('time','18:30')}前送达",
            })
        else:
            result["status"] = "skipped"
            result["detail"] = f"未知动作类型: {action_type}"

        if result["status"] != "confirmed":
            all_success = False
        results.append(result)

    return json.dumps({
        "success": all_success,
        "executedAt": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "totalActions": len(actions),
        "results": results,
        "shareMessage": _generate_share_message(results) if all_success else "",
    }, ensure_ascii=False, indent=2)


def _generate_share_message(results):
    """生成发给朋友/老婆的确认消息"""
    lines = ["搞定了！已一键安排好：\n"]
    for r in results:
        lines.append(f"✅ {r['detail']}")
    lines.append(f"\n下午见～")
    return "\n".join(lines)


def _update_user_habits(args):
    """AI 对话中收集用户习惯 → 直接更新统一画像 UserProfile"""
    user_id = args.get("user_id", "")
    if not user_id:
        return json.dumps({"error": "user_id 必填"}, ensure_ascii=False)

    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.session.add(profile)

    changed = []
    field_map = {
        'work_days':'work_days','off_work_time':'off_work_time',
        'commute_minutes':'commute_minutes','free_slots':'free_slots',
        'dietary':'dietary',
        'mobility':'mobility','budget_comfort':'budget_comfort',
        'notes':'user_notes','group_size_preference':'group_size_preference',
        'home_area':'home_area','work_area':'work_area',
        'preferred_areas':'favorite_districts',
    }
    for arg_key, col_name in field_map.items():
        if arg_key in args:
            old = getattr(profile, col_name)
            val = args[arg_key]
            # 列表字段合并而非覆盖
            if isinstance(old, list) and isinstance(val, list):
                setattr(profile, col_name, list(set(old + val)))
            else:
                setattr(profile, col_name, val)
            if old != getattr(profile, col_name):
                changed.append(arg_key)

    if 'preferred_areas' in args:
        old_areas = profile.favorite_districts or []
        normalized = []
        seen = set()
        for item in old_areas:
            if isinstance(item, dict):
                district = item.get('district')
                count = item.get('count', 1)
            else:
                district = str(item)
                count = 1
            if district and district not in seen:
                normalized.append({'district': district, 'count': count})
                seen.add(district)
        for area in args.get('preferred_areas') or []:
            if area and area not in seen:
                normalized.append({'district': area, 'count': 1})
                seen.add(area)
        if normalized != old_areas:
            profile.favorite_districts = normalized
            changed.append('preferred_areas')

    profile.habits_updated_at = time.strftime('%Y-%m-%dT%H:%M:%S')
    db.session.commit()

    return json.dumps({
        "success": True,
        "userId": user_id,
        "updatedFields": changed,
        "profile": profile.to_dict(),
        "tip": "已更新统一画像。后续推荐会同时参考消费数据和你的自述偏好。",
    }, ensure_ascii=False, indent=2)

