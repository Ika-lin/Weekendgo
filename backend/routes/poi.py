"""
POI 详情 API 路由
"""
import time
import uuid
from flask import Blueprint, request, jsonify
from models import db, POI

poi_bp = Blueprint('poi', __name__)


@poi_bp.route('/api/v1/pois/<poi_id>', methods=['GET'])
def get_poi_detail(poi_id):
    """获取地点详情"""
    poi = POI.query.filter_by(poi_id=poi_id).first()
    if not poi:
        return jsonify({
            'code': 1003,
            'message': '地点不存在',
            'data': {},
            'requestId': uuid.uuid4().hex[:16],
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        }), 404

    data = poi.to_dict()
    # 补充额外字段
    data.update({
        'heroImage': f'https://picsum.photos/seed/{poi_id}/400/300',
        'impressionTags': poi.impression_tags or ['环境很好', '值得一去', '拍照好看'],
        'userQuote': poi.user_quote or '店内氛围很好，适合和朋友一起来',
        'suitableFor': poi.suitable_for or ['朋友聚会', '短暂停留'],
        'attention': poi.attention or ['周末下午可能人多'],
    })

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': data,
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@poi_bp.route('/api/v1/pois/<poi_id>/review-insights', methods=['GET'])
def get_review_insights(poi_id):
    """获取地点评论洞察"""
    poi = POI.query.filter_by(poi_id=poi_id).first()
    if not poi:
        return jsonify({'code': 1003, 'message': '地点不存在'}), 404

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'poiId': poi_id,
            'rating': poi.rating,
            'reviewCount': 326,
            'impressionTags': poi.impression_tags or ['环境好', '服务佳'],
            'highlights': ['适合短暂休息', '拍照友好'],
            'riskNotes': ['周末 15:00-17:00 可能排队'],
            'sampleQuote': poi.user_quote or '氛围很好，值得再去',
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@poi_bp.route('/api/v1/pois/<poi_id>/arrival-hints', methods=['GET'])
def get_arrival_hints(poi_id):
    """获取到店提醒"""
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'poiId': poi_id,
            'stopId': request.args.get('stopId', ''),
            'queueRisk': 'medium',
            'bestArrivalWindow': '14:00-15:00',
            'trafficNote': '周边停车紧张，建议步行或地铁',
            'weatherImpact': '晴天较晒，建议带遮阳伞',
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@poi_bp.route('/api/v1/pois/<poi_id>/contact', methods=['GET'])
def get_contact(poi_id):
    """获取地点联系方式"""
    poi = POI.query.filter_by(poi_id=poi_id).first()
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'poiId': poi_id,
            'phoneMasked': '021-xxxx-xxxx',
            'phone': poi.phone if poi else '021-12345678',
            'canCall': True,
            'callWindow': '09:00-19:00',
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@poi_bp.route('/api/v1/pois/<poi_id>/actions', methods=['POST'])
def report_action(poi_id):
    """上报地点详情页交互"""
    data = request.get_json(silent=True) or {}
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {'recorded': True},
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })
