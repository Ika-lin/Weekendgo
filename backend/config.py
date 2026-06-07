"""
美团黑客松 - 后端配置
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 加载 .env 文件
env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = value

# SQLite 数据库
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'meituan_v2.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

# DeepSeek API
# 模型: deepseek-v4-flash (¥1/M in, ¥2/M out, 1M ctx, 支持Tool Call)
#       deepseek-v4-pro  (¥3/M in, ¥6/M out, 1M ctx, 支持思考模式)
# 旧名 deepseek-chat/deepseek-reasoner 将于 2026/07/24 弃用
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'your-deepseek-api-key')
DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
DEEPSEEK_MODEL = 'deepseek-v4-pro'  # 最强模型, 支持思考模式 + function calling

# Flask
DEBUG = True
SECRET_KEY = 'meituan-hackathon-2026'
JSON_AS_ASCII = False  # 支持中文输出

# 城市配置
DEFAULT_CITY = '上海'
DEFAULT_CENTER = {'lat': 31.2123, 'lng': 121.4392}  # 武康路附近
