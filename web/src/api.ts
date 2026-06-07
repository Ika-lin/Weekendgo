/**
 * Weekendgo API 服务
 */
const API_BASE = '/api/v1'

export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
  requestId?: string
  timestamp?: string
}

export interface AgentAction {
  type: string
  label: string
  status?: string
}

export interface ChatPayload {
  reply: string
  intent: string
  stage: string
  toolCalls: any[]
  trip: any | null
  suggestions: any[]
  actions: AgentAction[]
  needs: string[]
  metadata: Record<string, any>
  sessionId: string
  userId: string
}

export interface GroupPayload {
  reply?: string
  messages?: Array<{ persona: string; emoji?: string; color?: string; text: string }>
  trip?: any
  members?: Array<{ userId: string; nickname?: string; summary?: string; profile?: UserProfilePayload }>
  intent?: string
  actions?: AgentAction[]
  toolCalls?: any[]
  metadata?: Record<string, any>
  sessionId?: string
  mode?: string
}

export interface FriendPayload {
  reply: string
  intent?: string
  actions?: AgentAction[]
  metadata?: Record<string, any>
  sessionId?: string
  userId?: string
  friendId?: string
}

export interface TripStopPayload {
  stopId: string
  poiId?: string
  index: number
  time: string
  endTime?: string
  name: string
  desc: string
  category?: string
  address?: string
  lat?: number | null
  lng?: number | null
  pricePerCapita?: number | null
  rating?: number | null
  walkFromPrevious?: number
  tags?: string[]
  queueInfo?: string | null
  durationMinutes?: number
  done?: boolean
  checkinTime?: string | null
  alternatives?: any[]
}

export interface TripDetailPayload {
  tripId: string
  title: string
  city: string
  date: string
  totalBudget: string
  status: string
  overview: Record<string, any>
  routeMap: Record<string, any>
  stops: TripStopPayload[]
}

export interface TripListItemPayload {
  tripId: string
  planId?: string
  title: string
  city: string
  date: string
  status: string
  totalBudget?: string
  type?: string
  duration?: string
  transportMode?: string
  totalWalkMinutes?: number | null
  stopCount: number
  firstStop?: string
  lastStop?: string
  source?: string
  createdAt?: string
}

export interface PoiDetailPayload {
  poiId: string
  name: string
  category: string
  address: string
  lat: number
  lng: number
  pricePerCapita: number
  rating: number
  businessStatus: string
  openHoursText: string
  phone: string
  heroImage: string
  tags: string[]
  about: string
  impressionTags: string[]
  suitableFor: string[]
  attention: string[]
  userQuote: string
  peakHours: string
  facilities: string[]
  mustTry: string
  reviewCount: number
  photoCount: number
}

export interface PoiReviewInsightsPayload {
  poiId: string
  rating: number
  reviewCount: number
  impressionTags: string[]
  highlights: string[]
  riskNotes: string[]
  sampleQuote: string
}

export interface PoiArrivalHintsPayload {
  poiId: string
  stopId: string
  queueRisk: string
  bestArrivalWindow: string
  trafficNote: string
  weatherImpact: string
}

export interface DiscoverPlaceItem {
  itemId: string
  name: string
  category: string
  badge: string
  subtitle: string
  layout: string
  gradient: string
}

export interface UserProfilePayload {
  userId: string
  nickname: string
  avatar?: string
  location?: string
  stats?: {
    footprints: number
    favorites: number
    completedTrips: number
  }
  favoriteCategories?: Array<{ category: string; count: number; avgAmount?: number }>
  favoriteDistricts?: Array<{ district: string; count: number }>
  favoriteTags?: string[]
  avgSpending?: number
  totalVisits?: number
  preferredTime?: string
  soloRatio?: number
  socialRatio?: number
  ratingAvg?: number
  personaSummary?: string
  personaTags?: string[]
  socialStyle?: string
  groupSizePreference?: number
  dietary?: string[]
  mobility?: string
  budgetComfort?: number
  freeSlots?: string[]
  rawRecordCount?: number
  interestCategories?: Array<{ category: string; count: number }>
  sourceBreakdown?: Record<string, number>
  mobilitySignals?: Record<string, number>
  homeArea?: string
  workArea?: string
}

export interface TripReminderPayload {
  tripId: string
  today: string[]
  packingChecklist: string[]
}

export interface TripWeatherPayload {
  tripId: string
  city: string
  date: string
  provider: string
  condition: string
  temperatureText: string
  humidity: string
  wind: string
  rainProbability: number
  comfortLevel: string
  agentTips: string[]
  impact: Record<string, string>
}

export interface TripAlternativePayload {
  candidateId: string
  name: string
  categoryTags: string[]
  priceRange: string
  walkMinutes: number
  reason: string
}

export interface TripAlternativesPayload {
  stopId: string
  alternatives: TripAlternativePayload[]
}

interface PlanGenerateRequest {
  timeType: string
  activities: string[]
  geographicRange: string
  budget: string
  prompt?: string
  city?: string
}

interface Plan {
  planId: string
  type: string
  title: string
  duration: string
  budgetText: string
  tag: string
  color: string
  score: number
  description: string
  spots: Spot[]
}

interface Spot {
  spotId: string
  name: string
  category: string
  address: string
  etaMinutes: number
}

const MOCK_TRIP: TripDetailPayload = {
  tripId: 'mock_trip_preview',
  title: '小薇生成的周末轻行程',
  city: '上海',
  date: '今天',
  totalBudget: '约 180-260 元/人',
  status: 'planned',
  overview: {
    duration: '3 小时 20 分钟',
    transportMode: '步行 + 短途打车',
    totalWalkMinutes: 24,
    weather: '多云，体感舒适',
    agentSummary: '小薇根据你的口味、同行人数、距离和排队风险，优先安排了咖啡、轻食和可聊天的散步路线。',
  },
  routeMap: {
    provider: 'mock-amap',
    center: { lat: 31.2158, lng: 121.4434 },
    polyline: [
      [121.4392, 31.2123],
      [121.4418, 31.2142],
      [121.4456, 31.2161],
      [121.4482, 31.218],
    ],
  },
  stops: [
    {
      stopId: 'mock_stop_1',
      poiId: 'poi_mock_cafe',
      index: 0,
      time: '15:30',
      endTime: '16:20',
      name: '% Arabica 武康路店',
      desc: '先用咖啡和甜点集合，适合等朋友到齐，也方便小薇根据实时排队情况调整后续路线。',
      category: '咖啡',
      address: '徐汇区武康路',
      lat: 31.2123,
      lng: 121.4392,
      pricePerCapita: 48,
      rating: 4.7,
      walkFromPrevious: 0,
      tags: ['集合方便', '拍照友好', '排队可控'],
      queueInfo: '预计排队 8-12 分钟',
      durationMinutes: 50,
      alternatives: [],
    },
    {
      stopId: 'mock_stop_2',
      poiId: 'poi_mock_walk',
      index: 1,
      time: '16:30',
      endTime: '17:25',
      name: '武康路城市散步段',
      desc: '沿街区慢走，减少室内拥挤；如果同行有人累，小薇会把后半段替换成附近茶饮店。',
      category: 'CityWalk',
      address: '武康路 - 安福路',
      lat: 31.2161,
      lng: 121.4456,
      pricePerCapita: 0,
      rating: 4.8,
      walkFromPrevious: 10,
      tags: ['轻松', '低预算', '可替换'],
      queueInfo: '无需排队',
      durationMinutes: 55,
      alternatives: [],
    },
    {
      stopId: 'mock_stop_3',
      poiId: 'poi_mock_food',
      index: 2,
      time: '17:40',
      endTime: '18:50',
      name: '附近轻食 Brunch',
      desc: '收尾选择低负担餐食，兼顾减脂和聚餐聊天；小薇会提醒提前取号和过敏忌口。',
      category: '轻食',
      address: '安福路附近',
      lat: 31.218,
      lng: 121.4482,
      pricePerCapita: 96,
      rating: 4.6,
      walkFromPrevious: 14,
      tags: ['减脂友好', '适合聊天', '可预约'],
      queueInfo: '晚高峰可能排队，建议提前 20 分钟取号',
      durationMinutes: 70,
      alternatives: [],
    },
  ],
}

const MOCK_PROFILE: UserProfilePayload = {
  userId: 'u_demo_001',
  nickname: '周末体验家',
  location: '上海',
  stats: { footprints: 0, favorites: 0, completedTrips: 0 },
  favoriteCategories: [
    { category: '咖啡', count: 12, avgAmount: 45 },
    { category: '轻食', count: 8, avgAmount: 82 },
    { category: 'CityWalk', count: 6, avgAmount: 0 },
  ],
  favoriteDistricts: [
    { district: '徐汇', count: 10 },
    { district: '静安', count: 7 },
  ],
  favoriteTags: ['安静', '好拍照', '少排队', '适合聊天'],
  avgSpending: 86,
  totalVisits: 26,
  preferredTime: '下午',
  soloRatio: 0.35,
  socialRatio: 0.65,
  ratingAvg: 4.7,
  personaSummary: '你偏好轻松、不赶路、有聊天空间的周末体验。小薇会优先控制步行距离、排队风险和预算。',
  personaTags: ['咖啡偏好', '轻社交', '低压力路线'],
  socialStyle: '轻松熟人局',
  groupSizePreference: 3,
  rawRecordCount: 86,
  sourceBreakdown: { dinein: 23, search: 42, bike: 21 },
}

function mockChatPayload(options?: RequestInit): ChatPayload {
  const body = safeBody(options)
  const message = body.message || ''
  const onboarding = body.action === 'onboarding_profile'
  return {
    reply: onboarding
      ? '我已经读取了你的 mock 消费、搜索和出行记录：你更偏好徐汇/静安附近、咖啡轻食、低压力步行路线。我会在后续规划里自动避开过长步行、长排队和过高预算。'
      : `收到，我会按“${message || '轻松周末'}”来安排。建议先走咖啡集合、街区散步、轻食收尾，并提醒：晚高峰可能排队，同行成员需要确认忌口和步行接受度。`,
    intent: onboarding ? 'profile_onboarding' : 'trip_planning',
    stage: onboarding ? 'profile_ready' : 'plan_ready',
    toolCalls: [
      { tool: 'profile_retrieval', status: 'mocked' },
      { tool: 'poi_ranker', status: 'mocked' },
      { tool: 'weather_route_risk', status: 'mocked' },
    ],
    trip: onboarding ? null : MOCK_TRIP,
    suggestions: [],
    actions: onboarding
      ? [{ type: 'start_chat', label: '开始和小薇聊天', status: 'ready' }]
      : [
          { type: 'save_trip', label: '保存路线', status: 'ready' },
          { type: 'share_trip', label: '发给朋友确认', status: 'ready' },
        ],
    needs: [],
    metadata: { previewMode: true },
    sessionId: body.sessionId || 'mock_session',
    userId: body.userId || 'u_demo_001',
  }
}

function safeBody(options?: RequestInit): Record<string, any> {
  try {
    return options?.body ? JSON.parse(String(options.body)) : {}
  } catch {
    return {}
  }
}

function mockRequest<T>(path: string, options?: RequestInit): T {
  if (path === '/chat') return mockChatPayload(options) as T
  if (path.startsWith('/group-chat')) {
    return {
      reply: '群聊小薇已综合成员偏好：减少步行、保留拍照点、晚餐选择轻食或本帮菜，并建议先发起投票确认。',
      messages: [
        { persona: '小薇', color: '#7c3aed', text: '我会把大家的预算、口味和时间合成一个可执行方案。' },
        { persona: '朋友A', color: '#0ea5e9', text: '我希望别走太远，最好能坐下来聊天。' },
      ],
      trip: MOCK_TRIP,
      actions: [{ type: 'share_trip', label: '同步到群聊', status: 'ready' }],
      toolCalls: [{ tool: 'group_preference_merge', status: 'mocked' }],
      metadata: { previewMode: true },
      sessionId: safeBody(options).sessionId || 'mock_group_session',
      mode: 'preview',
    } as T
  }
  if (path === '/friend-chat') {
    return {
      reply: '我会根据你和好友的共同偏好生成一个更轻量的双人路线，并提醒你们提前确认时间和忌口。',
      actions: [{ type: 'invite_friend', label: '邀请好友确认', status: 'ready' }],
      metadata: { previewMode: true },
    } as T
  }
  if (path.startsWith('/user/profile')) return MOCK_PROFILE as T
  if (path.includes('/footprints')) {
    return { userId: 'u_demo_001', total: 3, footprints: MOCK_TRIP.stops.map((stop) => ({ ...stop, visitedAt: 'mock' })) } as T
  }
  if (path === '/trips' || path.startsWith('/trips?')) {
    return {
      userId: 'u_demo_001',
      items: [
        {
          tripId: MOCK_TRIP.tripId,
          title: MOCK_TRIP.title,
          city: MOCK_TRIP.city,
          date: MOCK_TRIP.date,
          status: MOCK_TRIP.status,
          totalBudget: MOCK_TRIP.totalBudget,
          type: 'AI 生成路线',
          duration: MOCK_TRIP.overview.duration,
          transportMode: MOCK_TRIP.overview.transportMode,
          totalWalkMinutes: MOCK_TRIP.overview.totalWalkMinutes,
          stopCount: MOCK_TRIP.stops.length,
          firstStop: MOCK_TRIP.stops[0]?.name,
          lastStop: MOCK_TRIP.stops[MOCK_TRIP.stops.length - 1]?.name,
          source: 'preview-mock',
          createdAt: new Date().toISOString(),
        },
      ],
    } as T
  }
  if (path.startsWith('/trip/') && path.endsWith('/weather')) {
    return {
      tripId: MOCK_TRIP.tripId,
      city: '上海',
      date: '今天',
      provider: 'mock-weather',
      condition: '多云',
      temperatureText: '24-28°C',
      humidity: '62%',
      wind: '东南风 2 级',
      rainProbability: 20,
      comfortLevel: '适合步行',
      agentTips: ['带一把轻便伞', '晚餐前提前取号', '步行段可随时缩短'],
      impact: { walk: '舒适', queue: '晚高峰略高', outdoor: '适合' },
    } as T
  }
  if (path.startsWith('/trip/') && path.endsWith('/reminders')) {
    return { tripId: MOCK_TRIP.tripId, today: ['提前取号', '确认忌口', '控制步行'], packingChecklist: ['充电宝', '雨伞'] } as T
  }
  if (path.startsWith('/trip/') && path.endsWith('/route-map')) return MOCK_TRIP.routeMap as T
  if (path.startsWith('/trip/')) return MOCK_TRIP as T
  if (path === '/trip/create') return { tripId: MOCK_TRIP.tripId, trip: MOCK_TRIP } as T
  if (path === '/plan/generate') {
    return {
      plans: [
        {
          planId: 'mock_plan_1',
          type: 'local_life',
          title: MOCK_TRIP.title,
          duration: '3 小时',
          budgetText: MOCK_TRIP.totalBudget,
          tag: '低压力',
          color: '#7c3aed',
          score: 92,
          description: '咖啡集合、街区散步、轻食收尾，适合快速展示 AI Agent 规划能力。',
          spots: MOCK_TRIP.stops.map((stop) => ({
            spotId: stop.stopId,
            name: stop.name,
            category: stop.category || '',
            address: stop.address || '',
            etaMinutes: stop.walkFromPrevious || 0,
          })),
        },
      ],
    } as T
  }
  if (path.startsWith('/discover/categories')) return { categories: ['全部', '咖啡', '轻食', 'CityWalk', '展览'] } as T
  if (path.startsWith('/discover/events')) {
    return { events: [{ eventId: 'mock_event_1', emoji: 'AI', title: '周末轻路线', subtitle: '小薇推荐', badge: 'Preview' }] } as T
  }
  if (path.startsWith('/discover/places')) {
    return {
      items: MOCK_TRIP.stops.map((stop, index) => ({
        itemId: stop.poiId || stop.stopId,
        name: stop.name,
        category: stop.category || '推荐',
        badge: index === 0 ? '适合集合' : 'AI 推荐',
        subtitle: stop.desc,
        layout: index % 2 === 0 ? 'large' : 'small',
        gradient: 'linear-gradient(135deg, #fff7ed, #eef2ff)',
      })),
    } as T
  }
  if (path.startsWith('/pois/') && path.includes('/review-insights')) {
    return { poiId: 'mock', rating: 4.7, reviewCount: 1280, impressionTags: ['少排队', '好聊天'], highlights: ['环境稳定', '动线清晰'], riskNotes: ['晚高峰提前取号'], sampleQuote: '适合朋友轻松碰头。' } as T
  }
  if (path.startsWith('/pois/') && path.includes('/arrival-hints')) {
    return { poiId: 'mock', stopId: 'mock', queueRisk: '中', bestArrivalWindow: '提前 10-15 分钟', trafficNote: '短途步行优先', weatherImpact: '多云，影响较小' } as T
  }
  if (path.startsWith('/pois/')) {
    const stop = MOCK_TRIP.stops[0]
    return {
      poiId: stop.poiId || 'mock',
      name: stop.name,
      category: stop.category || '咖啡',
      address: stop.address || '',
      lat: stop.lat || 31.2123,
      lng: stop.lng || 121.4392,
      pricePerCapita: stop.pricePerCapita || 48,
      rating: stop.rating || 4.7,
      businessStatus: '营业中',
      openHoursText: '10:00-22:00',
      phone: '暂无',
      heroImage: '/discover-cafe.png',
      tags: stop.tags || [],
      about: stop.desc,
      impressionTags: ['适合集合', '环境稳定'],
      suitableFor: ['朋友见面', '轻松聊天'],
      attention: ['晚高峰可能排队'],
      userQuote: '这里适合作为路线第一站。',
      peakHours: '16:00-18:00',
      facilities: ['可外带', '附近可步行'],
      mustTry: '拿铁 / 甜点',
      reviewCount: 1280,
      photoCount: 320,
    } as T
  }
  return {} as T
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!res.ok) {
      throw new Error(`API ${res.status}`)
    }
    const json = await res.json()
    if (json.code !== 0) {
      throw new Error(json.message || 'API Error')
    }
    return json.data as T
  } catch (error) {
    console.warn('[Weekendgo] API unavailable, using preview mock fallback:', path, error)
    return mockRequest<T>(path, options)
  }
}

export async function chatAgent(params: {
  message: string
  sessionId: string
  userId: string
  action?: 'onboarding_profile' | string
}): Promise<ChatPayload> {
  return request<ChatPayload>('/chat', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

export async function resetChat(params: { sessionId: string; userId?: string }): Promise<void> {
  await request('/chat/reset', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

export async function groupChat(params: {
  message: string
  sessionId: string
  user_ids?: string[]
  action?: 'chat' | 'synthesize'
}): Promise<GroupPayload> {
  return request<GroupPayload>('/group-chat', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

export async function friendChat(params: {
  message: string
  sessionId: string
  userId: string
  friendId: string
}): Promise<FriendPayload> {
  return request<FriendPayload>('/friend-chat', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

export async function groupPlan(params: {
  user_ids: string[]
  message: string
  sessionId: string
}): Promise<GroupPayload> {
  return request<GroupPayload>('/group-chat/plan', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

export async function generatePlans(params: PlanGenerateRequest): Promise<Plan[]> {
  const data = await request<{ plans: Plan[] }>('/plan/generate', {
    method: 'POST',
    body: JSON.stringify(params),
  })
  return data.plans || []
}

export async function createTrip(params: {
  userId: string
  planId: string
  plan: Plan | any
  date?: string
  city?: string
}): Promise<{ tripId: string; trip: TripDetailPayload }> {
  return request('/trip/create', {
    method: 'POST',
    body: JSON.stringify(params),
  })
}

export async function getTripDetail(tripId: string): Promise<TripDetailPayload> {
  return request(`/trip/${tripId}`)
}

export async function getTripReminders(tripId: string): Promise<TripReminderPayload> {
  return request(`/trip/${tripId}/reminders`)
}

export async function getTripRouteMap(tripId: string): Promise<any> {
  return request(`/trip/${tripId}/route-map`)
}

export async function getTripWeather(tripId: string): Promise<TripWeatherPayload> {
  return request(`/trip/${tripId}/weather`)
}

export async function getTrips(userId: string): Promise<{ userId: string; items: TripListItemPayload[] }> {
  return request(`/trips?userId=${userId}`)
}

export async function adjustTrip(tripId: string, mode: string): Promise<any> {
  return request(`/trip/${tripId}/adjust`, {
    method: 'POST',
    body: JSON.stringify({ mode }),
  })
}

export async function getTripAlternatives(tripId: string, stopId: string): Promise<TripAlternativesPayload> {
  return request(`/trip/${tripId}/stops/${stopId}/alternatives`)
}

export async function replaceTripStop(tripId: string, stopId: string, candidateId: string): Promise<any> {
  return request(`/trip/${tripId}/stops/${stopId}/replace`, {
    method: 'POST',
    body: JSON.stringify({ candidateId }),
  })
}

export async function getPoiDetail(poiId: string): Promise<PoiDetailPayload> {
  return request(`/pois/${poiId}`)
}

export async function getPoiReviewInsights(poiId: string): Promise<PoiReviewInsightsPayload> {
  return request(`/pois/${poiId}/review-insights`)
}

export async function getPoiArrivalHints(poiId: string, stopId?: string): Promise<PoiArrivalHintsPayload> {
  const params = stopId ? `?stopId=${encodeURIComponent(stopId)}` : ''
  return request(`/pois/${poiId}/arrival-hints${params}`)
}

export async function getDiscoverCategories(): Promise<{ categories: string[] }> {
  return request('/discover/categories')
}

export async function getDiscoverPlaces(category?: string): Promise<{ items: DiscoverPlaceItem[] }> {
  const params = category && category !== '全部' ? `?category=${category}` : ''
  return request(`/discover/places${params}`)
}

export async function getDiscoverEvents(): Promise<{ events: any[] }> {
  return request('/discover/events')
}

export async function getUserProfile(userId: string = 'u_demo_001'): Promise<UserProfilePayload> {
  return request(`/user/profile?userId=${userId}`)
}

export async function getUserFootprints(userId: string): Promise<{ userId: string; total: number; footprints: any[] }> {
  return request(`/user/${userId}/footprints`)
}

export type { Plan, Spot, PlanGenerateRequest }
