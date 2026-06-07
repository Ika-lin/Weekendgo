"""
行程管理 API 路由
"""
import time
import uuid
from flask import Blueprint, request, jsonify
from models import db, Trip, TripStop, POI

trip_bp = Blueprint('trip', __name__)


def _generate_stops(plan_spots):
    """根据方案中的 spots 生成行程节点"""
    stops = []
    start_hour = 14  # 默认下午 2 点开始
    for i, spot in enumerate(plan_spots):
        poi = POI.query.filter_by(poi_id=spot.get('spotId', '')).first()
        duration = 50  # 默认 50 分钟
        hour = start_hour + (i * (duration + 10)) // 60
        minute = (start_hour * 60 + i * (duration + 10)) % 60

        stop_id = f"ts_{uuid.uuid4().hex[:8]}"
        stop = TripStop(
            stop_id=stop_id,
            poi_id=spot.get('spotId', ''),
            index=i + 1,
            time=f'{hour:02d}:{minute:02d}',
            name=poi.name if poi else spot.get('name', ''),
            desc=f"步行约{spot.get('etaMinutes', 10)}分钟",
            duration_minutes=duration,
        )
        stops.append(stop)
    return stops


def _generate_stops_from_agent(plan_stops):
    """根据 agent 结构化 trip.stops 生成行程节点"""
    stops = []
    for i, item in enumerate(plan_stops):
        stop = TripStop(
            stop_id=f"ts_{uuid.uuid4().hex[:8]}",
            poi_id=item.get('poiId', ''),
            index=item.get('order') or i + 1,
            time=item.get('time', ''),
            name=item.get('name', ''),
            desc=item.get('reason', ''),
            duration_minutes=item.get('durationMinutes', 50),
            alternatives={
                'endTime': item.get('endTime', ''),
                'category': item.get('category', ''),
                'address': item.get('address', ''),
                'lat': item.get('lat'),
                'lng': item.get('lng'),
                'pricePerCapita': item.get('pricePerCapita'),
                'rating': item.get('rating'),
                'walkFromPrevious': item.get('walkFromPrevious', 0),
                'tags': item.get('tags', []),
                'queueInfo': item.get('queueInfo'),
            },
        )
        stops.append(stop)
    return stops


def _trip_summary(trip):
    detail = trip.to_detail_dict()
    overview = detail.get('overview') or {}
    stops = detail.get('stops') or []
    return {
        'tripId': detail.get('tripId'),
        'planId': trip.plan_id,
        'title': detail.get('title'),
        'city': detail.get('city'),
        'date': detail.get('date'),
        'status': detail.get('status'),
        'totalBudget': detail.get('totalBudget'),
        'type': overview.get('type') or overview.get('planType') or _infer_trip_type(stops),
        'duration': overview.get('duration') or overview.get('totalDuration') or '',
        'transportMode': overview.get('transportMode') or '',
        'totalWalkMinutes': overview.get('totalWalkMinutes') or overview.get('walkDurationMinutes'),
        'stopCount': len(stops),
        'firstStop': stops[0].get('name') if stops else '',
        'lastStop': stops[-1].get('name') if stops else '',
        'source': overview.get('source') or 'agent',
        'createdAt': trip.created_at.isoformat() if trip.created_at else '',
    }


def _infer_trip_type(stops):
    cats = [s.get('category') for s in stops if s.get('category')]
    if not cats:
        return '周末路线'
    if '咖啡' in cats and '书店' in cats:
        return '咖啡书店'
    if '美食' in cats:
        return '美食探店'
    if '艺术' in cats:
        return '艺术展览'
    return ' + '.join(list(dict.fromkeys(cats))[:2])


