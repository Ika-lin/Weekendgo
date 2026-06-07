"""
Agent 对话 + AI 群聊 API 路由
"""
import time
import uuid
from flask import Blueprint, request, jsonify
from agent.agent import agent_chat, friend_chat, group_chat, group_synthesize
from agent.response_schema import public_payload

chat_bp = Blueprint('chat', __name__)

# 服务端会话存储（简单内存存储，demo级别）
_sessions = {}


def _session_key(session_id, user_id=None):
    return f"{user_id or 'global'}:{session_id or 'default'}"


def _get_or_create_session(session_id, user_id=None):
    key = _session_key(session_id, user_id)
    if key not in _sessions:
        _sessions[key] = {
            "history": [],
            "group_history": [],
            "agent_state": {},
        }
    return _sessions[key]


@chat_bp.route('/api/v1/chat', methods=['POST'])
def chat():
    """
    与主 Agent 对话
    Request: { message, sessionId? }
    Response: { reply, toolCalls, trip }
    """
    data = request.get_json(silent=True) or {}
    user_message = data.get('message', '').strip()
    session_id = data.get('sessionId', 'default')
    user_id = data.get('userId', 'u_demo_001')
    action = data.get('action', '')

    if not user_message:
        return jsonify({
            'code': 1001,
            'message': '消息不能为空',
            'data': {},
            'requestId': uuid.uuid4().hex[:16],
        }), 400

    sess = _get_or_create_session(session_id, user_id)

    # 调用 Agent
    agent_message = f"onboarding {user_message}" if action == 'onboarding_profile' else user_message
    result = agent_chat(agent_message, sess["history"], user_id=user_id, state=sess["agent_state"])

    # 更新会话历史
    sess["history"].append({"role": "user", "content": user_message})
    sess["history"].append({"role": "assistant", "content": result["reply"]})

    # 限制历史长度
    if len(sess["history"]) > 20:
        sess["history"] = sess["history"][-20:]

    payload = public_payload(result)
    payload['sessionId'] = session_id
    payload['userId'] = user_id

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': payload,
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@chat_bp.route('/api/v1/chat/reset', methods=['POST'])
def reset_chat():
    """重置会话"""
    data = request.get_json(silent=True) or {}
    session_id = data.get('sessionId', 'default')
    user_id = data.get('userId')
    if user_id:
        _sessions.pop(_session_key(session_id, user_id), None)
    else:
        for key in [k for k in _sessions if k.endswith(f":{session_id}")]:
            _sessions.pop(key, None)
    return jsonify({
        'code': 0,
        'message': '会话已重置',
        'data': {},
        'requestId': uuid.uuid4().hex[:16],
    })


