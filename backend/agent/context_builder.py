"""
ContextBuilder — 统一上下文组装（产品落地级）

每一轮对话的 LLM prompt 由这里统一构建：
  system_prompt + profile_block + memory_block + history_block + user_message
"""
from __future__ import annotations

from agent.memory import get_memory
from agent.profile_service import compact_profile_text, get_structured_profile

SYSTEM_PROMPT = (
    "你是 Weekendgo，美团旗下的周末出行 AI 助手。"
    "你帮用户安排周末闲时生活：搜店、排路线、查团购、看排队、一键预订。"
    "风格温暖松弛，像懂生活的本地朋友。"
    "不凭空编造地点，推荐基于搜索数据。"
)


class ContextBlock:
    """组装后的上下文"""
    def __init__(self, system: str = "", profile: str = "",
                 memory: str = "", history: str = "", user: str = "",
                 user_id: str = "u_demo_001", profile_data: dict | None = None):
        self.system = system
        self.profile = profile
        self.memory = memory
        self.history = history
        self.user = user
        self.user_id = user_id
        self.profile_data = profile_data or {}

    def build(self, with_history: bool = True) -> str:
        parts = [self.system]
        if self.profile:
            parts.append(self.profile)
        if self.memory:
            parts.append(self.memory)
        if with_history and self.history:
            parts.append(self.history)
        parts.append(self.user)
        return "\n\n".join(p for p in parts if p)

    def messages(self, with_history: bool = True) -> list[dict]:
        return [{"role": "user", "content": self.build(with_history)}]


def build_context(
    user_message: str,
    user_id: str = "u_demo_001",
    history: list[dict] | None = None,
    state: dict | None = None,
) -> ContextBlock:
    """每轮对话前调用，统一组装上下文"""
    history = history or []
    state = state or {}
    memory = get_memory()
    profile = get_structured_profile(user_id)

    # System
    system = SYSTEM_PROMPT

    # Profile block (精简版，~120 tokens)
    profile_text = compact_profile_text(profile)
    profile_block = f"[用户画像]\n{profile_text}"
    if profile.get("dietary"):
        profile_block += f"\n饮食限制：{'、'.join(profile['dietary'])}"
    if profile.get("offWorkTime"):
        profile_block += f"\n下班时间：{profile['offWorkTime']}"
    if profile.get("freeSlots"):
        profile_block += f"\n空闲时段：{'、'.join(profile['freeSlots'])}"
    if profile.get("homeArea"):
        profile_block += f"\n居住区域：{profile['homeArea']}"
    if profile.get("workArea"):
        profile_block += f"\n工作区域：{profile['workArea']}"

    # Memory block
    mem_block = memory.build_context_block(user_message, user_id=user_id)

    # History block (最近 5 轮，~400 tokens)
    history_block = ""
    if history:
        recent = history[-10:]  # 5 轮 = 10 条消息
        lines = ["[对话历史]"]
        for msg in recent:
            role = "用户" if msg["role"] == "user" else "AI"
            content = (msg.get("content") or "")[:150]
            lines.append(f"{role}：{content}")
        history_block = "\n".join(lines)

    # Current plan in state
    if state.get("last_plan") and state["last_plan"].get("stops"):
        plan = state["last_plan"]
        stops_text = " → ".join(
            f"{s.get('name','')}" for s in plan.get("stops", [])[:4]
        )
        history_block += f"\n[当前草稿方案] {plan.get('title','')}: {stops_text}"

    return ContextBlock(
        system=system,
        profile=profile_block,
        memory=mem_block,
        history=history_block,
        user=f"用户：{user_message}",
        user_id=user_id,
        profile_data=profile,
    )
