"""
Intent router for the Weekendgo agent.

This is deliberately deterministic. LLMs may enrich language later, but the
product flow starts here so core behavior is predictable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


CATEGORIES = ["咖啡", "美食", "艺术", "户外", "市集", "书店", "酒吧", "甜品", "亲子"]
AREAS = [
    "武康路", "安福路", "法租界", "新天地", "外滩", "愚园路", "西岸", "陆家嘴",
    "衡山路", "淮海中路", "打浦桥", "巨鹿路", "永康路", "徐汇", "静安", "黄浦",
    "长宁", "浦东", "虹口", "普陀",
]
PLAN_WORDS = ["规划", "安排", "路线", "行程", "周末", "下午", "晚上", "半天", "一天", "带我", "约会"]
SEARCH_WORDS = ["推荐", "找", "附近", "想去", "有没有", "看看", "好去处"]
LEISURE_WORDS = ["逛", "走走", "散步", "闲逛", "转转", "玩", "出去", "出门"]
CONFIRM_WORDS = ["好的", "行", "可以", "确认", "保存", "就这个", "按这个", "搞定"]
MODIFY_WORDS = ["换", "替换", "改改", "调整一下", "删掉"]
PROFILE_WORDS = ["我喜欢", "我不吃", "不吃", "下班", "通勤", "偏好", "以后记住", "记住", "住在", "家在", "公司在", "上班在", "工作在"]
ONBOARDING_WORDS = ["首次登录", "正在了解你", "画像生成", "生成画像", "onboarding", "新用户"]


@dataclass
class IntentResult:
    intent: str
    confidence: float
    slots: dict = field(default_factory=dict)
    needs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "slots": self.slots,
            "needs": self.needs,
        }


def route_intent(message: str, history: list[dict] | None = None) -> dict:
    text = (message or "").strip()
    history = history or []
    slots = _extract_slots(text)

    if not text:
        return IntentResult("empty", 1.0).to_dict()

    if text == "__greeting__":
        return IntentResult("greeting", 0.99).to_dict()

    if _has_any(text, ONBOARDING_WORDS):
        return IntentResult("onboarding_profile", 0.94, slots).to_dict()

    if _is_confirm_text(text):
        return IntentResult("confirm_plan", 0.84, slots).to_dict()

    if _has_any(text, MODIFY_WORDS):
        return IntentResult("modify_plan", 0.78, slots).to_dict()

    has_plan_signal = _has_any(text, PLAN_WORDS)
    has_search_signal = _has_any(text, SEARCH_WORDS)
    has_leisure_signal = _has_any(text, LEISURE_WORDS)
    has_category = bool(slots.get("category"))
    has_time_budget = bool(slots.get("budget") or slots.get("timeText") or slots.get("partySize") or slots.get("range"))

    if _has_any(text, PROFILE_WORDS) and not _has_any(text, CONFIRM_WORDS):
        return IntentResult("update_profile", 0.82, slots).to_dict()

    if has_plan_signal and (has_category or has_time_budget or len(text) > 8):
        return IntentResult("plan_trip", 0.86, slots, _missing_plan_needs(slots)).to_dict()

    if has_leisure_signal and (has_time_budget or has_category or slots.get("area")):
        return IntentResult("plan_trip", 0.78, slots, _missing_plan_needs(slots)).to_dict()

    if has_search_signal or has_category or slots.get("area"):
        return IntentResult("find_place", 0.74, slots).to_dict()

    return IntentResult("smalltalk", 0.55, slots).to_dict()


def _extract_slots(text: str) -> dict:
    slots: dict = {}

    categories = [cat for cat in CATEGORIES if cat in text]
    if categories:
        slots["category"] = categories[0]
        slots["categories"] = categories

    areas = [area for area in AREAS if area in text]
    if areas:
        slots["area"] = areas[0]
        slots["areas"] = areas

    budget = _extract_budget(text)
    if budget:
        slots["budget"] = budget

    party_size = _extract_party_size(text)
    if party_size:
        slots["partySize"] = party_size

    time_text = _extract_time_text(text)
    if time_text:
        slots["timeText"] = time_text

    if any(w in text for w in ["不吃辣", "清淡", "减肥", "低脂", "素食"]):
        slots["dietary"] = [w for w in ["不吃辣", "清淡", "减肥", "低脂", "素食"] if w in text]

    # 亲子/儿童场景
    if any(w in text for w in ["孩子", "小朋友", "小孩", "亲子", "带娃"]):
        slots["category"] = slots.get("category") or "亲子"
        if not party_size:
            slots["partySize"] = 3  # 默认一家三口

    # 距离约束
    if any(w in text for w in ["别离家太远", "别太远", "离家近", "近一点", "就近", "不要太远"]):
        slots["range"] = "就近玩玩"

    if any(w in text for w in ["少走路", "不想走", "地铁", "打车", "开车", "可以跨区", "跨区"]):
        slots["mobility"] = next(w for w in ["少走路", "不想走", "地铁", "打车", "开车", "可以跨区", "跨区"] if w in text)
        if slots["mobility"] in ("可以跨区", "跨区"):
            slots["range"] = "可以跨区"

    return slots


def _extract_budget(text: str) -> int | None:
    match = re.search(r"(\d{2,4})\s*(元|块|预算|以内|左右)?", text)
    if match:
        value = int(match.group(1))
        if 20 <= value <= 5000:
            return value
    return None


def _extract_party_size(text: str) -> int | None:
    match = re.search(r"(\d+)\s*(个人|人|位)", text)
    if match:
        value = int(match.group(1))
        if 1 <= value <= 20:
            return value
    if "一个人" in text or "自己" in text:
        return 1
    if "情侣" in text or "约会" in text or "两个人" in text:
        return 2
    return None


def _extract_time_text(text: str) -> str | None:
    for token in ["今天", "明天", "周五", "周六", "周日", "周末", "上午", "中午", "下午", "晚上", "夜宵"]:
        if token in text:
            return token
    match = re.search(r"([01]?\d|2[0-3])[:点][0-5]?\d?", text)
    return match.group(0) if match else None


def _missing_plan_needs(slots: dict) -> list[str]:
    needs = []
    if not slots.get("timeText"):
        needs.append("time")
    if not slots.get("budget"):
        needs.append("budget")
    if not slots.get("category") and not slots.get("area"):
        needs.append("preference")
    return needs[:2]


def _has_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def _is_confirm_text(text: str) -> bool:
    if len(text.strip()) > 12 and _has_any(text, PLAN_WORDS + SEARCH_WORDS + LEISURE_WORDS):
        return False
    strong = ["确认", "保存", "就这个", "按这个", "搞定"]
    if any(word in text for word in strong):
        return True
    if any(word in text for word in ["跨区", "少走路", "不想走", "地铁", "打车", "开车"]):
        return False
    short_confirms = {"好的", "好", "行", "可以", "ok", "OK"}
    return text.strip() in short_confirms or (len(text.strip()) <= 4 and _has_any(text, ["好的", "行", "可以"]))
