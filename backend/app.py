"""
美团黑客松 - Weekendgo 后端入口
"""
import os
import sys
import io
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# 解决 Windows GBK 编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY, DEBUG, JSON_AS_ASCII
from models import db

# 确保 data 目录存在
os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web', 'dist'))


def create_app():
    frontend_dist = FRONTEND_DIST if os.path.exists(os.path.join(FRONTEND_DIST, 'index.html')) else None
    app = Flask(__name__, static_folder=None)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['JSON_AS_ASCII'] = JSON_AS_ASCII

    CORS(app)  # 允许跨域
    db.init_app(app)

    # 注册路由
    from routes.plan import plan_bp
    from routes.trip import trip_bp
    from routes.discover import discover_bp
    from routes.user import user_bp
    from routes.poi import poi_bp
    from routes.chat import chat_bp

    app.register_blueprint(plan_bp)
    app.register_blueprint(trip_bp)
    app.register_blueprint(discover_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(poi_bp)
    app.register_blueprint(chat_bp)

    # 健康检查
    @app.route('/api/v1/health')
    def health():
        return jsonify({'code': 0, 'message': 'ok', 'data': {'status': 'healthy'}})

    @app.route('/')
    def serve_index():
        if frontend_dist:
            return send_from_directory(frontend_dist, 'index.html')
        return jsonify({
            'code': 0,
            'message': 'Weekendgo API is running. Build web/dist to enable the frontend.',
            'data': {'apiBase': '/api/v1'}
        })

    @app.route('/<path:path>')
    def serve_frontend(path):
        if path.startswith('api/'):
            return jsonify({'code': 404, 'message': 'API route not found', 'data': None}), 404
        if frontend_dist:
            candidate = os.path.join(frontend_dist, path)
            if os.path.exists(candidate) and os.path.isfile(candidate):
                return send_from_directory(frontend_dist, path)
            return send_from_directory(frontend_dist, 'index.html')
        return jsonify({'code': 404, 'message': 'Frontend is not built', 'data': None}), 404

    # 初始化数据库
    with app.app_context():
        db.create_all()
        # 如果数据库为空，自动填充 mock 数据
        from models import POI
        if POI.query.count() == 0:
            print('[Init] 数据库为空，正在填充 Mock 数据...')
            from seed import seed_all
            seed_all()
            print('[Init] Mock 数据填充完成！')

    return app


if __name__ == '__main__':
    app = create_app()
    print('[Weekendgo] 后端启动: http://localhost:5000')
    print('[Weekendgo] API Base: http://localhost:5000/api/v1')
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)
