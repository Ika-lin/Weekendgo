<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { chatAgent, createTrip, generatePlans, getTripDetail, getTrips, type ChatPayload, type Plan, type PlanGenerateRequest, type TripDetailPayload, type TripListItemPayload } from './api'
import ItineraryPage from './components/ItineraryPage.vue'
import DiscoverPage from './components/DiscoverPage.vue'
import CreatePostPage from './components/CreatePostPage.vue'
import PlaceDetailPage from './components/PlaceDetailPage.vue'
import NavigationPage from './components/NavigationPage.vue'
import ChatPage from './components/ChatPage.vue'
import ChatThreadPage from './components/ChatThreadPage.vue'
import ProfilePage from './components/ProfilePage.vue'
import SettingsPage from './components/SettingsPage.vue'
import type { PlaceDetail } from './data/placeDetails'

type Screen = 'home1' | 'home2' | 'onboarding' | 'discover' | 'createPost' | 'ai1' | 'ai5' | 'itinerary' | 'placeDetail' | 'navigation' | 'chat' | 'chatDetail' | 'profile' | 'settings'
type DetailReturnScreen = Extract<Screen, 'discover' | 'itinerary'>

interface PlaceDetailRequest {
  detail: PlaceDetail
  poiId?: string | null
  returnScreen?: DetailReturnScreen
}

type AiChatMessage = {
  role: 'assistant' | 'user'
  text: string
}

type PlanningRiskReminder = {
  type?: string
  level?: string
  title?: string
  detail?: string
  action?: string
}

type PlanningExecutionAction = {
  type?: string
  label?: string
  status?: string
}

type SelectedChatThread = {
  id: string
  isGroup: boolean
  memberIds?: string[]
}

type CreatedChatGroup = SelectedChatThread & {
  isGroup: true
  memberIds: string[]
  title: string
  preview: string
  time: string
  image: string
  unread?: number
}

const activeScreen = ref<Screen>('home1')
const selectedPlaceDetail = ref<PlaceDetail | null>(null)
const selectedPoiId = ref<string | null>(null)
const placeDetailReturnScreen = ref<DetailReturnScreen>('itinerary')
const profileReturnScreen = ref<Screen>('ai1')
const selectedChatThread = ref<SelectedChatThread>({ id: 'group', isGroup: true })
const createdChatGroups = ref<CreatedChatGroup[]>([])
const currentTrip = ref<TripDetailPayload | null>(null)
const tripList = ref<TripListItemPayload[]>([])
const draftTrip = ref<TripDetailPayload | null>(null)
const isLoadingTrips = ref(false)
const showItineraryList = ref(true)
const aiPrompt = ref('')
const isGeneratingTrip = ref(false)
const aiGenerationError = ref('')
const isChattingWithAgent = ref(false)
const aiChatThreadRef = ref<HTMLElement | null>(null)
const aiMessages = ref<AiChatMessage[]>([
  { role: 'assistant', text: '我是小薇，告诉我你现在的时间、心情或想去的地方，我来帮你一起想。' },
])
const isOnboardingProfile = ref(false)
const onboardingReply = ref('')
const onboardingError = ref('')

const DEMO_USER_ID = 'u_demo_001'
const DEFAULT_CITY = '上海'
const currentUserId = ref(DEMO_USER_ID)

const demoUsers = [
  { id: 'u_demo_001', label: 'demo 用户 1' },
  { id: 'u_demo_002', label: 'demo 用户 2' },
  { id: 'u_demo_003', label: 'demo 用户 3' },
]

const displayedTrips = computed<TripListItemPayload[]>(() => {
  const draft = draftTrip.value ? [buildTripListItemFromDraft(draftTrip.value)] : []
  const saved = dedupeTripList(tripList.value).filter((item) => item.tripId !== draftTrip.value?.tripId)
  return [...draft, ...saved]
})

interface CardData {
  title: string
  tags: string[]
  tagColor: string
  tagTextColor: string
  time: string
  photo: string
  cardBg: string
}

const cardList: CardData[] = [
  {
    title: '约会夜晚计划',
    tags: ['夜景', '微醺', '约会'],
    tagColor: '#ffffff',
    tagTextColor: '#000000',
    time: '约3h · 氛围感',
    photo: '/cards/card-1.png',
    cardBg: 'rgba(197, 209, 249, 0.36)',
  },
  {
    title: '轻松恢复半日',
    tags: ['治愈', '展览', '休闲'],
    tagColor: '#6d7167',
    tagTextColor: '#ffffff',
    time: '半日 · 不赶路',
    photo: '/cards/card-2.png',
    cardBg: 'rgba(216, 204, 212, 0.64)',
  },
  {
    title: '一个人的慢下午',
    tags: ['咖啡', '独处', '放空'],
    tagColor: '#f4758c',
    tagTextColor: '#ffffff',
    time: '约2h · 少走路',
    photo: '/cards/card-3.png',
    cardBg: 'rgba(255, 226, 243, 0.47)',
  },
  {
    title: '城市漫游时刻',
    tags: ['City Walk', '探店', '出片'],
    tagColor: '#ffffff',
    tagTextColor: '#000000',
    time: '约2.5h · 好拍照',
    photo: '/cards/card-4.png',
    cardBg: 'rgba(211, 204, 245, 0.37)',
  },
]

const currentCardIndex = ref(0)
let touchStartX = 0
let touchEndX = 0
let isMouseDragging = false
let mouseStartX = 0
let mouseEndX = 0

function handleTouchStart(e: TouchEvent) {
  touchStartX = e.touches[0].clientX
}

function handleTouchEnd(e: TouchEvent) {
  touchEndX = e.changedTouches[0].clientX
  const diff = touchStartX - touchEndX
  if (Math.abs(diff) > 50) {
    if (diff > 0) {
      currentCardIndex.value = (currentCardIndex.value + 1) % cardList.length
    } else {
      currentCardIndex.value = (currentCardIndex.value - 1 + cardList.length) % cardList.length
    }
  }
}

function handleMouseDown(e: MouseEvent) {
  isMouseDragging = true
  mouseStartX = (e as any).pageX || e.clientX
  mouseEndX = (e as any).pageX || e.clientX
}

function handleMouseMove(e: MouseEvent) {
  if (!isMouseDragging) return
  mouseEndX = (e as any).pageX || e.clientX
}

function handleMouseUp(e: MouseEvent) {
  if (!isMouseDragging) return
  isMouseDragging = false
  
  // Final position from mouseup event
  const finalX = (e as any).pageX || e.clientX
  mouseEndX = finalX
  
  const diff = mouseStartX - mouseEndX
  if (Math.abs(diff) > 50) {
    if (diff > 0) {
      currentCardIndex.value = (currentCardIndex.value + 1) % cardList.length
    } else {
      currentCardIndex.value = (currentCardIndex.value - 1 + cardList.length) % cardList.length
    }
  }
}

const logoAsset = '/Frame 12.svg'
const levelsAsset = '/Levels.svg'
const wechatAsset = '/微信 1.svg'
const meituanAsset = '/美团 1.svg'
const appleAsset = '/苹果.svg'

// AI生成页1 Figma 资产
const ai1LevelsAsset = 'https://www.figma.com/api/mcp/asset/35bb016e-759a-449f-b9af-7ef15e90c5f3'
const ai1SparkIconAsset = 'https://www.figma.com/api/mcp/asset/6dd54065-b1b9-4654-8362-9e0c1ff8543e'

// 底部导航图标使用 public 下的本地正式资源
const ai1MicAsset = '/ChatTeardrop-dark.svg'
const ai1SearchAsset = '/MagnifyingGlass.svg'
const ai1NavCenterAsset = '/Icon-3.svg'
const ai1NavLeftAsset = '/user.svg'
const ai1NavRightAsset = '/lucide_map.svg'

function goToHome2() {
  activeScreen.value = 'home2'
}

function getOnboardingStorageKey(userId: string) {
  return `weekendgo:onboarded:${userId}`
}

function getCreatedGroupsStorageKey(userId: string) {
  return `weekendgo:created-groups:${userId}`
}

function loadCreatedChatGroups(userId: string): CreatedChatGroup[] {
  try {
    const raw = window.localStorage.getItem(getCreatedGroupsStorageKey(userId))
    if (!raw) return []

    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []

    return parsed.filter((group): group is CreatedChatGroup => (
      group &&
      group.isGroup === true &&
      Array.isArray(group.memberIds) &&
      typeof group.id === 'string' &&
      typeof group.title === 'string' &&
      typeof group.preview === 'string' &&
      typeof group.time === 'string' &&
      typeof group.image === 'string'
    ))
  } catch {
    return []
  }
}

function saveCreatedChatGroups(userId: string, groups: CreatedChatGroup[]) {
  try {
    window.localStorage.setItem(getCreatedGroupsStorageKey(userId), JSON.stringify(groups.slice(0, 12)))
  } catch {
    // Ignore storage failures; created groups still work for the current session.
  }
}

function hasCompletedOnboarding(userId: string) {
  try {
    return window.localStorage.getItem(getOnboardingStorageKey(userId)) === '1'
  } catch {
    return false
  }
}

function markOnboardingCompleted(userId: string) {
  try {
    window.localStorage.setItem(getOnboardingStorageKey(userId), '1')
  } catch {
    // Ignore storage failures; the app can still continue normally.
  }
}

function clearOnboardingCompleted(userId: string) {
  try {
    window.localStorage.removeItem(getOnboardingStorageKey(userId))
  } catch {
    // Ignore storage failures; logging out should still return to login.
  }
}

function logoutCurrentUser() {
  clearOnboardingCompleted(currentUserId.value)
  selectedPlaceDetail.value = null
  selectedPoiId.value = null
  currentTrip.value = null
  tripList.value = []
  draftTrip.value = null
  showItineraryList.value = true
  aiPrompt.value = ''
  aiGenerationError.value = ''
  isChattingWithAgent.value = false
  aiMessages.value = [
    { role: 'assistant', text: '我是小薇，告诉我你现在的时间、心情或想去的地方，我来帮你一起想。' },
  ]
  createdChatGroups.value = []
  onboardingReply.value = ''
  onboardingError.value = ''
  isOnboardingProfile.value = false
  activeScreen.value = 'home1'
}

async function startDemoLogin(userId: string = DEMO_USER_ID) {
  if (isOnboardingProfile.value) return

  currentUserId.value = userId
  createdChatGroups.value = loadCreatedChatGroups(userId)

  if (hasCompletedOnboarding(userId)) {
    activeScreen.value = 'ai1'
    return
  }

  activeScreen.value = 'onboarding'
  onboardingReply.value = ''
  onboardingError.value = ''
  isOnboardingProfile.value = true

  try {
    const result = await chatAgent({
      userId,
      sessionId: `onboarding-${userId}`,
      action: 'onboarding_profile',
      message: '首次登录，请根据我的美团生态数据生成画像，但不要直接生成行程。',
    })

    onboardingReply.value = result.reply || '小薇已经了解你的周末偏好，可以开始规划了。'
  } catch (error) {
    onboardingError.value = error instanceof Error ? error.message : '画像生成失败，请稍后重试'
    onboardingReply.value = '小薇暂时无法读取完整画像，但可以先根据你的输入规划路线。'
  } finally {
    isOnboardingProfile.value = false
  }
}

function finishOnboarding() {
  markOnboardingCompleted(currentUserId.value)
  activeScreen.value = 'ai1'
}

function goToAi5() {
  ensureAiPrompt()

  activeScreen.value = 'ai5'
}

function setActiveScreen(screen: Screen) {
  if (screen === 'profile' && activeScreen.value !== 'profile') {
    profileReturnScreen.value = activeScreen.value
  }

  if (screen === 'itinerary') {
    showItineraryList.value = true
    void refreshTrips()
  }

  activeScreen.value = screen
}

async function refreshTrips() {
  if (isLoadingTrips.value) return

  isLoadingTrips.value = true
  try {
    const data = await getTrips(currentUserId.value)
    tripList.value = data.items || []

    if (!currentTrip.value && tripList.value[0]?.tripId) {
      currentTrip.value = await getTripDetail(tripList.value[0].tripId)
    }
  } catch {
    tripList.value = []
  } finally {
    isLoadingTrips.value = false
  }
}

async function openTripFromList(tripId: string) {
  try {
    if (tripId === draftTrip.value?.tripId) {
      currentTrip.value = draftTrip.value
      showItineraryList.value = false
      return
    }

    currentTrip.value = await getTripDetail(tripId)
    showItineraryList.value = false
  } catch (error) {
    aiGenerationError.value = error instanceof Error ? error.message : '行程详情加载失败'
  }
}

function backToTripList() {
  showItineraryList.value = true
  void refreshTrips()
}

function buildDraftTripFromAgent(agentTrip: any, sourceMessage: string): TripDetailPayload {
  const planId = agentTrip.planId || `draft-${Date.now()}`
  const stops = (agentTrip.stops || []).map((stop: any, index: number) => ({
    stopId: stop.stopId || `draft-stop-${index + 1}`,
    poiId: stop.poiId || '',
    index: stop.index || stop.order || index + 1,
    time: stop.time || '',
    endTime: stop.endTime || '',
    name: stop.name || `第 ${index + 1} 站`,
    desc: stop.desc || stop.reason || '',
    category: stop.category || '',
    address: stop.address || '',
    lat: stop.lat ?? null,
    lng: stop.lng ?? null,
    pricePerCapita: stop.pricePerCapita ?? null,
    rating: stop.rating ?? null,
    walkFromPrevious: stop.walkFromPrevious || 0,
    tags: stop.tags || [],
    queueInfo: stop.queueInfo || null,
    durationMinutes: stop.durationMinutes || 50,
    done: false,
    checkinTime: null,
    alternatives: [],
  }))

  return {
    tripId: `draft-${planId}`,
    title: agentTrip.title || '小薇生成的路线草稿',
    city: agentTrip.city || DEFAULT_CITY,
    date: agentTrip.date || new Date().toISOString().slice(0, 10),
    totalBudget: agentTrip.totalBudget || (agentTrip.budgetValue ? `人均约${agentTrip.budgetValue}元` : ''),
    status: 'draft',
    overview: {
      ...(agentTrip.overview || {}),
      request: agentTrip.request || sourceMessage,
      source: 'agent-draft',
    },
    routeMap: agentTrip.routeMap || {},
    stops,
  }
}

function buildTripListItemFromDraft(trip: TripDetailPayload): TripListItemPayload {
  const overview = trip.overview || {}
  const stops = trip.stops || []

  return {
    tripId: trip.tripId,
    planId: trip.tripId.replace(/^draft-/, ''),
    title: `${trip.title}（待确认）`,
    city: trip.city,
    date: trip.date,
    status: trip.status,
    totalBudget: trip.totalBudget,
    type: typeof overview.type === 'string' ? overview.type : 'AI路线草稿',
    duration: typeof overview.duration === 'string' ? overview.duration : '',
    transportMode: typeof overview.transportMode === 'string' ? overview.transportMode : '',
    totalWalkMinutes: Number(overview.totalWalkMinutes ?? overview.walkDurationMinutes) || null,
    stopCount: stops.length,
    firstStop: stops[0]?.name || '',
    lastStop: stops.at(-1)?.name || '',
    source: 'agent-draft',
    createdAt: new Date().toISOString(),
  }
}

function getTripDedupeKey(item: TripListItemPayload) {
  const summaryKey = [
    item.title || '',
    item.date || '',
    item.firstStop || '',
    item.lastStop || '',
    item.stopCount || 0,
  ].join('|')

  return summaryKey.replace(/\s+/g, '').toLowerCase() || `plan:${item.planId || item.tripId}`
}

function dedupeTripList(items: TripListItemPayload[]) {
  const seen = new Set<string>()
  const result: TripListItemPayload[] = []

  for (const item of items) {
    const key = getTripDedupeKey(item)
    if (seen.has(key)) continue

    seen.add(key)
    result.push(item)
  }

  return result
}

async function applyAgentTrip(agentTrip: any, sourceMessage: string) {
  if (!agentTrip || !Array.isArray(agentTrip.stops) || agentTrip.stops.length === 0) {
    return
  }

  if (agentTrip.tripId && !String(agentTrip.tripId).startsWith('draft-')) {
    draftTrip.value = null
    currentTrip.value = agentTrip as TripDetailPayload
    await refreshTrips()
    return
  }

  draftTrip.value = buildDraftTripFromAgent(agentTrip, sourceMessage)
  currentTrip.value = draftTrip.value
}

function openPlaceDetail(detailOrRequest: PlaceDetail | PlaceDetailRequest) {
  if ('detail' in detailOrRequest) {
    selectedPlaceDetail.value = detailOrRequest.detail
    selectedPoiId.value = detailOrRequest.poiId ?? null
    placeDetailReturnScreen.value = detailOrRequest.returnScreen ?? 'itinerary'
  } else {
    selectedPlaceDetail.value = detailOrRequest
    selectedPoiId.value = null
    placeDetailReturnScreen.value = activeScreen.value === 'discover' ? 'discover' : 'itinerary'
  }

  activeScreen.value = 'placeDetail'
}

function goBackToItinerary() {
  activeScreen.value = 'itinerary'
}

function goBackFromPlaceDetail() {
  activeScreen.value = placeDetailReturnScreen.value
}

function goBackToChat() {
  activeScreen.value = 'chat'
}

function openChatThread(conversation: SelectedChatThread) {
  selectedChatThread.value = conversation
  activeScreen.value = 'chatDetail'
}

function addCreatedChatGroup(conversation: CreatedChatGroup) {
  const nextGroups = [
    conversation,
    ...createdChatGroups.value.filter((group) => group.id !== conversation.id),
  ]

  createdChatGroups.value = nextGroups
  saveCreatedChatGroups(currentUserId.value, nextGroups)
}

function goBackFromProfile() {
  activeScreen.value = profileReturnScreen.value === 'profile' ? 'ai1' : profileReturnScreen.value
}

function goBackFromSettings() {
  activeScreen.value = 'profile'
}

// AI5 偏好页状态
const ai5TimeType = ref('')
const ai5Activities = ref<string[]>([])
const ai5Range = ref('')
const ai5Budget = ref('')
const ai5Stay = ref('')
const ai5TimelineValue = ref(3) // 时间轴默认值，范围 1-6 小时

function selectAi5TimeType(type: string) {
  ai5TimeType.value = type

  if (type !== '周末两天') {
    ai5Stay.value = ''
  }
}

function toggleAi5Activity(tag: string) {
  const idx = ai5Activities.value.indexOf(tag)
  if (idx === -1) ai5Activities.value.push(tag)
  else ai5Activities.value.splice(idx, 1)
}

function buildPromptFromCard(card: CardData) {
  return [card.title, ...card.tags].join(' · ')
}

function ensureAiPrompt() {
  if (!aiPrompt.value.trim()) {
    aiPrompt.value = buildPromptFromCard(cardList[currentCardIndex.value])
  }

  return aiPrompt.value.trim()
}

function getPlanPreferences() {
  const timeType = ai5TimeType.value || '短时闲逛'
  const activities = ai5Activities.value.length ? [...ai5Activities.value] : [...cardList[currentCardIndex.value].tags]
  const geographicRange = ai5Range.value || '就近玩玩'
  const budget = ai5Budget.value || '100-200元'

  return {
    timeType,
    activities,
    geographicRange,
    budget,
    stay: ai5Stay.value,
    timelineHours: ai5TimelineValue.value,
  }
}

function buildCombinedPrompt() {
  const basePrompt = ensureAiPrompt()
  const preferences = getPlanPreferences()

  return [
    basePrompt,
    `游玩时间类型：${preferences.timeType}`,
    preferences.timeType === '短时闲逛' ? `预计可用时间：${preferences.timelineHours}小时` : '',
    preferences.stay ? `是否留宿：${preferences.stay}` : '',
    preferences.activities.length ? `活动偏好：${preferences.activities.join('、')}` : '',
    `出行范围：${preferences.geographicRange}`,
    `人均预算：${preferences.budget}`,
  ].filter(Boolean).join('；')
}

function applyCardPrompt(card: CardData) {
  aiPrompt.value = buildPromptFromCard(card)
  goToAi5()
}

function buildPlanRequest(): PlanGenerateRequest {
  const preferences = getPlanPreferences()

  return {
    timeType: preferences.timeType,
    activities: preferences.activities,
    geographicRange: preferences.geographicRange,
    budget: preferences.budget,
    prompt: buildCombinedPrompt(),
    city: DEFAULT_CITY,
  }
}

function buildTripPlan(plan: Plan, request: string) {
  return {
    title: plan.title,
    totalDuration: plan.duration,
    totalBudget: plan.budgetText,
    type: plan.type,
    source: 'plan-generate',
    request,
    spots: plan.spots,
  }
}

async function generateTripFromPreferences() {
  if (isGeneratingTrip.value) return

  isGeneratingTrip.value = true
  aiGenerationError.value = ''

  try {
    const planRequest = buildPlanRequest()
    const plans = await generatePlans(planRequest)
    const selectedPlan = plans[0]

    if (!selectedPlan) {
      throw new Error('未生成可用方案，请调整偏好后重试')
    }

    const createdTrip = await createTrip({
      userId: currentUserId.value,
      planId: selectedPlan.planId,
      plan: buildTripPlan(selectedPlan, planRequest.prompt || ensureAiPrompt()),
      city: DEFAULT_CITY,
    })

    currentTrip.value = createdTrip.trip
    draftTrip.value = null
    await refreshTrips()
    showItineraryList.value = false
    activeScreen.value = 'itinerary'
  } catch (error) {
    aiGenerationError.value = error instanceof Error ? error.message : '生成失败，请稍后重试'
  } finally {
    isGeneratingTrip.value = false
  }
}

async function scrollAiChatToBottom() {
  await nextTick()
  const el = aiChatThreadRef.value
  if (!el) return

  el.scrollTop = el.scrollHeight
}

function buildPlanningSupportMessage(result: ChatPayload, sourceMessage: string) {
  const trip = result.trip
  if (!trip) return ''

  const riskReminders = normalizeRiskReminders(
    trip.riskReminders || result.metadata?.riskReminders || inferRiskReminders(trip, sourceMessage),
  )
  const executionActions = normalizeExecutionActions(
    trip.executionActions || result.metadata?.executionActions || result.actions || [],
  )

  if (!riskReminders.length && !executionActions.length) return ''

  const lines = ['我还提前检查了几个可能的问题：']
  riskReminders.slice(0, 4).forEach((item, index) => {
    const title = item.title || '需要确认的点'
    const detail = item.detail ? `：${item.detail}` : ''
    lines.push(`${index + 1}. ${title}${detail}`)
  })

  if (executionActions.length) {
    lines.push('')
    lines.push('你确认方案后，我可以继续执行：')
    executionActions.slice(0, 4).forEach((action) => {
      lines.push(`- ${action.label || executionActionLabel(action.type)}`)
    })
  }

  const confirmMessage = trip.confirmMessage || result.metadata?.confirmMessage
  lines.push('')
  lines.push(confirmMessage || '你说“就这个”或“确认”，我就把它保存到行程，并继续处理预约、排队和分享动作。')
  return lines.join('\n')
}

function normalizeRiskReminders(items: unknown): PlanningRiskReminder[] {
  if (!Array.isArray(items)) return []
  return items
    .filter((item): item is PlanningRiskReminder => Boolean(item) && typeof item === 'object')
    .map((item) => ({
      type: String(item.type || ''),
      level: String(item.level || ''),
      title: String(item.title || ''),
      detail: String(item.detail || ''),
      action: String(item.action || ''),
    }))
    .filter((item) => item.title || item.detail)
}

function normalizeExecutionActions(items: unknown): PlanningExecutionAction[] {
  if (!Array.isArray(items)) return []
  return items
    .filter((item): item is PlanningExecutionAction => Boolean(item) && typeof item === 'object')
    .map((item) => ({
      type: String(item.type || ''),
      label: String(item.label || ''),
      status: String(item.status || ''),
    }))
    .filter((item) => item.type || item.label)
}

function inferRiskReminders(trip: any, sourceMessage: string): PlanningRiskReminder[] {
  const reminders: PlanningRiskReminder[] = []
  const stops = Array.isArray(trip.stops) ? trip.stops : []
  const totalWalk = Number(trip.totalWalkMinutes || trip.overview?.totalWalkMinutes || trip.overview?.walkDurationMinutes || 0)

  for (const stop of stops) {
    const queueInfo = stop.queueInfo || {}
    if (queueInfo.queueRisk === 'high' || queueInfo.queueRisk === 'medium') {
      reminders.push({
        title: `${stop.name || '这个点'}可能要等位`,
        detail: `预计等位约${queueInfo.waitMinutes || 15}分钟，建议提前预约或保留附近备选。`,
      })
    }
  }

  if (totalWalk >= 25) {
    reminders.push({
      title: '步行时间偏长',
      detail: `全程步行约${totalWalk}分钟，建议中间留一个可坐下休息的点。`,
    })
  }

  if (/孩子|小朋友|亲子|儿童/.test(sourceMessage)) {
    reminders.push({
      title: '亲子场景需要缓冲',
      detail: '孩子可能临时累或饿，最好每60-75分钟安排一次休息/补给。',
    })
  }

  if (/减肥|清淡|低脂|不吃辣|素食/.test(sourceMessage)) {
    reminders.push({
      title: '饮食偏好要提前标注',
      detail: '点餐时建议优先低脂清淡，避免重油重辣，并准备一两个替代菜。',
    })
  }

  if (/朋友|群|一起|多人/.test(sourceMessage)) {
    reminders.push({
      title: '多人同行要先确认',
      detail: '餐厅座位、儿童椅、预算和集合时间最好发给同行人确认一次。',
    })
  }

  if (!reminders.length) {
    reminders.push({
      title: '保留一个备选点',
      detail: '周末客流不稳定，建议同区域保留一家备选餐厅或咖啡。',
    })
  }

  return reminders.slice(0, 5)
}

function executionActionLabel(type?: string) {
  const labels: Record<string, string> = {
    reserve_or_queue: '预约/排队餐厅',
    reserve_restaurant: '预约餐厅',
    check_ticket: '确认门票和开放时间',
    buy_tickets: '购买门票',
    share_plan: '把计划发给同行人',
    save_trip: '保存行程',
    execute_arrangements: '执行预约、排队和分享',
  }
  return labels[type || ''] || '处理下一步动作'
}

async function sendAiChatMessage() {
  const message = aiPrompt.value.trim()
  if (!message || isChattingWithAgent.value) return

  aiMessages.value.push({ role: 'user', text: message })
  void scrollAiChatToBottom()
  aiPrompt.value = ''
  aiGenerationError.value = ''
  isChattingWithAgent.value = true
  void scrollAiChatToBottom()

  try {
    const result = await chatAgent({
      userId: currentUserId.value,
      sessionId: `ai-chat-${currentUserId.value}`,
      action: 'chat',
      message,
    })

    aiMessages.value.push({
      role: 'assistant',
      text: result.reply || '我已经收到啦，可以继续告诉我时间、预算或想玩的方向。',
    })

    const supportMessage = buildPlanningSupportMessage(result, message)
    if (supportMessage) {
      aiMessages.value.push({
        role: 'assistant',
        text: supportMessage,
      })
    }
    void scrollAiChatToBottom()

    if (result.trip) {
      await applyAgentTrip(result.trip, message)
    }
  } catch (error) {
    aiGenerationError.value = error instanceof Error ? error.message : '小薇暂时没有连上，请稍后再试'
  } finally {
    isChattingWithAgent.value = false
  }
}

// Phone simulator enhancements
const deviceType = ref<'iphone14' | 'iphone15' | 'iphone16' | 'iphone16pro'>('iphone16')
const isRotated = ref(false)
const screenBrightness = ref(100)
const screenZoom = ref(100)

const deviceSpecs = {
  iphone14: { name: 'iPhone 14', width: 390, height: 844 },
  iphone15: { name: 'iPhone 15', width: 393, height: 852 },
  iphone16: { name: 'iPhone 16', width: 393, height: 852 },
  iphone16pro: { name: 'iPhone 16 Pro', width: 402, height: 874 }
}

function toggleRotate() {
  isRotated.value = !isRotated.value
}

function resetSimulator() {
  screenBrightness.value = 100
  screenZoom.value = 100
  isRotated.value = false
}

function changeDevice(device: typeof deviceType.value) {
  deviceType.value = device
}

function takeScreenshot() {
  const shell = document.querySelector('.iphone-shell') as HTMLElement
  if (!shell) return
  
  // Simple approach: use html2canvas or built-in screenshot
  alert('Screenshot功能可通过集成html2canvas库实现 📸')
}
</script>

<template>
  <div class="preview-page">
    <!-- 控制面板 -->
    <div class="device-controls">
      <div class="control-section">
        <label class="control-label">设备选择</label>
        <div class="device-buttons">
          <button
            v-for="(spec, device) in deviceSpecs"
            :key="device"
            :class="['device-btn', { active: deviceType === device }]"
            @click="changeDevice(device as any)"
          >
            {{ spec.name }}
          </button>
        </div>
      </div>

      <div class="control-section">
        <label class="control-label">屏幕亮度: {{ screenBrightness }}%</label>
        <input
          v-model.number="screenBrightness"
          type="range"
          min="30"
          max="100"
          class="slider"
        />
      </div>

      <div class="control-section">
        <label class="control-label">缩放: {{ screenZoom }}%</label>
        <input
          v-model.number="screenZoom"
          type="range"
          min="50"
          max="150"
          step="10"
          class="slider"
        />
      </div>

      <div class="control-section">
        <div class="control-buttons">
          <button
            :class="['control-btn', { active: isRotated }]"
            @click="toggleRotate"
            title="旋转设备"
          >
            🔄 旋转
          </button>
          <button class="control-btn" @click="resetSimulator" title="重置模拟器">
            ↺ 重置
          </button>
          <button class="control-btn" @click="takeScreenshot" title="截图">
            📸 截图
          </button>
        </div>
      </div>

      <div class="device-info">
        <p><strong>当前设备:</strong> {{ deviceSpecs[deviceType].name }}</p>
        <p><strong>分辨率:</strong> {{ deviceSpecs[deviceType].width }} × {{ deviceSpecs[deviceType].height }}</p>
        <p><strong>状态:</strong> {{ isRotated ? '横屏模式' : '竖屏模式' }}</p>
      </div>
    </div>

    <!-- iPhone 外壳 -->
    <div
      class="iphone-shell"
      :style="{
        transform: `${isRotated ? 'rotate(90deg)' : ''} scale(${screenZoom / 100})`,
        filter: `brightness(${screenBrightness}%)`
      }"
    >
      <div class="iphone-body">
        <div class="dynamic-island"></div>

        <!-- 屏幕区域，严格 393×852 -->
        <div class="app-container">
          <main
            v-if="activeScreen === 'home1'"
            class="screen home1-screen"
            data-node-id="147:12"
            role="button"
            tabindex="0"
            @click="goToHome2"
            @keyup.enter="goToHome2"
            @keyup.space.prevent="goToHome2"
          >
            <div class="screen-bg" aria-hidden="true">
              <div class="bg-blob bg-blob-rose"></div>
              <div class="bg-blob bg-blob-gold"></div>
              <div class="bg-blob bg-blob-ivory"></div>
              <div class="bg-blob bg-blob-mist"></div>
            </div>

            <header class="status-bar" data-node-id="147:13">
              <div class="status-time" data-node-id="147:15">9:41</div>
              <div class="status-island" data-node-id="147:17"></div>
              <img :src="levelsAsset" alt="" class="status-levels" data-node-id="147:18" />
            </header>

            <section class="brand-block" data-node-id="147:786">
              <img :src="logoAsset" alt="Weekendgo Logo" class="brand-logo" data-node-id="147:801" />
              <h1 class="brand-title" data-node-id="147:35">Weekendgo</h1>
            </section>

            <p class="tagline" data-node-id="147:36">你的闲时逛逛搭子</p>

            <footer class="home-indicator-wrap" data-node-id="147:26">
              <div class="home-indicator" data-node-id="147:27"></div>
            </footer>
          </main>

          <main v-else-if="activeScreen === 'home2'" class="screen home2-screen" data-node-id="224:1574">
            <div class="screen-bg" aria-hidden="true">
              <div class="bg-blob bg-blob-rose home2-blob-rose"></div>
              <div class="bg-blob bg-blob-gold home2-blob-gold"></div>
              <div class="bg-blob bg-blob-ivory home2-blob-ivory"></div>
              <div class="bg-blob bg-blob-mist home2-blob-mist"></div>
            </div>

            <header class="status-bar" data-node-id="147:13">
              <div class="status-time" data-node-id="147:15">9:41</div>
              <div class="status-island" data-node-id="147:17"></div>
              <img :src="levelsAsset" alt="" class="status-levels" data-node-id="147:18" />
            </header>

            <section class="login-brand-block">
              <img :src="logoAsset" alt="Weekendgo Logo" class="login-brand-logo" />
              <h2 class="login-brand-title">Weekendgo</h2>
            </section>

            <section class="login-copy-block">
              <h1 class="login-title">轻松规划你的周末闲时活动 让每一刻都不浪费</h1>
            </section>

            <section class="login-form">
              <label class="login-field">
                <span class="login-field-label">昵称</span>
              </label>
              <label class="login-field">
                <span class="login-field-label">手机号</span>
              </label>
              <label class="login-field login-field-password">
                <span class="login-field-label">密码</span>
              </label>
            </section>

            <button type="button" class="login-button" @click="startDemoLogin(currentUserId)">登录</button>

            <section class="login-divider-row">
              <div class="login-divider-line"></div>
              <p class="login-divider-text">或者使用以下方式登录</p>
              <div class="login-divider-line"></div>
            </section>

            <section class="social-login-row">
              <button type="button" class="social-login-button" :aria-label="demoUsers[0].label" :title="demoUsers[0].label" @click="startDemoLogin(demoUsers[0].id)">
                <img :src="appleAsset" alt="" class="social-login-icon social-login-icon-apple" />
              </button>
              <button type="button" class="social-login-button" :aria-label="demoUsers[1].label" :title="demoUsers[1].label" @click="startDemoLogin(demoUsers[1].id)">
                <img :src="wechatAsset" alt="" class="social-login-icon" />
              </button>
              <button type="button" class="social-login-button" :aria-label="demoUsers[2].label" :title="demoUsers[2].label" @click="startDemoLogin(demoUsers[2].id)">
                <img :src="meituanAsset" alt="" class="social-login-icon" />
              </button>
            </section>

            <p class="signup-hint">
              还没有账户？
              <a href="#" class="signup-link">注册账号</a>
            </p>

            <footer class="home-indicator-wrap" data-node-id="147:26">
              <div class="home-indicator" data-node-id="147:27"></div>
            </footer>
          </main>

          <main v-else-if="activeScreen === 'onboarding'" class="screen onboarding-screen">
            <div class="screen-bg" aria-hidden="true">
              <div class="bg-blob bg-blob-rose"></div>
              <div class="bg-blob bg-blob-gold"></div>
              <div class="bg-blob bg-blob-ivory"></div>
              <div class="bg-blob bg-blob-mist"></div>
            </div>

            <header class="ai1-status-bar">
              <div class="ai1-status-time">9:41</div>
              <div class="ai1-status-island"></div>
              <img :src="levelsAsset" alt="" class="ai1-status-levels" />
            </header>

            <section class="onboarding-agent-card">
              <div class="onboarding-agent-orbit" aria-hidden="true">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <img :src="logoAsset" alt="" class="onboarding-agent-logo" />
              <p class="onboarding-agent-eyebrow">小薇正在了解你</p>
              <h1 class="onboarding-agent-title">生成你的本地生活画像</h1>
              <p class="onboarding-agent-copy">
                {{ isOnboardingProfile ? '正在读取模拟美团生态记录，区分真实消费、搜索兴趣和出行半径。' : onboardingReply }}
              </p>
              <div class="onboarding-agent-steps">
                <span :class="{ active: isOnboardingProfile || onboardingReply }">消费偏好</span>
                <span :class="{ active: isOnboardingProfile || onboardingReply }">活动半径</span>
                <span :class="{ active: onboardingReply }">规划习惯</span>
              </div>
              <p v-if="onboardingError" class="onboarding-agent-error">{{ onboardingError }}</p>
              <button type="button" class="onboarding-agent-button" :disabled="isOnboardingProfile" @click="finishOnboarding">
                {{ isOnboardingProfile ? '分析中...' : '开始使用' }}
              </button>
            </section>

            <footer class="home-indicator-wrap">
              <div class="home-indicator"></div>
            </footer>
          </main>

          <main v-else-if="activeScreen === 'ai1'" class="screen ai1-screen" data-node-id="210:628" @mousemove="handleMouseMove" @mouseup="handleMouseUp" @mouseleave="handleMouseUp">
            <!-- 背景光斑：纯 CSS 渐变，避免位图边缘伪影 -->
            <div class="ai1-bg" aria-hidden="true"></div>

            <!-- 状态栏 -->
            <header class="ai1-status-bar" data-node-id="210:638">
              <div class="ai1-status-time">9:41</div>
              <div class="ai1-status-island"></div>
              <img :src="ai1LevelsAsset" alt="" class="ai1-status-levels" />
            </header>

            <!-- 主标题 -->
            <h1 class="ai1-title" data-node-id="210:653">小薇</h1>

            <!-- 活动推荐卡：已隐藏，主入口改为小薇聊天 -->
            <div
              class="ai1-card"
              data-node-id="188:591"
              @touchstart="handleTouchStart"
              @touchend="handleTouchEnd"
              @mousedown="handleMouseDown"
            >
              <!-- 每张卡片独立背景色 -->
              <div class="ai1-card-bg" :style="{ background: cardList[currentCardIndex].cardBg }"></div>
              <!-- 图片区域 -->
              <div class="ai1-card-photo-wrap">
                <img :src="cardList[currentCardIndex].photo" :alt="cardList[currentCardIndex].title" class="ai1-card-photo" />
              </div>
              <!-- 标签（居中，top:122px） -->
              <div class="ai1-tags">
                <span
                  v-for="tag in cardList[currentCardIndex].tags"
                  :key="tag"
                  class="ai1-tag"
                  :style="{ background: cardList[currentCardIndex].tagColor, color: cardList[currentCardIndex].tagTextColor }"
                >{{ tag }}</span>
              </div>
              <!-- 卡片标题 -->
              <p class="ai1-card-title">{{ cardList[currentCardIndex].title }}</p>
              <!-- Go 按钞 -->
              <button type="button" class="ai1-card-go" aria-label="Go" @click="applyCardPrompt(cardList[currentCardIndex])">Go</button>
              <!-- 时间胶囊 -->
              <div class="ai1-card-time-pill">
                <span class="ai1-card-time-text">{{ cardList[currentCardIndex].time }}</span>
              </div>
            </div>

            <!-- 说明文字 -->
            <p class="ai1-hint" data-node-id="210:654">选一个状态，我来为你生成一条刚刚好的出行路线</p>

            <!-- 翻页指示点 -->
            <div class="ai1-dots" data-node-id="210:675">
              <span
                v-for="(_, index) in cardList"
                :key="index"
                class="ai1-dot"
                :class="{ 'ai1-dot-active': index === currentCardIndex }"
              ></span>
            </div>

            <section ref="aiChatThreadRef" class="ai1-chat-thread" aria-live="polite">
              <article
                v-for="(message, index) in aiMessages"
                :key="`${message.role}-${index}-${message.text}`"
                class="ai1-message"
                :class="{ mine: message.role === 'user' }"
              >
                <span>{{ message.role === 'assistant' ? '小薇' : '我' }}</span>
                <p>{{ message.text }}</p>
              </article>
              <article v-if="isChattingWithAgent" class="ai1-message typing">
                <span>小薇</span>
                <p>正在思考</p>
              </article>
            </section>

            <!-- 输入搜索栏 (left:19 top:537 w:357 h:47) -->
            <form class="ai1-input-bar ai1-chat-input-bar" data-node-id="233:1064" @submit.prevent="sendAiChatMessage">
              <img :src="ai1SparkIconAsset" alt="" class="ai1-input-spark" />
              <input
                v-model="aiPrompt"
                type="text"
                class="ai1-input-field"
                aria-label="输入出行想法"
                placeholder="和小薇聊聊你想怎么过"
                enterkeyhint="done"
              />
              <button type="submit" class="ai-input-submit" :disabled="isChattingWithAgent" aria-label="发送给小薇">
                <span class="ai-input-submit-icon" aria-hidden="true"></span>
              </button>
            </form>

            <p v-if="aiGenerationError" class="ai1-generation-error">
              {{ aiGenerationError }}
            </p>

            <!-- 底部导航背景胶囊 (left:33 top:765 w:327 h:54) -->
            <div class="ai1-nav-bg" data-node-id="233:997"></div>
            <!-- 个人 (left:41 top:768 size:48) -->
            <button
              type="button"
              class="ai1-nav-btn ai1-nav-btn-muted"
              style="left:41px;top:768px;"
              aria-label="个人"
              @click="setActiveScreen('profile')"
            >
              <img :src="ai1NavLeftAsset" alt="" class="ai1-nav-btn-user-icon" />
            </button>
            <!-- 发现 (left:113 top:768 size:48) -->
            <button
              type="button"
              class="ai1-nav-btn ai1-nav-btn-muted"
              style="left:113px;top:768px;"
              aria-label="发现"
              @click="setActiveScreen('discover')"
            >
              <img :src="ai1SearchAsset" alt="" class="ai1-nav-btn-search-icon" />
            </button>
            <!-- AI (left:177 top:768 size:48) -->
            <button
              type="button"
              class="ai1-nav-btn ai1-nav-btn-active"
              style="left:177px;top:768px;"
              aria-label="AI"
              aria-current="page"
              @click="setActiveScreen('ai1')"
            >
              <img :src="ai1NavCenterAsset" alt="" class="ai1-nav-btn-ai-icon" />
            </button>
            <!-- 行程 (left:240 top:768 size:48) -->
            <button
              type="button"
              class="ai1-nav-btn ai1-nav-btn-muted"
              style="left:240px;top:768px;"
              aria-label="行程"
              @click="setActiveScreen('itinerary')"
            >
              <img :src="ai1NavRightAsset" alt="" class="ai1-nav-btn-trip-icon" />
            </button>
            <!-- 聊天 (left:305 top:768 size:48) -->
            <button
              type="button"
              class="ai1-nav-btn ai1-nav-btn-muted"
              style="left:305px;top:768px;"
              aria-label="聊天"
              @click="setActiveScreen('chat')"
            >
              <img :src="ai1MicAsset" alt="" class="ai1-nav-btn-chat-icon" />
            </button>

            <!-- Home Indicator -->
            <footer class="home-indicator-wrap" data-node-id="210:651">
              <div class="home-indicator"></div>
            </footer>
          </main>

          <!-- AI偏好设置页 (node 224:1026) -->
          <main v-else-if="activeScreen === 'ai5'" class="screen ai5-screen" data-node-id="224:1026">
            <div class="screen-bg" aria-hidden="true">
              <div class="bg-blob bg-blob-rose"></div>
              <div class="bg-blob bg-blob-gold"></div>
              <div class="bg-blob bg-blob-ivory"></div>
              <div class="bg-blob bg-blob-mist"></div>
            </div>

            <!-- 状态栏 -->
            <header class="ai1-status-bar">
              <div class="ai1-status-time">9:41</div>
              <div class="ai1-status-island"></div>
              <img :src="levelsAsset" alt="" class="ai1-status-levels" />
            </header>

            <!-- 返回按鈕 -->
            <button type="button" class="ai5-back-btn" @click="activeScreen = 'ai1'" aria-label="返回">
              <span class="ai5-back-chevron"></span>
            </button>

            <!-- 页面标题 -->
            <h1 class="ai5-page-title">告诉我你的偏好</h1>

            <!-- 跳过 -->
            <button type="button" class="ai5-skip-btn" @click="activeScreen = 'itinerary'">跳过</button>

            <div class="ai5-scroll">
              <section class="ai5-section ai5-section-first">
                <p class="ai5-label">游玩时间类型</p>
                <div class="ai5-row ai5-row-pill">
                  <button class="ai5-pill" :class="{active: ai5TimeType==='短时闲逛'}" @click="selectAi5TimeType('短时闲逛')">短时闲逛</button>
                  <button class="ai5-pill" :class="{active: ai5TimeType==='城市一日'}" @click="selectAi5TimeType('城市一日')">城市一日</button>
                  <button class="ai5-pill" :class="{active: ai5TimeType==='周末两天'}" @click="selectAi5TimeType('周末两天')">周末两天</button>
                </div>
              </section>

              <section v-if="ai5TimeType === '短时闲逛'" class="ai5-section ai5-section-timeline">
                <div class="ai5-timeline-container">
                  <p class="ai5-timeline-label">预计可用时间</p>
                  <div class="ai5-timeline-track">
                    <span class="ai5-timeline-min">1小时</span>
                    <input
                      v-model.number="ai5TimelineValue"
                      type="range"
                      min="1"
                      max="6"
                      class="ai5-timeline-slider"
                    />
                    <span class="ai5-timeline-max">6小时</span>
                  </div>
                  <p class="ai5-timeline-current">{{ ai5TimelineValue }}小时</p>
                </div>
              </section>

              <section v-if="ai5TimeType === '周末两天'" class="ai5-section">
                <p class="ai5-label">是否在沪留宿</p>
                <div class="ai5-row ai5-row-stay">
                  <button class="ai5-pill ai5-pill--stay" :class="{active: ai5Stay==='是'}" @click="ai5Stay='是'">是</button>
                  <button class="ai5-pill ai5-pill--stay" :class="{active: ai5Stay==='否'}" @click="ai5Stay='否'">否</button>
                </div>
              </section>

              <section class="ai5-section">
                <p class="ai5-label">活动偏好 (多选)</p>
                <div class="ai5-chip-grid">
                  <button class="ai5-chip" :class="{active: ai5Activities.includes('寻味美食')}" @click="toggleAi5Activity('寻味美食')">寻味美食</button>
                  <button class="ai5-chip" :class="{active: ai5Activities.includes('喝咖啡')}" @click="toggleAi5Activity('喝咖啡')">喝咖啡</button>
                  <button class="ai5-chip" :class="{active: ai5Activities.includes('逛街区')}" @click="toggleAi5Activity('逛街区')">逛街区</button>
                  <button class="ai5-chip" :class="{active: ai5Activities.includes('手作体验')}" @click="toggleAi5Activity('手作体验')">手作体验</button>
                  <button class="ai5-chip" :class="{active: ai5Activities.includes('城市散步')}" @click="toggleAi5Activity('城市散步')">城市散步</button>
                  <button class="ai5-chip" :class="{active: ai5Activities.includes('拍照打卡')}" @click="toggleAi5Activity('拍照打卡')">拍照打卡</button>
                  <button class="ai5-chip" :class="{active: ai5Activities.includes('书店阅读')}" @click="toggleAi5Activity('书店阅读')">书店阅读</button>
                  <button class="ai5-chip" :class="{active: ai5Activities.includes('看展览')}" @click="toggleAi5Activity('看展览')">看展览</button>
                </div>
              </section>

              <section class="ai5-section">
                <p class="ai5-label">出行范围</p>
                <div class="ai5-row ai5-row-pill">
                  <button class="ai5-pill" :class="{active: ai5Range==='就近玩玩'}" @click="ai5Range='就近玩玩'">就近玩玩</button>
                  <button class="ai5-pill" :class="{active: ai5Range==='地铁30分钟'}" @click="ai5Range='地铁30分钟'">地铁30分钟</button>
                  <button class="ai5-pill" :class="{active: ai5Range==='可以跨区'}" @click="ai5Range='可以跨区'">可以跨区</button>
                </div>
              </section>

              <section class="ai5-section">
                <p class="ai5-label">人均预算</p>
                <div class="ai5-budget-grid">
                  <button class="ai5-budget" :class="{active: ai5Budget==='100元内'}" @click="ai5Budget='100元内'">100元内</button>
                  <button class="ai5-budget" :class="{active: ai5Budget==='100-200元'}" @click="ai5Budget='100-200元'">100-200元</button>
                  <button class="ai5-budget" :class="{active: ai5Budget==='200-300元'}" @click="ai5Budget='200-300元'">200-300元</button>
                  <button class="ai5-budget" :class="{active: ai5Budget==='不限'}" @click="ai5Budget='不限'">不限</button>
                </div>
              </section>

              <button type="button" class="ai5-cta-btn" :disabled="isGeneratingTrip" :aria-busy="isGeneratingTrip" @click="generateTripFromPreferences">
                {{ isGeneratingTrip ? '正在生成中...' : '生成我的闲时计划' }}<span class="ai5-cta-lightning">⚡</span>
              </button>

              <p v-if="aiGenerationError" style="margin: 12px 18px 0; color: #8b2f45; font-size: 13px; line-height: 1.5;">
                {{ aiGenerationError }}
              </p>
            </div>

            <!-- Home Indicator -->
            <footer class="home-indicator-wrap">
              <div class="home-indicator"></div>
            </footer>
          </main>

          <!-- 行程页 (node 156:994) -->
          <main v-else-if="activeScreen === 'itinerary'" class="screen" data-node-id="156:994">
            <ItineraryPage
              :trip="currentTrip"
              :trips="displayedTrips"
              :loading-trips="isLoadingTrips"
              :show-list="showItineraryList"
              @navigate="setActiveScreen"
              @view-detail="openPlaceDetail"
              @select-trip="openTripFromList"
              @back-to-list="backToTripList"
              @refresh-trips="refreshTrips"
            />
          </main>

          <main v-else-if="activeScreen === 'discover'" class="screen" data-node-id="156:553">
            <DiscoverPage @navigate="setActiveScreen" @view-detail="openPlaceDetail" />
          </main>

          <main v-else-if="activeScreen === 'profile'" class="screen" data-node-id="156:729">
            <ProfilePage :user-id="currentUserId" @navigate="setActiveScreen" @back="goBackFromProfile" />
          </main>

          <main v-else-if="activeScreen === 'settings'" class="screen" data-node-id="187:265">
            <SettingsPage @back="goBackFromSettings" @logout="logoutCurrentUser" />
          </main>

          <main v-else-if="activeScreen === 'createPost'" class="screen" data-node-id="181:320">
            <CreatePostPage @navigate="setActiveScreen" />
          </main>

          <main v-else-if="activeScreen === 'chat'" class="screen" data-node-id="155:61">
            <ChatPage
              :user-id="currentUserId"
              :created-groups="createdChatGroups"
              @navigate="setActiveScreen"
              @open-conversation="openChatThread"
              @create-group="addCreatedChatGroup"
            />
          </main>

          <main v-else-if="activeScreen === 'chatDetail'" class="screen" data-node-id="155:314">
            <ChatThreadPage
              :key="`${selectedChatThread.isGroup ? 'group' : 'friend'}-${selectedChatThread.id}-${selectedChatThread.memberIds?.join('-') || 'default'}`"
              :user-id="currentUserId"
              :thread-type="selectedChatThread.isGroup ? 'group' : 'friend'"
              :friend-id="selectedChatThread.isGroup ? undefined : selectedChatThread.id"
              :group-member-ids="selectedChatThread.memberIds"
              @back="goBackToChat"
            />
          </main>

          <main v-else-if="activeScreen === 'navigation'" class="screen" data-node-id="174:375">
            <NavigationPage @back="goBackToItinerary" />
          </main>

          <main v-else-if="activeScreen === 'placeDetail'" class="screen" data-node-id="233:1138">
            <PlaceDetailPage v-if="selectedPlaceDetail" :detail="selectedPlaceDetail" :poi-id="selectedPoiId" @back="goBackFromPlaceDetail" />
          </main>
        </div>
      </div>

      <!-- 侧边按钮 -->
      <div class="side-buttons left">
        <div class="btn-mute"></div>
        <div class="btn-vol-up"></div>
        <div class="btn-vol-down"></div>
      </div>
      <div class="side-buttons right">
        <div class="btn-power"></div>
      </div>
    </div>
  </div>
</template>
