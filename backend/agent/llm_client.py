"""
DeepSeek API 客户端封装
"""
import json
import requests
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


def call_deepseek(
    messages,
    temperature=0.7,
    max_tokens=2048,
    response_format=None,
    tools=None,
    timeout_seconds=90,
):
    """
    调用 DeepSeek Chat API

    Args:
        messages: OpenAI 格式的消息列表
        temperature: 温度参数
        max_tokens: 最大输出 token
        response_format: 可选 {"type": "json_object"} 强制 JSON 输出
        tools: 可选工具定义列表 (OpenAI function-calling 格式)
        timeout_seconds: 请求超时秒数

    Returns:
        (content_text, error_string)
    """
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == 'your-deepseek-api-key':
        return None, 'DeepSeek API Key 未配置。请设置环境变量 DEEPSEEK_API_KEY'

    url = f'{DEEPSEEK_BASE_URL}/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': DEEPSEEK_MODEL,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }
    if response_format:
        payload['response_format'] = response_format
    if tools:
        payload['tools'] = tools
        payload['tool_choice'] = 'auto'

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
        if resp.status_code != 200:
            err_detail = resp.text[:300] if resp.text else 'no body'
            return None, f'DeepSeek API {resp.status_code}: {err_detail}'
        data = resp.json()
        message = data['choices'][0]['message']

        # 处理 tool_calls 响应
        if message.get('tool_calls'):
            # 返回 JSON 格式的 tool_calls 以便解析
            import json
            result = {
                'tool_calls': [
                    {
                        'id': tc.get('id', ''),
                        'name': tc['function']['name'],
                        'arguments': json.loads(tc['function']['arguments']) if tc['function'].get('arguments') else {},
                    }
                    for tc in message['tool_calls']
                ]
            }
            return json.dumps(result, ensure_ascii=False), None

        content = message.get('content', '')
        return content, None
    except requests.exceptions.Timeout:
        return None, 'DeepSeek API 请求超时'
    except requests.exceptions.RequestException as e:
        return None, f'DeepSeek API 请求失败: {str(e)}'
    except (KeyError, IndexError) as e:
        return None, f'DeepSeek API 响应解析失败: {str(e)}'


def parse_json_response(content):
    """尝试从 LLM 响应中解析 JSON"""
    try:
        return json.loads(content), None
    except json.JSONDecodeError:
        # 尝试提取 ```json ... ``` 中的内容
        if '```json' in content:
            try:
                start = content.index('```json') + 7
                end = content.index('```', start)
                return json.loads(content[start:end].strip()), None
            except (ValueError, json.JSONDecodeError):
                pass
        # 尝试找到第一个 { 和最后一个 }
        try:
            start = content.index('{')
            end = content.rindex('}') + 1
            return json.loads(content[start:end]), None
        except (ValueError, json.JSONDecodeError):
            pass
        return None, f'无法解析 LLM 返回的 JSON: {content[:200]}...'
