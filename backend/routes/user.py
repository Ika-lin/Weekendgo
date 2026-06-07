"""
用户资产 API 路由
"""
import time
import uuid
from flask import Blueprint, request, jsonify
from models import db, User, Favorite, Footprint, POI

user_bp = Blueprint('user', __name__)


@user_bp.route('/api/v1/user/profile', methods=['GET'])
def get_profile():
    """获取我的页信息"""
    user_id = request.args.get('userId', 'u_demo_001')
    user = User.query.filter_by(user_id=user_id).first()
    from agent.profile_service import get_structured_profile

    profile = get_structured_profile(user_id)

    if not user:
        return jsonify({
            'code': 0,
            'message': 'ok',
            'data': {
                **profile,
                'userId': user_id,
                'avatar': profile.get('avatar', ''),
                'stats': {
                    'footprints': 0,
                    'favorites': 0,
                    'completedTrips': 0,
                },
            },
            'requestId': uuid.uuid4().hex[:16],
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        })

    data = {
        **profile,
        **user.to_profile_dict(),
        'nickname': profile.get('nickname') or user.nickname,
    }

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': data,
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@user_bp.route('/api/v1/user/favorites', methods=['GET'])
def get_favorites():
    """获取用户收藏"""
    user_id = request.args.get('userId', 'u_demo_001')
    favs = Favorite.query.filter_by(user_id=user_id).all()
    pois = []
    for f in favs:
        poi = POI.query.filter_by(poi_id=f.poi_id).first()
        if poi:
            pois.append(poi.to_dict())

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {'favorites': pois},
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@user_bp.route('/api/v1/user/favorites/<poi_id>', methods=['POST', 'DELETE'])
def toggle_favorite(poi_id):
    """收藏/取消收藏 POI"""
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId', 'u_demo_001')

    if request.method == 'POST':
        existing = Favorite.query.filter_by(user_id=user_id, poi_id=poi_id).first()
        if not existing:
            db.session.add(Favorite(user_id=user_id, poi_id=poi_id))
            db.session.commit()
        return jsonify({
            'code': 0, 'message': 'ok',
            'data': {'favorited': True},
            'requestId': uuid.uuid4().hex[:16],
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        })
    else:
        Favorite.query.filter_by(user_id=user_id, poi_id=poi_id).delete()
        db.session.commit()
        return jsonify({
            'code': 0, 'message': 'ok',
            'data': {'favorited': False},
            'requestId': uuid.uuid4().hex[:16],
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        })


@user_bp.route('/api/v1/user/footprints', methods=['GET'])
def get_footprints():
    """获取用户足迹"""
    user_id = request.args.get('userId', 'u_demo_001')
    footprints = Footprint.query.filter_by(user_id=user_id).all()
    pois = []
    for fp in footprints:
        poi = POI.query.filter_by(poi_id=fp.poi_id).first()
        if poi:
            pois.append(poi.to_dict())

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {'footprints': pois},
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@user_bp.route('/api/v1/user/checkins', methods=['POST'])
def checkin():
    """用户打卡"""
    data = request.get_json(silent=True) or {}
    user_id = data.get('userId', 'u_demo_001')
    poi_id = data.get('poiId', '')
    trip_id = data.get('tripId', '')

    db.session.add(Footprint(user_id=user_id, poi_id=poi_id, trip_id=trip_id))
    db.session.commit()

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {'checkedIn': True},
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@user_bp.route('/api/v1/user/<user_id>/footprints', methods=['GET'])
def get_user_footprints(user_id):
    """获取用户真实到店消费足迹（从消费记录）"""
    from models import ConsumptionRecord
    limit = int(request.args.get('limit', 30))
    records = (
        ConsumptionRecord.query
        .filter_by(user_id=user_id)
        .filter(ConsumptionRecord.source.in_(['dinein', 'movie', 'hotel']))
        .order_by(ConsumptionRecord.date.desc())
        .limit(limit).all()
    )
    items = [{
        'date': r.date,
        'timeOfDay': r.time_of_day,
        'poiName': r.poi_name,
        'category': r.category,
        'amount': r.amount,
        'rating': r.rating,
        'review': r.review,
        'withFriends': r.with_friends or [],
        'source': r.source,
        'locationContext': r.location_context,
        'itemDetail': r.item_detail,
    } for r in records]

    return jsonify({
        'code': 0, 'message': 'ok',
        'data': {
            'userId': user_id,
            'total': len(items),
            'footprints': items,
        },
        'requestId': uuid.uuid4().hex[:16],
    })
