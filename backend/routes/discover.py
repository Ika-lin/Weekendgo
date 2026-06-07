"""
发现页 API 路由
"""
import time
import uuid
from flask import Blueprint, request, jsonify
from models import db, POI, Event

discover_bp = Blueprint('discover', __name__)


@discover_bp.route('/api/v1/discover/categories', methods=['GET'])
def get_categories():
    """获取发现页分类"""
    # 动态从数据库获取所有类别
    cats = [row[0] for row in db.session.query(POI.category).distinct().all()]
    if not cats:
        cats = ['全部', '美食', '艺术', '户外', '市集', '咖啡', '书店', '酒吧', '甜品']
    else:
        cats.insert(0, '全部')

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {'categories': cats},
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@discover_bp.route('/api/v1/discover/places', methods=['GET'])
def get_places():
    """获取发现页内容（瀑布流卡片）"""
    category = request.args.get('category', '全部')
    limit = int(request.args.get('limit', 20))
    cursor = request.args.get('cursor', '')

    query = POI.query.filter(POI.business_status == 'open')
    if category != '全部':
        query = query.filter(POI.category == category)

    pois = query.limit(limit).all()

    items = [p.to_card_dict() for p in pois]
    next_cursor = f"c_{int(time.time())}" if len(items) == limit else ''

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'items': items,
            'nextCursor': next_cursor,
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@discover_bp.route('/api/v1/discover/events', methods=['GET'])
def get_events():
    """获取活动列表"""
    city = request.args.get('city', '上海')
    limit = int(request.args.get('limit', 10))

    events = Event.query.filter_by(city=city, is_active=True).limit(limit).all()

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'events': [e.to_dict() for e in events],
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })
