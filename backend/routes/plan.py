"""
规划相关 API 路由
"""
import time
import uuid
from flask import Blueprint, request, jsonify
from models import db, POI, Trip, TripStop
from agent.planner import generate_plans

plan_bp = Blueprint('plan', __name__)


@plan_bp.route('/api/v1/plan/generate', methods=['POST'])
def generate():
    """生成候选方案"""
    data = request.get_json(silent=True) or {}

    time_type = data.get('timeType', '')
    activities = data.get('activities', [])
    geo_range = data.get('geographicRange', '')
    budget = data.get('budget', '')
    prompt_text = data.get('prompt', '')
    city = data.get('city', '上海')

    plans, error = generate_plans(
        time_type=time_type,
        activities=activities,
        geo_range=geo_range,
        budget=budget,
        prompt_text=prompt_text,
        city=city,
    )

    if error:
        return jsonify({
            'code': 2001,
            'message': f'方案生成失败: {error}',
            'data': {},
            'requestId': uuid.uuid4().hex[:16],
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        }), 500

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'plans': plans,
            'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@plan_bp.route('/api/v1/plan/regenerate', methods=['POST'])
def regenerate():
    """重新生成方案（排除已有 planId）"""
    data = request.get_json(silent=True) or {}
    exclude_ids = data.get('excludePlanIds', [])

    plans, error = generate_plans(
        time_type=data.get('timeType', ''),
        activities=data.get('activities', []),
        geo_range=data.get('geographicRange', ''),
        budget=data.get('budget', ''),
        prompt_text=data.get('prompt', ''),
        city=data.get('city', '上海'),
    )

    # 过滤掉已排除的方案
    plans = [p for p in plans if p.get('planId') not in exclude_ids]

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'plans': plans,
            'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@plan_bp.route('/api/v1/plan/validate', methods=['POST'])
def validate():
    """校验方案可行性"""
    data = request.get_json(silent=True) or {}
    plan_id = data.get('planId', '')
    date = data.get('date', '')
    start_time = data.get('startTime', '')

    # 简化实现：大部分方案都标记为可用
    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'valid': True,
            'warnings': [],
            'planId': plan_id,
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })
