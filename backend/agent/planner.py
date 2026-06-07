"""
AI 规划 Agent - 方案生成核心
"""
import json
import time
import random
from models import db, POI
from agent.llm_client import call_deepseek, parse_json_response

# 方案生成的 System Prompt
PLANNER_SYSTEM_PROMPT = """你是美团周末规划助手 "Weekendgo"，一个帮助用户在碎片化空闲时间内发现和执行本地活动的 AI 规划师。

你的任务是根据用户的偏好条件和可用地点，生成 3-4 个差异化的周末出行方案。

## 输出要求
严格输出 JSON 格式：
```json
{
  "plans": [
    {
      "planId": "p_XXXX",
      "type": "美食探店",
      "title": "安福路咖啡和小食慢逛",
      "duration": "3 小时",
      "budgetText": "人均约 168 元",
      "tag": "热门",
      "color": "#ff8a65",
      "score": 92,
      "description": "一句话描述这个方案的亮点",
      "spots": [
        {
          "spotId": "poi_XXX",
          "name": "地点名称",
          "category": "类别",
          "address": "地址",
          "etaMinutes": 12
        }
      ]
    }
  ],
  "generatedAt": "ISO 时间戳"
}
```

## 规划原则
1. **地理连贯性**：同一方案的地点应在步行可达范围内（相邻街区），不要跨区组合
2. **时间合理**：每个地点停留 40-60 分钟，步行时间 5-15 分钟
3. **多样性**：3-4 个方案应覆盖不同风格（如美食向、文艺向、户外向、约会向）
4. **节奏感**：方案间保持不同时长（1.5h / 3h / 半日）
5. **定价准确**：根据候选 POI 的实际价格范围估算总预算

## 注意
- 只使用我提供的候选 POI 列表中的地点
- 每个方案包含 2-4 个地点节点
- 如果某个偏好下候选 POI 不足，可以适当放宽条件
"""


def _filter_pois(time_type, activities, geo_range, budget, prompt_text):
    """
    规则引擎：根据用户偏好从数据库筛选候选 POI
    不依赖 LLM，纯 SQL 查询
    """
    query = POI.query.filter(POI.business_status == 'open')

    # 活动类别映射
    category_map = {
        '寻味美食': '美食',
        '喝咖啡': '咖啡',
        '逛街区': '户外',
        '手作体验': '市集',
        '城市散步': '户外',
        '拍照打卡': '户外',
        '书店阅读': '书店',
        '看展览': '艺术',
    }

    categories = set()
    for act in activities:
        cat = category_map.get(act)
        if cat:
            categories.add(cat)

    if categories:
        # 匹配类别
        from sqlalchemy import or_
        conditions = [POI.category == c for c in categories]
        query = query.filter(or_(*conditions))

    # 预算过滤
    budget_range = {
        '100元内': (0, 100),
        '100-200元': (100, 200),
        '200-300元': (200, 300),
    }
    if budget in budget_range:
        low, high = budget_range[budget]
        query = query.filter(POI.price_per_capita <= high)

    # 地理范围过滤（简化：默认全城，就近玩玩用徐汇+静安）
    if geo_range == '就近玩玩':
        query = query.filter(POI.district.in_(['徐汇', '静安']))

    pois = query.limit(60).all()
    return [p.to_dict() for p in pois]


def _build_llm_prompt(pois, time_type, activities, geo_range, budget, prompt_text, city='上海'):
    """构建发给 LLM 的完整 prompt"""
    pois_json = json.dumps(pois, ensure_ascii=False, indent=2)

    user_message = f"""## 用户偏好
- 城市：{city}
- 时间类型：{time_type or '未指定'}
- 偏好活动：{', '.join(activities) if activities else '未指定'}
- 出行范围：{geo_range or '未指定'}
- 人均预算：{budget or '不限'}
- 用户输入：{prompt_text or '无额外输入'}

## 候选地点列表（共 {len(pois)} 个）
{pois_json}

请根据以上信息生成 3-4 个方案。"""

    return [
        {'role': 'system', 'content': PLANNER_SYSTEM_PROMPT},
        {'role': 'user', 'content': user_message},
    ]


