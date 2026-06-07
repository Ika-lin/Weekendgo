"""
SQLAlchemy 数据模型
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON, Text, Float, Integer, String, Boolean, DateTime

db = SQLAlchemy()


class POI(db.Model):
    """地点/商户表"""
    __tablename__ = 'pois'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    poi_id = db.Column(String(50), unique=True, nullable=False, index=True)  # poi_322
    name = db.Column(String(100), nullable=False)
    category = db.Column(String(50), nullable=False)  # 咖啡/美食/艺术/户外/市集/书店/酒吧/甜品
    address = db.Column(String(300), nullable=False)
    lat = db.Column(Float, nullable=False)
    lng = db.Column(Float, nullable=False)
    price_per_capita = db.Column(Integer, default=0)  # 人均价格（元）
    rating = db.Column(Float, default=4.0)  # 评分 1-5
    business_status = db.Column(String(20), default='open')  # open/closed/temporary_closed
    open_hours = db.Column(String(100), default='周一至周日 09:00-21:00')
    phone = db.Column(String(20), default='')
    hero_image = db.Column(String(300), default='')
    tags = db.Column(JSON, default=list)  # ["电影主题", "安静翻阅", ...]
    about = db.Column(Text, default='')  # 简介
    impression_tags = db.Column(JSON, default=list)  # ["投影", "有咖啡厅", "环境很好"]
    suitable_for = db.Column(JSON, default=list)  # ["一个人阅读", "短暂停留"]
    attention = db.Column(JSON, default=list)  # ["周末下午可能人多"]
    user_quote = db.Column(String(300), default='')  # 用户引语
    district = db.Column(String(50), default='')
    neighborhood = db.Column(String(100), default='')
    # 新字段 — 丰富数据
    peak_hours = db.Column(String(50), default='')  # "11:30-13:00,17:30-19:30"
    facilities = db.Column(JSON, default=list)  # ["WiFi","停车","户外座位","儿童区"]
    must_try = db.Column(String(200), default='')  # "可丽饼,手冲咖啡"
    review_count = db.Column(Integer, default=0)  # 评论总数
    photo_count = db.Column(Integer, default=0)  # 照片数

    def to_dict(self):
        return {
            'poiId': self.poi_id, 'name': self.name, 'category': self.category,
            'address': self.address, 'lat': self.lat, 'lng': self.lng,
            'pricePerCapita': self.price_per_capita, 'rating': self.rating,
            'businessStatus': self.business_status, 'openHoursText': self.open_hours,
            'phone': self.phone, 'heroImage': self.hero_image,
            'tags': self.tags or [], 'about': self.about,
            'impressionTags': self.impression_tags or [],
            'suitableFor': self.suitable_for or [],
            'attention': self.attention or [], 'userQuote': self.user_quote,
            'peakHours': self.peak_hours,
            'facilities': self.facilities or [],
            'mustTry': self.must_try,
            'reviewCount': self.review_count,
            'photoCount': self.photo_count,
        }

    def to_card_dict(self):
        """用于发现页卡片的精简数据"""
        return {
            'itemId': self.poi_id,
            'name': self.name,
            'category': self.category,
            'badge': '热门' if self.rating >= 4.5 else '推荐',
            'subtitle': f'{self.district}，{self.neighborhood}',
            'layout': 'tall' if len(self.tags or []) > 2 else 'normal',
            'gradient': '#3a1f5d,#1f3c88',
        }


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(String(50), unique=True, nullable=False, index=True)
    nickname = db.Column(String(50), default='周末散步家')
    avatar = db.Column(String(300), default='')
    phone = db.Column(String(20), default='')
    password_hash = db.Column(String(200), default='')
    location = db.Column(String(50), default='上海')
    created_at = db.Column(DateTime, default=datetime.utcnow)

    def to_profile_dict(self):
        return {
            'userId': self.user_id,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'location': self.location,
            'stats': {
                'footprints': Footprint.query.filter_by(user_id=self.user_id).count(),
                'favorites': Favorite.query.filter_by(user_id=self.user_id).count(),
                'completedTrips': Trip.query.filter_by(user_id=self.user_id, status='completed').count(),
            }
        }


class Trip(db.Model):
    """行程表"""
    __tablename__ = 'trips'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    trip_id = db.Column(String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(String(50), nullable=False)
    plan_id = db.Column(String(50), default='')
    title = db.Column(String(200), nullable=False)
    city = db.Column(String(50), default='上海')
    date = db.Column(String(20), default='')  # 2026-06-04
    total_budget = db.Column(String(50), default='')
    status = db.Column(String(20), default='planned')  # planned/ongoing/completed/canceled
    created_at = db.Column(DateTime, default=datetime.utcnow)
    # JSON 字段存储行程元数据
    overview = db.Column(JSON, default=dict)  # 总路程/预算/交通方式
    route_map = db.Column(JSON, default=dict)  # 路线地图数据
    reminders = db.Column(JSON, default=dict)  # 提醒数据

    stops = db.relationship('TripStop', backref='trip', lazy=True, cascade='all, delete-orphan')

    def to_detail_dict(self):
        return {
            'tripId': self.trip_id,
            'title': self.title,
            'city': self.city,
            'date': self.date,
            'totalBudget': self.total_budget,
            'status': self.status,
            'overview': self.overview or {},
            'routeMap': self.route_map or {},
            'stops': sorted(
                [s.to_dict() for s in self.stops],
                key=lambda x: x['index']
            ),
        }


class TripStop(db.Model):
    """行程节点表"""
    __tablename__ = 'trip_stops'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    stop_id = db.Column(String(50), unique=True, nullable=False, index=True)
    trip_id_fk = db.Column(String(50), db.ForeignKey('trips.trip_id'), nullable=False)
    poi_id = db.Column(String(50), nullable=False)
    index = db.Column(Integer, default=0)
    time = db.Column(String(20), default='')  # 14:30
    name = db.Column(String(100), default='')
    desc = db.Column(Text, default='')
    duration_minutes = db.Column(Integer, default=45)
    done = db.Column(Boolean, default=False)
    checkin_time = db.Column(String(30), nullable=True)
    # 候选替换列表
    alternatives = db.Column(JSON, default=list)

    def to_dict(self):
        meta = self.alternatives if isinstance(self.alternatives, dict) else {}
        return {
            'stopId': self.stop_id,
            'poiId': self.poi_id,
            'index': self.index,
            'time': self.time,
            'endTime': meta.get('endTime', ''),
            'name': self.name,
            'desc': self.desc or '',
            'category': meta.get('category', ''),
            'address': meta.get('address', ''),
            'lat': meta.get('lat'),
            'lng': meta.get('lng'),
            'pricePerCapita': meta.get('pricePerCapita'),
            'rating': meta.get('rating'),
            'walkFromPrevious': meta.get('walkFromPrevious', 0),
            'tags': meta.get('tags', []),
            'queueInfo': meta.get('queueInfo'),
            'durationMinutes': self.duration_minutes,
            'done': self.done,
            'checkinTime': self.checkin_time,
            'alternatives': self.alternatives if isinstance(self.alternatives, list) else [],
        }


class Favorite(db.Model):
    """收藏表"""
    __tablename__ = 'favorites'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(String(50), nullable=False, index=True)
    poi_id = db.Column(String(50), nullable=False)
    trip_id = db.Column(String(50), default='')
    created_at = db.Column(DateTime, default=datetime.utcnow)


class Footprint(db.Model):
    """足迹表"""
    __tablename__ = 'footprints'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(String(50), nullable=False, index=True)
    poi_id = db.Column(String(50), nullable=False)
    trip_id = db.Column(String(50), default='')
    visited_at = db.Column(DateTime, default=datetime.utcnow)


class Event(db.Model):
    """周末活动/市集表"""
    __tablename__ = 'events'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(String(50), unique=True, nullable=False, index=True)
    emoji = db.Column(String(10), default='🎨')
    title = db.Column(String(200), nullable=False)
    subtitle = db.Column(String(200), default='')
    badge = db.Column(String(50), default='火热进行中')
    category = db.Column(String(50), default='市集')
    city = db.Column(String(50), default='上海')
    start_date = db.Column(String(20), default='')
    end_date = db.Column(String(20), default='')
    is_active = db.Column(Boolean, default=True)

    def to_dict(self):
        return {
            'eventId': self.event_id,
            'emoji': self.emoji,
            'title': self.title,
            'subtitle': self.subtitle,
            'badge': self.badge,
        }


class ConsumptionRecord(db.Model):
    """用户消费记录 - 模拟美团/大众点评消费数据"""
    __tablename__ = 'consumption_records'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    record_id = db.Column(String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(String(50), nullable=False, index=True)
    poi_id = db.Column(String(50), nullable=False)
    poi_name = db.Column(String(100), default='')
    category = db.Column(String(50), default='')
    amount = db.Column(Float, default=0.0)  # 消费金额
    rating = db.Column(Integer, default=4)  # 用户评分 1-5
    review = db.Column(Text, default='')
    date = db.Column(String(20), default='')
    time_of_day = db.Column(String(20), default='')
    with_friends = db.Column(JSON, default=list)
    tags = db.Column(JSON, default=list)
    deal_used = db.Column(String(100), default='')
    # 数据来源 + 情境
    source = db.Column(String(20), default='dinein')  # dinein/delivery/movie/hotel/bike/search
    location_context = db.Column(String(30), default='')  # 公司附近/家附近/周末出游/出差
    item_detail = db.Column(String(200), default='')  # 外卖菜品/电影名/酒店名 等具体内容

    def to_dict(self):
        return {
            'recordId': self.record_id, 'userId': self.user_id,
            'poiId': self.poi_id, 'poiName': self.poi_name,
            'category': self.category, 'amount': self.amount,
            'rating': self.rating, 'review': self.review,
            'date': self.date, 'timeOfDay': self.time_of_day,
            'withFriends': self.with_friends or [],
            'tags': self.tags or [], 'dealUsed': self.deal_used,
            'source': self.source, 'locationContext': self.location_context,
            'itemDetail': self.item_detail,
        }


class Deal(db.Model):
    """团购券/优惠券 - 模拟美团/大众点评团购"""
    __tablename__ = 'deals'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    deal_id = db.Column(String(50), unique=True, nullable=False, index=True)
    poi_id = db.Column(String(50), nullable=False, index=True)
    poi_name = db.Column(String(100), default='')
    title = db.Column(String(200), default='')  # 团购标题
    original_price = db.Column(Float, default=0.0)
    deal_price = db.Column(Float, default=0.0)
    discount = db.Column(String(20), default='')  # 折扣描述 如"7.5折"
    category = db.Column(String(50), default='')
    sold_count = db.Column(Integer, default=0)  # 已售数量
    expire_date = db.Column(String(20), default='')
    tags = db.Column(JSON, default=list)  # ["限时", "新客专享", "周末可用"]

    def to_dict(self):
        return {
            'dealId': self.deal_id,
            'poiId': self.poi_id,
            'poiName': self.poi_name,
            'title': self.title,
            'originalPrice': self.original_price,
            'dealPrice': self.deal_price,
            'discount': self.discount,
            'category': self.category,
            'soldCount': self.sold_count,
            'expireDate': self.expire_date,
            'tags': self.tags or [],
        }


class UserProfile(db.Model):
    """用户画像 - AI 根据消费记录自动总结"""
    __tablename__ = 'user_profiles'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(String(50), unique=True, nullable=False, index=True)
    nickname = db.Column(String(50), default='')
    # 消费偏好
    favorite_categories = db.Column(JSON, default=list)  # [{"category":"咖啡","count":12,"avgAmount":45}]
    favorite_districts = db.Column(JSON, default=list)  # [{"district":"徐汇","count":8}]
    favorite_tags = db.Column(JSON, default=list)  # 常出现的标签
    avg_spending = db.Column(Float, default=0.0)  # 平均消费
    total_spending = db.Column(Float, default=0.0)
    total_visits = db.Column(Integer, default=0)
    # 行为特征
    preferred_time = db.Column(String(20), default='下午')  # 最常消费时段
    solo_ratio = db.Column(Float, default=0.0)  # 独自消费比例
    social_ratio = db.Column(Float, default=0.0)  # 社交消费比例
    rating_avg = db.Column(Float, default=4.0)  # 给商家的平均评分
    # AI 生成的画像描述
    persona_summary = db.Column(Text, default='')
    persona_tags = db.Column(JSON, default=list)  # ["咖啡控", "安福路常客", "Brunch爱好者"]
    # 社交画像
    social_style = db.Column(String(50), default='')
    group_size_preference = db.Column(Integer, default=2)
    interested_categories_for_social = db.Column(JSON, default=list)
    # 用户自述习惯（AI 对话收集）—— 与消费画像合并为统一画像
    work_days = db.Column(Integer, default=5)
    off_work_time = db.Column(String(10), default='')
    commute_minutes = db.Column(Integer, default=0)
    free_slots = db.Column(JSON, default=list)  # ["周六下午","周日"]
    dietary = db.Column(JSON, default=list)  # ["不吃辣","减肥中"]
    mobility = db.Column(String(20), default='')
    budget_comfort = db.Column(Integer, default=0)
    user_notes = db.Column(Text, default='')
    habits_updated_at = db.Column(String(20), default='')
    # 位置画像
    home_area = db.Column(String(50), default='')  # 家住哪个区
    work_area = db.Column(String(50), default='')  # 公司在哪个区

    def to_dict(self):
        return {
            'userId': self.user_id, 'nickname': self.nickname,
            # 消费画像（数据驱动）
            'favoriteCategories': self.favorite_categories or [],
            'favoriteDistricts': self.favorite_districts or [],
            'favoriteTags': self.favorite_tags or [],
            'avgSpending': self.avg_spending, 'totalSpending': self.total_spending,
            'totalVisits': self.total_visits, 'preferredTime': self.preferred_time,
            'soloRatio': self.solo_ratio, 'socialRatio': self.social_ratio,
            'ratingAvg': self.rating_avg,
            'personaSummary': self.persona_summary,
            'personaTags': self.persona_tags or [],
            'socialStyle': self.social_style,
            'groupSizePreference': self.group_size_preference,
            'interestedCategoriesForSocial': self.interested_categories_for_social or [],
            # 用户自述习惯（对话收集）
            'workDays': self.work_days, 'offWorkTime': self.off_work_time,
            'commuteMinutes': self.commute_minutes,
            'freeSlots': self.free_slots or [], 'dietary': self.dietary or [],
            'mobility': self.mobility, 'budgetComfort': self.budget_comfort,
            'userNotes': self.user_notes,
            'homeArea': self.home_area, 'workArea': self.work_area,
        }


class SocialConnection(db.Model):
    """社交关系 - 好友/组局记录"""
    __tablename__ = 'social_connections'

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    connection_id = db.Column(String(50), unique=True, nullable=False, index=True)
    user_id_1 = db.Column(String(50), nullable=False)
    user_id_2 = db.Column(String(50), nullable=False)
    common_pois = db.Column(JSON, default=list)  # 共同去过的地方
    common_categories = db.Column(JSON, default=list)  # 共同喜欢的类别
    match_score = db.Column(Float, default=0.0)  # 匹配分数
    last_interaction = db.Column(String(20), default='')

    def to_dict(self):
        return {
            'connectionId': self.connection_id,
            'userId1': self.user_id_1,
            'userId2': self.user_id_2,
            'commonPois': self.common_pois or [],
            'commonCategories': self.common_categories or [],
            'matchScore': self.match_score,
        }
