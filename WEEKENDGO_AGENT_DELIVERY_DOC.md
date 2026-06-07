# Weekendgo 本地生活短时活动规划 Agent 交付文档

## 0. 原始任务要求覆盖

本设计文档覆盖以下任务要求：

- 任务背景：周六上午 9 点，小明临时获得半天休息时间，希望下午带老婆、5 岁孩子和朋友出门玩几个小时，地点不能离家太远，并需要把最终安排发给老婆和朋友确认。
- 场景约束：老婆最近在减脂；同行朋友约 4 人，包含男生和女生；需要同时考虑家庭、朋友、餐饮、活动和距离。
- 规划目标：不是搜索推荐，而是在几分钟内完成一条下午 4-6 点可执行的综合方案。
- Agent 必须处理：去哪玩、玩完去哪吃、餐厅是否适合、是否排队、位置是否合适、吃饭前后是否有亲子/展览/citywalk/小吃街等补充活动。
- 输出动作：方案确认后，可以继续模拟保存行程、预约/排队、购票、发送给同行人确认等关键动作。
- 交付形式：Demo 可以使用命令行或 Web UI；本项目采用 Web UI + Flask API。
- API 要求：允许使用 Mock API，但工具调用链必须完整，能体现真实产品可替换为高德/天气/预约/票务/订单/分享服务。
- 文档要求：说明 Planning 策略、工具调用链和异常处理机制。

## 1. 任务背景与目标

周六上午 9 点，用户小明临时获得半天休息时间，想在下午 4-6 点带家人和朋友出门玩几个小时。家庭场景包含 5 岁孩子、老婆最近减脂，朋友场景包含总共约 4 人、2 个男生和 2 个女生。用户希望 Agent 不只是搜索推荐，而是在接下来的几分钟内完成一条可执行的本地生活方案：去哪玩、玩完去哪吃、餐厅是否适合、是否排队、吃饭前后还能安排什么、如何把计划发给同行人确认，以及确认后如何一键执行预约、排队、购票、分享等动作。

本项目目标是构建一个 AI agent 原生的本地生活 planning 产品。Demo 数据可以是 mock，登录可以使用 demo 账号，但核心链路需要像完整产品：用户自然语言输入目标，Agent 理解约束、检索画像和地点、规划路线、检查风险、输出可落地方案，并将结果同步到行程页、地图、聊天和群聊中。

## 2. 产品范围

当前交付包含 Web UI 和后端 Agent 服务，主要入口是 fresh 版本：

- 前端目录：`web/`
- 后端目录：`backend/`
- 本地访问：`http://127.0.0.1:5174/`
- 后端 API：`http://127.0.0.1:5000/api/v1`

核心用户链路：

1. Demo 登录，首次登录由小薇读取模拟美团生态数据生成用户画像。
2. 用户在小薇聊天页输入自然语言目标。
3. Agent 识别意图、补充槽位、读取用户画像、检索 POI、生成结构化行程草稿。
4. Agent 同时返回风险提醒和确认后可执行动作。
5. 前端展示路线、提醒、执行动作，并把行程同步到行程页。
6. 用户确认后保存行程，并可继续查看高德实时地图、天气、提醒、替换站点。
7. 好友/群聊页支持私聊 Agent、群协调 Agent、创建群聊、根据成员画像生成群路线。

## 3. 功能需求清单

### 3.1 用户与画像

- 支持 3 个 demo 登录入口，保留原登录页素材和视觉风格。
- 首次登录时展示小薇分析画像的交互动画。
- 首次画像生成不能硬编码文案，需要通过后端 Agent action `onboarding_profile` 获取。
- 退出登录后清理当前用户 onboarding 记录，下次登录重新生成画像。
- 用户画像由消费、搜索、骑行/出行等模拟记录推断。
- 搜索记录、消费记录、出行记录需要语义区分：搜索咖啡不等于去了咖啡店。

### 3.2 小薇 AI 对话