@trip_bp.route('/api/v1/trips', methods=['GET'])
def list_trips():
    """获取用户行程列表，用于类似聊天列表的行程入口"""
    user_id = request.args.get('userId', 'u_demo_001')
    limit = int(request.args.get('limit', 30))
    trips = (
        Trip.query
        .filter_by(user_id=user_id)
        .order_by(Trip.created_at.desc())
        .limit(limit)
        .all()
    )
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'userId': user_id,
            'items': [_trip_summary(t) for t in trips],
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/create', methods=['POST'])
def create():
    """创建行程"""
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId', 'anonymous')
    plan_id = data.get('planId', '')
    plan_data = data.get('plan', {})  # 前端可能传完整方案数据
    date = data.get('date', time.strftime('%Y-%m-%d'))

    trip_id = f"t_{uuid.uuid4().hex[:8]}"

    spots = plan_data.get('spots', [])
    agent_stops = plan_data.get('stops', [])

    if agent_stops:
        total_price = sum(int(s.get('pricePerCapita') or 0) for s in agent_stops) or 168
        markers = [
            {
                'stopId': f"draft_{i + 1}",
                'order': s.get('order') or i + 1,
                'name': s.get('name', ''),
                'lat': s.get('lat'),
                'lng': s.get('lng'),
                'category': s.get('category', ''),
            }
            for i, s in enumerate(agent_stops[:6])
        ]
    else:
        # 计算总预算
        total_price = sum(
            (POI.query.filter_by(poi_id=s.get('spotId', '')).first().price_per_capita
             if POI.query.filter_by(poi_id=s.get('spotId', '')).first() else 50)
            for s in spots
        ) or 168
        markers = [
            {
                'stopId': f'ts_{i}',
                'order': i + 1,
                'name': s.get('name', ''),
                'lat': 31.21 + i * 0.002,
                'lng': 121.44 + i * 0.001,
            }
            for i, s in enumerate(spots[:4])
        ]

    trip = Trip(
        trip_id=trip_id,
        user_id=user_id,
        plan_id=plan_id,
        title=plan_data.get('title', '周末出行'),
        city=data.get('city', '上海'),
        date=date,
        total_budget=plan_data.get('totalBudget') or f'约 {total_price} 元',
        status='planned',
        overview={
            'duration': plan_data.get('totalDuration'),
            'type': plan_data.get('type'),
            'source': plan_data.get('source', 'agent'),
            'distanceKm': round(0.5 + (len(agent_stops) or len(spots)) * 0.6, 1),
            'budgetRange': f'{total_price - 50}-{total_price + 50}',
            'budgetValue': plan_data.get('budgetValue') or total_price,
            'transportMode': plan_data.get('transportMode') or '全程步行',
            'totalWalkMinutes': plan_data.get('totalWalkMinutes'),
            'walkDurationMinutes': plan_data.get('totalWalkMinutes') or 10 + (len(agent_stops) or len(spots)) * 15,
            'fitReasons': plan_data.get('fitReasons', []),
            'conflicts': plan_data.get('conflicts', []),
            'request': plan_data.get('request', ''),
        },
        route_map={
            'polyline': '',
            'markers': markers,
            'bounds': {'north': 31.22, 'south': 31.20, 'east': 121.45, 'west': 121.43},
            'provider': 'mock_route_api',
            'agentPath': 'rank_pois -> generate_structured_trip -> route_map',
        },
    )

    # 生成行程节点
    stops = _generate_stops_from_agent(agent_stops) if agent_stops else _generate_stops(spots)
    for s in stops:
        s.trip_id_fk = trip_id
        db.session.add(s)

    db.session.add(trip)
    db.session.commit()

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'tripId': trip_id,
            'trip': trip.to_detail_dict(),
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>', methods=['GET'])
def get_detail(trip_id):
    """获取行程详情"""
    trip = Trip.query.filter_by(trip_id=trip_id).first()
    if not trip:
        return jsonify({
            'code': 1003,
            'message': '行程不存在',
            'data': {},
            'requestId': uuid.uuid4().hex[:16],
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        }), 404

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': trip.to_detail_dict(),
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>/stops/<stop_id>', methods=['PATCH'])
def update_stop(trip_id, stop_id):
    """更新行程节点状态（打卡）"""
    data = request.get_json(silent=True) or {}
    stop = TripStop.query.filter_by(stop_id=stop_id, trip_id_fk=trip_id).first()
    if not stop:
        return jsonify({
            'code': 3002,
            'message': '行程节点不存在',
            'data': {},
            'requestId': uuid.uuid4().hex[:16],
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        }), 404

    stop.done = data.get('done', stop.done)
    stop.checkin_time = data.get('actualTime', time.strftime('%Y-%m-%dT%H:%M:%S+08:00'))
    db.session.commit()

    # 更新行程状态
    trip = Trip.query.filter_by(trip_id=trip_id).first()
    all_stops = TripStop.query.filter_by(trip_id_fk=trip_id).all()
    done_count = sum(1 for s in all_stops if s.done)
    if done_count == len(all_stops):
        trip.status = 'completed'
    elif done_count > 0:
        trip.status = 'ongoing'
    db.session.commit()

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'tripId': trip_id,
            'stop': stop.to_dict(),
            'progress': {
                'total': len(all_stops),
                'done': done_count,
            },
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>/overview', methods=['GET'])
def get_overview(trip_id):
    """获取行程总览"""
    trip = Trip.query.filter_by(trip_id=trip_id).first()
    if not trip:
        return jsonify({'code': 1003, 'message': '行程不存在', 'data': {}}), 404

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': trip.overview or {},
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>/route-map', methods=['GET'])
def get_route_map(trip_id):
    """获取行程路线图数据"""
    trip = Trip.query.filter_by(trip_id=trip_id).first()
    if not trip:
        return jsonify({'code': 1003, 'message': '行程不存在', 'data': {}}), 404

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': trip.route_map or {},
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>/weather', methods=['GET'])
def get_trip_weather(trip_id):
    """获取行程天气影响。当前使用 mock provider，但接口路径按产品能力保留。"""
    trip = Trip.query.filter_by(trip_id=trip_id).first()
    if not trip:
        return jsonify({'code': 1003, 'message': '行程不存在', 'data': {}}), 404

    city = trip.city or request.args.get('city', '上海')
    weather = {
        'tripId': trip_id,
        'city': city,
        'date': trip.date or time.strftime('%Y-%m-%d'),
        'provider': 'mock_weather_api',
        'condition': '多云转晴',
        'temperatureText': '24-29°C',
        'humidity': '62%',
        'wind': '东南风 2 级',
        'rainProbability': 12,
        'comfortLevel': '适合步行',
        'agentTips': [
            '下午日照偏强，建议带遮阳伞。',
            '整体降雨概率低，路线可以优先步行。',
            '咖啡店高峰可能比天气影响更大，建议保留缓冲时间。',
        ],
        'impact': {
            'walking': 'good',
            'outdoor': 'good',
            'queue': 'medium',
        },
    }
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': weather,
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>/stops/<stop_id>/alternatives', methods=['GET'])
def get_alternatives(trip_id, stop_id):
    """获取节点候选替换列表"""
    stop = TripStop.query.filter_by(stop_id=stop_id, trip_id_fk=trip_id).first()
    if not stop:
        return jsonify({'code': 3002, 'message': '节点不存在', 'data': {}}), 404

    # 找同类别附近 POI
    current_poi = POI.query.filter_by(poi_id=stop.poi_id).first()
    alternatives = []
    if current_poi:
        nearby = POI.query.filter(
            POI.category == current_poi.category,
            POI.poi_id != stop.poi_id,
        ).limit(3).all()
        for p in nearby:
            alternatives.append({
                'candidateId': f"alt_{p.poi_id}",
                'name': p.name,
                'categoryTags': p.tags[:3] if p.tags else [p.category],
                'priceRange': f'{max(0, p.price_per_capita - 10)}-{p.price_per_capita + 10}',
                'walkMinutes': 5,
                'reason': f'离当前位置更近，{p.user_quote or "不错的选择"}',
            })

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'stopId': stop_id,
            'alternatives': alternatives,
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>/stops/<stop_id>/replace', methods=['POST'])
def replace_stop(trip_id, stop_id):
    """替换行程节点"""
    data = request.get_json(silent=True) or {}
    candidate_id = data.get('candidateId', '')
    # candidateId 格式: alt_poi_XXX
    new_poi_id = candidate_id.replace('alt_', '') if candidate_id.startswith('alt_') else candidate_id

    stop = TripStop.query.filter_by(stop_id=stop_id, trip_id_fk=trip_id).first()
    if not stop:
        return jsonify({'code': 3002, 'message': '节点不存在', 'data': {}}), 404

    new_poi = POI.query.filter_by(poi_id=new_poi_id).first()
    if new_poi:
        stop.poi_id = new_poi_id
        stop.name = new_poi.name
        db.session.commit()

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'tripId': trip_id,
            'replacedStopId': stop_id,
            'newStopId': stop_id,
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>/reminders', methods=['GET'])
def get_reminders(trip_id):
    """获取出发提醒"""
    trip = Trip.query.filter_by(trip_id=trip_id).first()
    now = time.strftime('%Y-%m-%d')
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'tripId': trip_id,
            'today': [
                '暴晒 25°C',
                'RAC BAR 可能等位',
                '已预留缓冲 15 分钟',
            ],
            'packingChecklist': ['遮阳伞', '一台便携胶片相机', '充电宝'],
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>/favorite', methods=['POST'])
def favorite_trip(trip_id):
    """收藏/取消收藏行程"""
    data = request.get_json(silent=True) or {}
    is_favorite = data.get('favorite', True)
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {'tripId': trip_id, 'favorite': is_favorite},
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>/share', methods=['POST'])
def share_trip(trip_id):
    """生成分享链接"""
    share_code = uuid.uuid4().hex[:6].upper()
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'shareUrl': f'https://weekendgo.example.com/share/{trip_id}',
            'shareCode': share_code,
            'expiresAt': time.strftime('%Y-%m-%dT%H:%M:%S+08:00',
                                       time.localtime(time.time() + 7 * 86400)),
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@trip_bp.route('/api/v1/trip/<trip_id>/adjust', methods=['POST'])
def adjust_trip(trip_id):
    """行程一键微调"""
    data = request.get_json(silent=True) or {}
    mode = data.get('mode', 'reduce_walking')
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'tripId': trip_id,
            'adjusted': True,
            'changeSummary': ['替换 1 个远距离点位', '总步行时长从 25 分钟降到 14 分钟'],
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })
