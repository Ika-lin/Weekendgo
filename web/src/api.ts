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

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  const json = await res.json()
  if (json.code !== 0) {
    throw new Error(json.message || 'API Error')
  }
  return json.data as T
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