- 聊天页是中心入口，不再使用“今天想怎么过”“补充我的想法”等冗余流程。
- 用户自然语言输入后，Agent 返回路线草稿和可读解释。
- 除行程外，必须额外提醒可能的问题：
  - 餐厅排队、预约、大桌、儿童椅。
  - 步行时间过长、孩子体力、老人/家庭成员休息。
  - 减脂、清淡、不吃辣、素食等饮食偏好。
  - 多人预算差异、集合时间、地点是否太远。
  - 周末客流导致的备选餐厅/咖啡/活动点。
- 用户说“确认/就这个/搞定”后，应进入保存和模拟执行流程。

### 3.3 行程与地图

- 行程页采用类似聊天列表的时间分类入口，支持同一天多个 plan。
- 点击行程进入详情，展示路线、天气、提醒、预算、步行时间、交通方式。
- 地图显示接入高德 JS API 真实底图。
- 路线、天气、交通、POI 可以先由 mock API 返回，但字段和工具链按真实 API 设计。
- 高德加载失败时回退到静态 mock 地图，不允许空白。

### 3.4 好友与群聊

- 右侧底部入口为聊天/群聊，不是 AI 主入口。
- 好友列表和群聊列表 UI 需要区分。
- 好友可点击进入私聊，私聊中小薇作为协调 Agent，不伪装成好友。
- 群聊可点击进入群会话，支持群设置、成员画像面板。
- 群聊页支持创建群聊，从已有好友列表选择成员。
- 群聊中 @小薇 触发群协调 Agent，根据成员画像生成群路线。

### 3.5 执行动作

当前为 mock 执行，但链路和返回结构需要完整：

- 保存行程。
- 预约/排队餐厅。
- 查询门票/开放时间。
- 购票。
- 把确认文案发给同行人。
- 失败时给出原因和可重试动作。

## 4. Agent 架构设计

Agent 不是单纯 prompt 驱动，而是 code-led state machine + LLM polishing 的结构。

```text
User Message
  -> intent_router
  -> session_state / memory / profile
  -> planning_service or profile_service or group_agent
  -> tool calls
  -> structured response schema
  -> optional LLM polish with fallback
  -> frontend render
```

关键模块：

- `agent/intent_router.py`：确定意图，如 `plan_trip`、`find_place`、`modify_plan`、`confirm_plan`、`update_profile`、`onboarding_profile`。
- `agent/profile_service.py`：从 mock 生态记录构建用户画像，支持群成员画像融合。
- `agent/planning_service.py`：确定性 planning 核心，负责 POI 检索、排序、路线选择、预算、步行、风险提醒、执行动作。
- `agent/agent.py`：Agent 总入口，管理会话状态、memory、确认保存、LLM 润色与 fallback。
- `agent/multi_agent.py`：群规划协调，合并成员画像、识别冲突、生成统一方案。
- `agent/tools.py`：模拟工具，包括天气、可订状态、路线、执行动作等。
- `agent/response_schema.py`：统一输出结构，前端消费 `reply`、`trip`、`actions`、`metadata`。

## 5. Tool 调用链

### 5.1 单人短时规划

```text
route_intent
  -> get_structured_profile
  -> find_places
  -> rank_pois
  -> generate_structured_trip
  -> check_plan_risks
  -> return draft plan
```

输出包括：

- `trip.stops`
- `trip.totalBudget`
- `trip.totalWalkMinutes`
- `trip.fitReasons`
- `trip.riskReminders`
- `trip.executionActions`
- `trip.confirmMessage`

### 5.2 用户确认后执行

```text
confirm_plan
  -> save_plan
  -> execute_actions
  -> return saved trip + execution results
```

Mock 执行动作示例：

- `reserve_restaurant`
- `buy_tickets`
- `share_plan`
- `reserve_or_queue`
- `check_ticket`

### 5.3 群规划

```text
group_chat / group_plan
  -> load member profiles
  -> merge preferences
  -> resolve conflicts
  -> build_trip_plan(group_context)
  -> return group plan + conflicts + actions
```