def generate_plans(time_type='', activities=None, geo_range='', budget='',
                   prompt_text='', city='上海'):
    """
    生成方案：规则过滤 → LLM 编排 → 返回结果

    如果 LLM 不可用，返回规则生成的 fallback 方案
    """
    if activities is None:
        activities = []

    # Step 1: 规则引擎筛选候选 POI
    pois = _filter_pois(time_type, activities, geo_range, budget, prompt_text)

    if len(pois) < 3:
        # 候选不足，放宽条件（不限定类别）
        pois = POI.query.filter(POI.business_status == 'open').limit(60).all()
        pois = [p.to_dict() for p in pois]

    # Step 2: 尝试 LLM 编排
    messages = _build_llm_prompt(pois, time_type, activities, geo_range, budget, prompt_text, city)
    llm_response, error = call_deepseek(messages, temperature=0.8, max_tokens=2048)

    if llm_response and not error:
        result, parse_error = parse_json_response(llm_response)
        if result and 'plans' in result:
            # 填充 planId 和时间戳
            for i, plan in enumerate(result.get('plans', [])):
                if 'planId' not in plan:
                    plan['planId'] = f"p_{int(time.time() * 1000)}_{i}"
            result['generatedAt'] = result.get('generatedAt', time.strftime('%Y-%m-%dT%H:%M:%S+08:00'))
            return result.get('plans', []), None

    # Step 3: Fallback — 规则生成简单方案
    print(f"[Agent] LLM 方案生成失败: {error or parse_error}, 使用 fallback")
    return _fallback_generate(pois, time_type, activities, budget)


def _fallback_generate(pois, time_type, activities, budget):
    """规则引擎 fallback：随机组合 3-4 个方案"""
    import random as rnd
    rnd.seed(int(time.time()))

    if len(pois) < 4:
        # 数据不够，从全库拉
        all_pois = POI.query.filter(POI.business_status == 'open').all()
        pois = [p.to_dict() for p in all_pois]

    # 按类别分组
    by_category = {}
    for p in pois:
        cat = p.get('category', '其他')
        by_category.setdefault(cat, []).append(p)

    plan_templates = [
        {'type': '美食探店', 'tag': '热门', 'color': '#ff8a65', 'cats': ['美食', '咖啡', '甜品']},
        {'type': '文艺漫步', 'tag': '推荐', 'color': '#7c4dff', 'cats': ['艺术', '书店', '咖啡']},
        {'type': '城市探索', 'tag': '新晋', 'color': '#26a69a', 'cats': ['户外', '市集', '美食']},
        {'type': '浪漫约会', 'tag': '精选', 'color': '#ec407a', 'cats': ['酒吧', '甜品', '美食']},
    ]

    plans = []
    for i, template in enumerate(plan_templates):
        plan_pois = []
        for cat in template['cats']:
            candidates = by_category.get(cat, [])
            if candidates:
                choice = rnd.choice(candidates)
                if choice not in plan_pois:
                    plan_pois.append(choice)

        if len(plan_pois) < 2:
            # 补充随机地点
            others = [p for p in pois if p not in plan_pois]
            rnd.shuffle(others)
            plan_pois.extend(others[:4 - len(plan_pois)])

        # 计算总预算
        total_price = sum(p.get('pricePerCapita', 50) for p in plan_pois[:4])
        durations = ['1.5 小时', '2.5 小时', '3 小时', '半日']
        plan = {
            'planId': f"p_fallback_{int(time.time() * 1000)}_{i}",
            'type': template['type'],
            'title': f"{plan_pois[0].get('name', '地点')}周边{'·'.join(template['cats'][:2])}",
            'duration': durations[i],
            'budgetText': f"人均约 {total_price} 元",
            'tag': template['tag'],
            'color': template['color'],
            'score': rnd.randint(78, 95),
            'description': f"在{plan_pois[0].get('neighborhood', '附近')}的{'·'.join(template['cats'][:2])}路线",
            'spots': [
                {
                    'spotId': p.get('poiId', ''),
                    'name': p.get('name', ''),
                    'category': p.get('category', ''),
                    'address': p.get('address', ''),
                    'etaMinutes': max(5, 10 + i * 3),  # 粗略估计
                }
                for p in plan_pois[:4]
            ],
        }
        plans.append(plan)

    return plans, None