@chat_bp.route('/api/v1/group-chat', methods=['POST'])
def group_chat_endpoint():
    """
    AI 群聊协调 - 小薇读取群成员画像，推进共识或引导群规划。
    Request: { message, sessionId?, user_ids? }
    Response: { messages: [{persona, emoji, color, text}], trip, metadata }
    """
    data = request.get_json(silent=True) or {}
    user_message = data.get('message', '').strip()
    session_id = data.get('sessionId', 'default')
    action = data.get('action', 'chat')  # 'chat' or 'synthesize'
    user_ids = data.get('user_ids') or data.get('userIds') or []

    if not user_message and action != 'synthesize':
        return jsonify({
            'code': 1001,
            'message': '消息不能为空',
            'data': {},
            'requestId': uuid.uuid4().hex[:16],
        }), 400

    sess = _get_or_create_session(session_id, "group")

    if action == 'synthesize':
        # 汇总群聊，生成最终方案
        result = group_synthesize(sess["group_history"])
        return jsonify({
            'code': 0,
            'message': 'ok',
            'data': {
                'reply': result['reply'],
                'trip': result.get('trip'),
                'intent': result.get('intent'),
                'actions': result.get('actions', []),
                'mode': 'synthesize',
            },
            'requestId': uuid.uuid4().hex[:16],
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
        })

    # 群聊
    sess["group_history"].append({"role": "user", "content": user_message})
    result = group_chat(user_message, sess["group_history"], user_ids=user_ids)

    # 更新历史
    for m in result['messages']:
        sess["group_history"].append({
            "role": "assistant",
            "content": f"[{m['persona']}] {m['text']}",
        })

    if len(sess["group_history"]) > 30:
        sess["group_history"] = sess["group_history"][-30:]

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'messages': result['messages'],
            'trip': result.get('trip'),
            'intent': result.get('intent'),
            'actions': result.get('actions', []),
            'metadata': result.get('metadata', {}),
            'sessionId': session_id,
        },
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@chat_bp.route('/api/v1/friend-chat', methods=['POST'])
def friend_chat_endpoint():
    """
    AI 私聊协调 - 小薇读取双方画像，帮助用户和单个好友沟通/规划。
    Request: { message, userId, friendId, sessionId? }
    """
    data = request.get_json(silent=True) or {}
    user_message = data.get('message', '').strip()
    user_id = data.get('userId') or data.get('user_id') or 'u_demo_001'
    friend_id = data.get('friendId') or data.get('friend_id') or 'u_demo_002'
    session_id = data.get('sessionId', 'default')

    if not user_message:
        return jsonify({
            'code': 1001,
            'message': '消息不能为空',
            'data': {},
            'requestId': uuid.uuid4().hex[:16],
        }), 400

    sess = _get_or_create_session(session_id, f"friend:{user_id}:{friend_id}")
    sess["history"].append({"role": "user", "content": user_message})
    result = friend_chat(user_message, sess["history"], user_id=user_id, friend_id=friend_id)
    sess["history"].append({"role": "assistant", "content": result["reply"]})

    if len(sess["history"]) > 24:
        sess["history"] = sess["history"][-24:]

    result['sessionId'] = session_id
    result['userId'] = user_id
    result['friendId'] = friend_id

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': result,
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@chat_bp.route('/api/v1/group-chat/plan', methods=['POST'])
def group_plan():
    """
    多 Agent 协商规划 — 群聊场景
    Request: { user_ids: ["u_demo_001","u_demo_002",...], message: "用户消息" }
    每个成员的画像从数据库动态生成，协调 Agent 协商出统一方案。
    """
    data = request.get_json(silent=True) or {}
    user_ids = data.get('user_ids', [])
    user_message = data.get('message', '')
    session_id = data.get('sessionId', 'default')

    if not user_ids:
        return jsonify({'code': 1001, 'message': 'user_ids 不能为空', 'data': {}}), 400

    from agent.multi_agent import plan_for_group
    result = plan_for_group(user_ids, user_message, session_id)

    return jsonify({
        'code': 0, 'message': 'ok',
        'data': result,
        'requestId': uuid.uuid4().hex[:16],
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
    })


@chat_bp.route('/api/v1/chat/agent-tools', methods=['GET'])
def list_tools():
    """列出 Agent 所有可用工具"""
    from agent.tools import TOOL_DEFINITIONS
    tools_info = []
    for t in TOOL_DEFINITIONS:
        f = t['function']
        tools_info.append({
            'name': f['name'],
            'description': f['description'],
            'parameters': f.get('parameters', {}).get('properties', {}),
        })

    return jsonify({
        'code': 0,
        'message': 'ok',
        'data': {
            'count': len(tools_info),
            'tools': tools_info,
        },
        'requestId': uuid.uuid4().hex[:16],
    })


@chat_bp.route('/api/v1/chat/memories', methods=['GET'])
def list_memories():
    """列出 Agent 所有记忆"""
    from agent.memory import get_memory
    user_id = request.args.get('userId') or request.args.get('user_id')
    mem = get_memory()
    memories = mem.list_all(user_id=user_id)
    return jsonify({
        'code': 0, 'message': 'ok',
        'data': {
            'count': len(memories),
            'userId': user_id,
            'memories': memories,
        },
        'requestId': uuid.uuid4().hex[:16],
    })


@chat_bp.route('/api/v1/chat/memories', methods=['POST'])
def add_memory():
    """手动添加记忆"""
    data = request.get_json(silent=True) or {}
    from agent.memory import get_memory
    mem = get_memory()
    user_id = data.get('userId') or data.get('user_id')
    mem.remember(
        key=data.get('key', ''),
        content=data.get('content', ''),
        importance=data.get('importance', 0.5),
        tags=data.get('tags', []),
        user_id=user_id,
    )
    return jsonify({'code': 0, 'message': 'ok', 'data': {'remembered': True, 'userId': user_id}})