群冲突处理包括预算差异、出门时间差异、偏好差异和社交风格差异。

## 6. Mock API 与真实 API 边界

当前 Demo 允许 mock，但路径按真实产品设计：

- 高德地图 JS API：真实地图显示。
- 路线规划：当前 mock 坐标/折线，后续可替换为高德步行/驾车路线 API。
- 天气：当前 mock 天气，后续可替换为天气 API。
- POI：当前 SQLite mock POI，后续可替换为美团/高德/内部 POI 服务。
- 排队/预约/购票：当前 mock `execute_actions`，后续可接商户预约、排队、票务和订单服务。
- 分享：当前 mock share message，后续可接微信/短信/站内消息。

## 7. 前端页面与状态

主要页面：

- 登录页：demo 登录入口，保留原素材。
- onboarding 页：首次画像分析。
- AI 聊天页：小薇主入口，支持路线生成、风险提醒、行程同步。
- 行程页：按时间列出多个行程，详情展示地图、站点、天气、提醒、替换。
- 聊天页：好友/群聊列表、创建群聊。
- 聊天详情页：好友私聊 Agent、群协调 Agent。
- 个人页/设置页：用户信息、好友列表、退出登录。

关键前端逻辑：

- `web/src/App.vue`：全局页面状态、AI 聊天、行程同步、登录状态。
- `web/src/components/ItineraryPage.vue`：行程列表和详情。
- `web/src/components/ItineraryMap.vue`：高德实时地图和静态兜底。
- `web/src/components/ChatPage.vue`：好友/群聊列表和创建群聊。
- `web/src/components/ChatThreadPage.vue`：私聊/群聊 Agent 对话。
- `web/src/api.ts`：后端 API 封装。

## 8. 异常处理机制

- LLM 不可用：保留确定性 planning 输出，LLM polish 失败不影响生成路线。
- 地图加载失败：回退静态地图，不阻断行程详情页。
- 后端无行程草稿时确认：返回 `needs_plan`，提示用户先生成方案。
- 长句含“确认”但仍是规划目标时：路由避免误判为保存确认。
- POI 不足：放宽检索条件，使用开放 POI 兜底。
- 排队/预约工具失败：风险提醒仍可生成，执行状态标记为 pending 或 failed。
- localStorage 失败：当前会话仍可运行，登录/群聊创建不崩溃。

## 9. 验收标准

可用以下场景验收：

1. 首次登录 demo 用户，看到小薇生成画像过程。
2. 输入：
   `今天下午4到6点，带5岁孩子、老婆最近减肥，还有4个朋友一起，别离家太远，帮我安排吃喝玩和发给朋友确认的方案`
3. 小薇应返回：
   - 一条下午短时路线。
   - 至少 2 条问题提醒，如步行偏长、亲子缓冲、饮食偏好、多人确认。
   - 确认后可执行动作，如预约/排队、确认开放时间、分享给同行人。
4. 行程页应出现路线草稿或保存后的行程。
5. 行程详情应显示高德实时地图或静态兜底地图。
6. 聊天页可以创建群聊，并在群里 @小薇 生成群路线。
7. 退出登录后，当前用户下次登录会重新触发画像生成。

## 10. 当前完成度与后续优化

已完成：

- Agent 状态机、画像、规划、风险提醒、执行动作 mock。
- 小薇聊天到行程页的主链路。
- 高德地图显示。
- 好友、群聊、创建群聊、私聊/群聊 Agent。
- 前端主要页面连接后端。

仍可增强：

- 接真实路线规划 API，替换 mock polyline。
- 接真实天气、预约、排队、票务、订单、消息分享服务。
- 将聊天消息、群聊消息、创建群聊持久化到后端数据库。
- 增加执行清单页面，展示每个动作的 pending/success/failed/retry 状态。
- 增加多轮追问策略，例如预算缺失、孩子年龄不确定、朋友口味未知时主动补问。
