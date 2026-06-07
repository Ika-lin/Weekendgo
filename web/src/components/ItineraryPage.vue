<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { getTripAlternatives, getTripReminders, getTripWeather, replaceTripStop, type TripAlternativePayload, type TripDetailPayload, type TripListItemPayload, type TripReminderPayload, type TripStopPayload, type TripWeatherPayload } from '../api'
import ItineraryMap from './ItineraryMap.vue'
import { itineraryKilometersPerPixel, itinerarySegmentAccessKilometers, itineraryWalkMinutesPerKilometer, routePointMap, type RoutePoint } from '../data/itineraryRoute'
import { resolvePlaceDetail, type PlaceDetail } from '../data/placeDetails'

const props = defineProps<{
  trip?: TripDetailPayload | null
  trips?: TripListItemPayload[]
  loadingTrips?: boolean
  showList?: boolean
}>()

const emit = defineEmits<{
  navigate: [screen: 'ai1' | 'discover' | 'itinerary' | 'navigation' | 'chat' | 'profile']
  viewDetail: [payload: { detail: PlaceDetail; poiId?: string | null; returnScreen: 'itinerary' }]
  selectTrip: [tripId: string]
  backToList: []
  refreshTrips: []
}>()

const levelsAsset = '/Levels.svg'
const addressStartAsset = '/Location Icon.svg'
const addressEndAsset = '/map-pin.svg'
const moreVerticalAsset = '/more-vertical.svg'
const swapAsset = '/iconamoon_swap.svg'
const startAsset = '/Start Icon.svg'
const walkAsset = '/CaretDoubleDown.svg'
const clockAsset = '/clock.svg'
const composerSparkAsset = '/Icon-3.svg'
const composerMicAsset = '/Group 3.svg'
const navProfileAsset = '/user.svg'
const navSearchAsset = '/MagnifyingGlass.svg'
const navAiAsset = '/Icon-3.svg'
const navTripAsset = '/lucide_map.svg'
const navChatAsset = '/ChatTeardrop-dark.svg'

type SwapGroup = 'culture' | 'coffee' | 'food'

type PriceRange = {
  min: number
  max: number
}

type MapPoint = RoutePoint

type StopBlueprint = {
  venueKey: string
  swapGroup: SwapGroup
  timeLabel: string
  durationMinutes: number
  title: string
  tags: string[]
  priceRange: PriceRange
  routePoint: MapPoint
  stopId?: string
  poiId?: string
}

type ItineraryStop = StopBlueprint & {
  id: number
}

type ReplacementOption = StopBlueprint & {
  id: string
  summary: string
}

type RemoteSwapOption = {
  id: string
  title: string
  priceLabel: string
  travelLabel: string
  summary: string
  candidateId: string
  categoryTags: string[]
  rawPriceRange: string
  kind: 'remote'
}

type LocalSwapOptionView = ReplacementOption & {
  priceLabel: string
  travelLabel: string
  kind: 'local'
}

type StopLayout = {
  walkTop: number
  cardTop: number
  cardHeight: number
  markerTop: number
  connectorTop: number
  connectorHeight: number
}

type ReminderItem = {
  id: string
  text: string
  done: boolean
}

type PackingItem = {
  id: string
  text: string
  checked: boolean
}

type AdjustmentItem = {
  id: string
  label: string
  emphasized: boolean
}

type TravelSegment = {
  distanceKm: number
  averageMinutes: number
  label: string
}

type RemovedStopNotice = {
  stop: ItineraryStop
  index: number
}

const defaultStartLocation = '上海市徐汇区武康路 376 号附近'
const defaultEndLocation = '上海市徐汇区上海图书馆地铁站'
const startMapPoint: MapPoint = routePointMap.start
const endMapPoint: MapPoint = routePointMap.end

const startLocation = ref(defaultStartLocation)
const endLocation = ref(defaultEndLocation)

let dynamicItemSeed = 0
let stopInstanceSeed = 0
let removedStopTimer: ReturnType<typeof setTimeout> | null = null

function createDynamicId(prefix: string) {
  dynamicItemSeed += 1
  return `${prefix}-${dynamicItemSeed}`
}

function clonePriceRange(priceRange: PriceRange): PriceRange {
  return {
    min: priceRange.min,
    max: priceRange.max,
  }
}

function clonePoint(point: MapPoint): MapPoint {
  return {
    x: point.x,
    y: point.y,
  }
}

function cloneStop(stop: ItineraryStop): ItineraryStop {
  return {
    id: stop.id,
    stopId: stop.stopId,
    poiId: stop.poiId,
    venueKey: stop.venueKey,
    swapGroup: stop.swapGroup,
    timeLabel: stop.timeLabel,
    durationMinutes: stop.durationMinutes,
    title: stop.title,
    tags: [...stop.tags],
    priceRange: clonePriceRange(stop.priceRange),
    routePoint: clonePoint(stop.routePoint),
  }
}

function createStopInstance(blueprint: StopBlueprint, forcedId?: number): ItineraryStop {
  const nextId = forcedId ?? stopInstanceSeed + 1
  stopInstanceSeed = Math.max(stopInstanceSeed, nextId)

  return {
    id: nextId,
    stopId: blueprint.stopId,
    poiId: blueprint.poiId,
    venueKey: blueprint.venueKey,
    swapGroup: blueprint.swapGroup,
    timeLabel: blueprint.timeLabel,
    durationMinutes: blueprint.durationMinutes,
    title: blueprint.title,
    tags: [...blueprint.tags],
    priceRange: clonePriceRange(blueprint.priceRange),
    routePoint: clonePoint(blueprint.routePoint),
  }
}

const stopLayouts: StopLayout[] = [
  { walkTop: 711, cardTop: 742, cardHeight: 140, markerTop: 742, connectorTop: 767, connectorHeight: 169 },
  { walkTop: 905, cardTop: 942, cardHeight: 144, markerTop: 942, connectorTop: 964, connectorHeight: 169 },
  { walkTop: 1110, cardTop: 1146, cardHeight: 141, markerTop: 1146, connectorTop: 1171, connectorHeight: 169 },
]

const maxVisibleStops = stopLayouts.length

const defaultStopBlueprints: StopBlueprint[] = [
  {
    venueKey: 'film-bookstore',
    swapGroup: 'culture',
    timeLabel: '14:08 - 14:55（50分钟）',
    durationMinutes: 50,
    title: 'FILM电影时光书店',
    tags: ['电影主题', '安静翻阅', '胶片气质'],
    priceRange: { min: 43, max: 43 },
    routePoint: routePointMap.filmBookstore,
  },
  {
    venueKey: 'rac-anfu',
    swapGroup: 'coffee',
    timeLabel: '15:00 - 16:00（60分钟）',
    durationMinutes: 60,
    title: 'RAC BAR（安福路店）',
    tags: ['街角咖啡', '露台小坐', '法式风情'],
    priceRange: { min: 120, max: 150 },
    routePoint: routePointMap.racBar,
  },
  {
    venueKey: 'spring-noodle',
    swapGroup: 'food',
    timeLabel: '16:10 - 16:50（40分钟）',
    durationMinutes: 40,
    title: '一面春风（吴兴路总店/武康周边）',
    tags: ['烟火小馆', '本帮风味', '匠心汤底'],
    priceRange: { min: 55, max: 70 },
    routePoint: routePointMap.springNoodle,
  },
]

const replacementOptionsByGroup: Record<SwapGroup, ReplacementOption[]> = {
  culture: [
    {
      id: 'film-default',
      venueKey: 'film-bookstore',
      swapGroup: 'culture',
      timeLabel: '14:08 - 14:55（50分钟）',
      durationMinutes: 50,
      title: 'FILM电影时光书店',
      tags: ['电影主题', '安静翻阅', '胶片气质'],
      priceRange: { min: 43, max: 43 },
      routePoint: routePointMap.filmBookstore,
      summary: '电影主题和书店氛围都比较完整',
    },
    {
      id: 'duozhuayu',
      venueKey: 'duozhuayu-cycle',
      swapGroup: 'culture',
      timeLabel: '14:08 - 14:55（50分钟）',
      durationMinutes: 45,
      title: '多抓鱼循环商店',
      tags: ['循环商店', '旧书淘选', '服饰闲逛'],
      priceRange: { min: 60, max: 70 },
      routePoint: routePointMap.duozhuayu,
      summary: '二手书和服饰都能逛，路线改动最小',
    },
    {
      id: 'hengshanheji',
      venueKey: 'hengshanheji',
      swapGroup: 'culture',
      timeLabel: '14:08 - 14:55（50分钟）',
      durationMinutes: 55,
      title: '衡山和集',
      tags: ['复合空间', '慢逛停留', '书店展陈'],
      priceRange: { min: 35, max: 45 },
      routePoint: routePointMap.hengshanheji,
      summary: '空间更完整，适合慢慢停留',
    },
  ],
  coffee: [
    {
      id: 'rac-default',
      venueKey: 'rac-anfu',
      swapGroup: 'coffee',
      timeLabel: '15:00 - 16:00（60分钟）',
      durationMinutes: 60,
      title: 'RAC BAR（安福路店）',
      tags: ['街角咖啡', '露台小坐', '法式风情'],
      priceRange: { min: 120, max: 150 },
      routePoint: routePointMap.racBar,
      summary: '露台氛围稳定，适合中段放松',
    },
    {
      id: 'manner-anfu',
      venueKey: 'manner-anfu',
      swapGroup: 'coffee',
      timeLabel: '15:00 - 16:00（60分钟）',
      durationMinutes: 45,
      title: 'MANNER COFFEE（安福路店）',
      tags: ['精品咖啡', '出杯很快', '街边停留'],
      priceRange: { min: 28, max: 40 },
      routePoint: routePointMap.mannerAnfu,
      summary: '出杯更快，适合轻量停留',
    },
    {
      id: 'cafe-del-volcan',
      venueKey: 'cafe-del-volcan',
      swapGroup: 'coffee',
      timeLabel: '15:00 - 16:00（60分钟）',
      durationMinutes: 60,
      title: 'Café del Volcán',
      tags: ['空间更松弛', '慢坐聊天', '风味咖啡'],
      priceRange: { min: 36, max: 52 },
      routePoint: routePointMap.cafeDelVolcan,
      summary: '空间更松弛，适合慢聊久坐',
    },
  ],
  food: [
    {
      id: 'spring-default',
      venueKey: 'spring-noodle',
      swapGroup: 'food',
      timeLabel: '16:10 - 16:50（40分钟）',
      durationMinutes: 40,
      title: '一面春风（吴兴路总店/武康周边）',
      tags: ['烟火小馆', '本帮风味', '匠心汤底'],
      priceRange: { min: 55, max: 70 },
      routePoint: routePointMap.springNoodle,
      summary: '热面收尾更轻松，节奏比较稳',
    },
    {
      id: 'lanxin',
      venueKey: 'lanxin',
      swapGroup: 'food',
      timeLabel: '16:10 - 16:50（40分钟）',
      durationMinutes: 55,
      title: '兰心餐厅（进贤路店）',
      tags: ['本帮经典', '收尾更稳', '口味扎实'],
      priceRange: { min: 70, max: 90 },
      routePoint: routePointMap.lanxin,
      summary: '本帮味更稳，适合经典收尾',
    },
    {
      id: 'wuyuan',
      venueKey: 'wuyuan-noodle',
      swapGroup: 'food',
      timeLabel: '16:10 - 16:50（40分钟）',
      durationMinutes: 35,
      title: '福和面馆（武康路附近）',
      tags: ['轻量晚餐', '热汤面食', '快速结束'],
      priceRange: { min: 32, max: 48 },
      routePoint: routePointMap.fuheNoodle,
      summary: '热汤面食更轻松，适合快速收尾',
    },
  ],
}

function buildAllStopBlueprints(): StopBlueprint[] {
  const blueprintMap = new Map<string, StopBlueprint>()

  for (const blueprint of defaultStopBlueprints) {
    blueprintMap.set(blueprint.venueKey, blueprint)
  }

  for (const option of Object.values(replacementOptionsByGroup).flat()) {
    if (!blueprintMap.has(option.venueKey)) {
      blueprintMap.set(option.venueKey, {
        venueKey: option.venueKey,
        swapGroup: option.swapGroup,
        timeLabel: option.timeLabel,
        durationMinutes: option.durationMinutes,
        title: option.title,
        tags: [...option.tags],
        priceRange: clonePriceRange(option.priceRange),
        routePoint: clonePoint(option.routePoint),
      })
    }
  }

  return Array.from(blueprintMap.values())
}

const allStopBlueprints = buildAllStopBlueprints()

function normalizeVenueTitle(value: string) {
  return value.replace(/（.*?）/g, '').trim().toLowerCase()
}

function findBlueprintForTripStop(stop: TripStopPayload, fallbackIndex: number) {
  const stopName = normalizeVenueTitle(stop.name || '')

  if (stopName) {
    const matchedBlueprint = allStopBlueprints.find((blueprint) => {
      const blueprintName = normalizeVenueTitle(blueprint.title)
      return blueprintName === stopName || blueprintName.includes(stopName) || stopName.includes(blueprintName)
    })

    if (matchedBlueprint) {
      return matchedBlueprint
    }
  }

  return defaultStopBlueprints[Math.min(fallbackIndex, defaultStopBlueprints.length - 1)]
}

function buildTripStopTimeLabel(stop: TripStopPayload, fallback: StopBlueprint) {
  if (stop.time && stop.endTime) {
    const durationSuffix = stop.durationMinutes ? `（${stop.durationMinutes}分钟）` : ''
    return `${stop.time} - ${stop.endTime}${durationSuffix}`
  }

  if (stop.time && stop.durationMinutes) {
    return `${stop.time}（${stop.durationMinutes}分钟）`
  }

  if (stop.time) {
    return stop.time
  }

  return fallback.timeLabel
}

function buildTripStopPriceRange(stop: TripStopPayload, fallback: StopBlueprint): PriceRange {
  const priceValue = Number(stop.pricePerCapita)

  if (Number.isFinite(priceValue) && priceValue > 0) {
    return { min: priceValue, max: priceValue }
  }

  return clonePriceRange(fallback.priceRange)
}

function createStopFromTrip(stop: TripStopPayload, fallbackIndex: number) {
  const fallbackBlueprint = findBlueprintForTripStop(stop, fallbackIndex)

  return createStopInstance(
    {
      venueKey: fallbackBlueprint.venueKey,
      swapGroup: fallbackBlueprint.swapGroup,
      timeLabel: buildTripStopTimeLabel(stop, fallbackBlueprint),
      durationMinutes: stop.durationMinutes || fallbackBlueprint.durationMinutes,
      title: stop.name || fallbackBlueprint.title,
      tags: stop.tags?.length ? [...stop.tags] : [...fallbackBlueprint.tags],
      priceRange: buildTripStopPriceRange(stop, fallbackBlueprint),
      routePoint: clonePoint(fallbackBlueprint.routePoint),
      stopId: stop.stopId,
      poiId: stop.poiId,
    },
    fallbackIndex + 1,
  )
}

function buildPackingItems(items: string[]) {
  return items.map((text, index) => ({
    id: `packing-remote-${index + 1}`,
    text,
    checked: false,
  }))
}

function buildRemindersFromApi(reminders: TripReminderPayload | null, weather: TripWeatherPayload | null, fallback: TripDetailPayload) {
  const merged = [
    weather ? `${weather.condition} ${weather.temperatureText}` : '',
    ...(reminders?.today || []),
    ...((weather?.agentTips || []).slice(0, 2)),
  ].filter((item): item is string => typeof item === 'string' && item.trim().length > 0)

  if (merged.length) {
    return Array.from(new Set(merged)).slice(0, 5).map((text, index) => ({
      id: `reminder-api-${index + 1}`,
      text,
      done: false,
    }))
  }

  return buildRemindersFromTrip(fallback)
}

function parseRemotePriceRange(value: string, fallback: PriceRange) {
  const matched = value.match(/(\d+)/g)
  if (!matched || matched.length === 0) {
    return clonePriceRange(fallback)
  }

  const values = matched.map((item) => Number(item)).filter((item) => Number.isFinite(item))
  if (!values.length) {
    return clonePriceRange(fallback)
  }

  return {
    min: values[0],
    max: values[1] ?? values[0],
  }
}

function buildRemindersFromTrip(trip: TripDetailPayload): ReminderItem[] {
  const overview = trip.overview || {}
  const fitReasons = Array.isArray(overview.fitReasons) ? overview.fitReasons : []
  const conflicts = Array.isArray(overview.conflicts) ? overview.conflicts : []
  const merged = [...fitReasons, ...conflicts].filter((item): item is string => typeof item === 'string' && item.trim().length > 0)

  if (merged.length) {
    return merged.slice(0, 3).map((text, index) => ({
      id: `reminder-trip-${index + 1}`,
      text,
      done: false,
    }))
  }

  const firstStop = trip.stops[0]
  return [
    {
      id: 'reminder-trip-default',
      text: firstStop?.queueInfo || `${trip.city || '当前城市'}行程已同步`,
      done: false,
    },
  ]
}

const itineraryStops = ref<ItineraryStop[]>([])
const hasStops = computed(() => itineraryStops.value.length > 0)
const tripListItems = computed(() => props.trips || [])
const hasTripListItems = computed(() => tripListItems.value.length > 0)
const activeSwapStopId = ref<number | null>(null)
const scrollRoot = ref<HTMLElement | null>(null)
const draggingStopId = ref<number | null>(null)
const dragOverStopId = ref<number | null>(null)
const removedStopNotice = ref<RemovedStopNotice | null>(null)
const remoteSwapOptions = ref<Record<number, RemoteSwapOption[]>>({})
const loadingSwapStopId = ref<number | null>(null)

function formatStopPrice(priceRange: PriceRange) {
  if (priceRange.min === priceRange.max) {
    return `人均 ¥${priceRange.min}`
  }

  return `人均 ¥${priceRange.min}-${priceRange.max}`
}

function formatBudgetEstimate(minPrice: number, maxPrice: number) {
  if (minPrice === 0 && maxPrice === 0) {
    return '--'
  }

  if (minPrice === maxPrice) {
    return `¥${minPrice}/人`
  }

  return `¥${minPrice}-${maxPrice}/人`
}

function formatSwapOptionPrice(priceRange: PriceRange) {
  if (priceRange.min === priceRange.max) {
    return `约￥${priceRange.min}`
  }

  return `约￥${priceRange.min}-${priceRange.max}`
}

function formatDistance(distanceKm: number) {
  if (distanceKm <= 0) return '--'
  return `约${distanceKm.toFixed(1)}km`
}

function formatWalkTotal(totalMinutes: number) {
  if (totalMinutes <= 0) return '--'
  return `约${Math.round(totalMinutes)}分钟`
}

function formatTravelLabel(averageMinutes: number) {
  if (averageMinutes >= 6.2) {
    const min = Math.max(3, Math.floor(averageMinutes - 0.8))
    const max = Math.max(min + 1, Math.ceil(averageMinutes + 0.8))
    return `步行约 ${min}-${max} 分钟`
  }

  if (averageMinutes >= 4.6) {
    return `步行约 ${Math.max(3, Math.round(averageMinutes))} 分钟`
  }

  const min = Math.max(3, Math.floor(averageMinutes - 0.6))
  const max = Math.max(min + 1, Math.ceil(averageMinutes + 0.4))
  return `步行约 ${min}-${max} 分钟`
}

function calculateTravelSegment(fromPoint: MapPoint, toPoint: MapPoint): TravelSegment {
  const distancePx = Math.hypot(toPoint.x - fromPoint.x, toPoint.y - fromPoint.y)
  const distanceKm = Number((distancePx * itineraryKilometersPerPixel + itinerarySegmentAccessKilometers).toFixed(2))
  const averageMinutes = distanceKm * itineraryWalkMinutesPerKilometer

  return {
    distanceKm,
    averageMinutes,
    label: formatTravelLabel(averageMinutes),
  }
}

const mapStopPoints = computed(() => itineraryStops.value.map((stop) => clonePoint(stop.routePoint)))
const mapRoutePoints = computed(() => (hasStops.value ? [startMapPoint, ...mapStopPoints.value, endMapPoint] : []))

const routeSegments = computed(() => {
  const orderedPoints = [startMapPoint, ...mapStopPoints.value, endMapPoint]

  return orderedPoints.slice(0, -1).map((point, index) => calculateTravelSegment(point, orderedPoints[index + 1]))
})

const itinerarySummaryStats = computed(() => {
  if (!hasStops.value) {
    return [
      { label: '总路程', value: '--' },
      { label: '预算估测', value: '--' },
      { label: '交通方式', value: '待生成' },
      { label: '步行时间', value: '--' },
    ]
  }

  const totalDistance = routeSegments.value.reduce((sum, segment) => sum + segment.distanceKm, 0)
  const totalWalkMinutes = routeSegments.value.reduce((sum, segment) => sum + segment.averageMinutes, 0)
  const minBudget = itineraryStops.value.reduce((sum, stop) => sum + stop.priceRange.min, 0)
  const maxBudget = itineraryStops.value.reduce((sum, stop) => sum + stop.priceRange.max, 0)
  const tripOverview = props.trip?.overview || {}
  const tripDistance = Number(tripOverview.distanceKm)
  const tripWalkMinutes = Number(tripOverview.totalWalkMinutes ?? tripOverview.walkDurationMinutes)
  const tripTransportMode = typeof tripOverview.transportMode === 'string' ? tripOverview.transportMode : ''

  return [
    { label: '总路程', value: Number.isFinite(tripDistance) && tripDistance > 0 ? formatDistance(tripDistance) : formatDistance(totalDistance) },
    { label: '预算估测', value: props.trip?.totalBudget || formatBudgetEstimate(minBudget, maxBudget) },
    { label: '交通方式', value: tripTransportMode || '全程步行' },
    { label: '步行时间', value: Number.isFinite(tripWalkMinutes) && tripWalkMinutes > 0 ? formatWalkTotal(tripWalkMinutes) : formatWalkTotal(totalWalkMinutes) },
  ]
})

const routeOriginLabel = computed(() => startLocation.value.trim() || defaultStartLocation)
const routeDestinationLabel = computed(() => endLocation.value.trim() || defaultEndLocation)

function restoreLocationDefaults() {
  startLocation.value = defaultStartLocation
  endLocation.value = defaultEndLocation
}

function swapLocations() {
  const previousStart = startLocation.value
  startLocation.value = endLocation.value
  endLocation.value = previousStart
}

const positionedStops = computed(() =>
  itineraryStops.value.map((stop, index) => ({
    ...stop,
    ...stopLayouts[index],
    order: index + 1,
    titleWide: stop.title.length >= 14,
    time: stop.timeLabel,
    price: formatStopPrice(stop.priceRange),
    walkFromPreviousLabel: routeSegments.value[index]?.label ?? '步行约 0 分钟',
  })),
)

const finalWalkTop = computed(() => {
  const lastStop = positionedStops.value[positionedStops.value.length - 1]
  if (!lastStop) return null

  return lastStop.cardTop + 158
})

const lowerContentTop = computed(() => {
  const lastStop = positionedStops.value[positionedStops.value.length - 1]
  if (!lastStop) return 711

  return lastStop.cardTop + 200
})

const finalWalkLabel = computed(() => {
  if (!hasStops.value) return ''
  return routeSegments.value[routeSegments.value.length - 1]?.label ?? ''
})

const activeSwapStop = computed(() => {
  if (activeSwapStopId.value === null) return null
  return itineraryStops.value.find((stop) => stop.id === activeSwapStopId.value) ?? null
})

const activeSwapStopOrder = computed(() => {
  if (activeSwapStopId.value === null) return null

  const index = itineraryStops.value.findIndex((stop) => stop.id === activeSwapStopId.value)
  return index === -1 ? null : index + 1
})

const activeSwapOptions = computed<Array<LocalSwapOptionView | RemoteSwapOption>>(() => {
  if (activeSwapStop.value === null) return []

  if (activeSwapStop.value.id in remoteSwapOptions.value) {
    return remoteSwapOptions.value[activeSwapStop.value.id]
  }

  return replacementOptionsByGroup[activeSwapStop.value.swapGroup]
    .filter((option) => option.venueKey !== activeSwapStop.value?.venueKey)
    .map((option) => ({
      ...option,
      priceLabel: formatSwapOptionPrice(option.priceRange),
      travelLabel: calculateTravelSegment(activeSwapStop.value!.routePoint, option.routePoint).label,
      kind: 'local' as const,
    }))
})

async function openSwapOptions(stopId: number) {
  activeSwapStopId.value = stopId

  const stop = itineraryStops.value.find((item) => item.id === stopId)
  if (!stop || !props.trip?.tripId || !stop.stopId || stopId in remoteSwapOptions.value) {
    return
  }

  loadingSwapStopId.value = stopId

  try {
    const data = await getTripAlternatives(props.trip.tripId, stop.stopId)
    remoteSwapOptions.value = {
      ...remoteSwapOptions.value,
      [stopId]: (data.alternatives || []).map((option: TripAlternativePayload) => ({
        id: option.candidateId,
        candidateId: option.candidateId,
        title: option.name,
        categoryTags: option.categoryTags || [],
        priceLabel: `约￥${option.priceRange}`,
        rawPriceRange: option.priceRange,
        travelLabel: `步行约 ${option.walkMinutes} 分钟`,
        summary: option.reason,
        kind: 'remote' as const,
      })),
    }
  } catch {
    remoteSwapOptions.value = {
      ...remoteSwapOptions.value,
      [stopId]: [],
    }
  } finally {
    loadingSwapStopId.value = null
  }
}

function closeSwapOptions() {
  activeSwapStopId.value = null
}

function clearStopDragState() {
  draggingStopId.value = null
  dragOverStopId.value = null
}

function clearRemovedStopNotice() {
  if (removedStopTimer !== null) {
    clearTimeout(removedStopTimer)
    removedStopTimer = null
  }

  removedStopNotice.value = null
}

function queueRemovedStopNotice(stop: ItineraryStop, index: number) {
  clearRemovedStopNotice()
  removedStopNotice.value = {
    stop: cloneStop(stop),
    index,
  }

  removedStopTimer = setTimeout(() => {
    removedStopNotice.value = null
    removedStopTimer = null
  }, 5000)
}

function undoRemoveStop() {
  if (!removedStopNotice.value) return

  const nextStops = [...itineraryStops.value]
  nextStops.splice(removedStopNotice.value.index, 0, cloneStop(removedStopNotice.value.stop))
  itineraryStops.value = nextStops.slice(0, maxVisibleStops)
  clearRemovedStopNotice()
}

function regenerateItinerary() {
  emit('navigate', 'ai1')
}

function formatTripListTime(item: TripListItemPayload) {
  const createdAt = item.createdAt ? new Date(item.createdAt) : null
  const dateText = item.date || (createdAt && !Number.isNaN(createdAt.getTime()) ? createdAt.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) : '待定日期')
  const durationText = item.duration || (item.stopCount ? `${item.stopCount}站` : '待生成')
  return `${dateText} · ${durationText}`
}

function formatTripListPreview(item: TripListItemPayload) {
  const route = [item.firstStop, item.lastStop].filter(Boolean).join(' → ')
  const type = item.type || 'AI路线'
  const transport = item.transportMode || '步行优先'
  return route ? `${type} · ${route}` : `${type} · ${transport}`
}

function formatTripListMeta(item: TripListItemPayload) {
  const chunks = [
    item.totalBudget || '',
    item.totalWalkMinutes ? `步行约${Math.round(item.totalWalkMinutes)}分钟` : '',
    item.source?.includes('agent') ? '小薇生成' : '后端方案',
  ].filter(Boolean)

  return chunks.join(' · ')
}

function addSuggestedStop() {
  emit('navigate', 'discover')
}

function startStopDrag(stopId: number, event: DragEvent) {
  if (itineraryStops.value.length < 2) return

  draggingStopId.value = stopId
  dragOverStopId.value = stopId
  event.dataTransfer?.setData('text/plain', String(stopId))

  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function setStopDropTarget(stopId: number) {
  if (draggingStopId.value === null || draggingStopId.value === stopId) return
  dragOverStopId.value = stopId
}

function dropStop(targetStopId: number) {
  if (draggingStopId.value === null || draggingStopId.value === targetStopId) {
    clearStopDragState()
    return
  }

  const nextStops = [...itineraryStops.value]
  const fromIndex = nextStops.findIndex((stop) => stop.id === draggingStopId.value)
  const targetIndex = nextStops.findIndex((stop) => stop.id === targetStopId)

  if (fromIndex === -1 || targetIndex === -1) {
    clearStopDragState()
    return
  }

  const [movedStop] = nextStops.splice(fromIndex, 1)
  nextStops.splice(targetIndex, 0, movedStop)
  itineraryStops.value = nextStops
  clearStopDragState()
}

function removeStop(stopId: number) {
  const index = itineraryStops.value.findIndex((stop) => stop.id === stopId)
  if (index === -1) return

  const nextStops = [...itineraryStops.value]
  const [removedStop] = nextStops.splice(index, 1)
  itineraryStops.value = nextStops
  queueRemovedStopNotice(removedStop, index)

  if (activeSwapStopId.value === stopId) {
    closeSwapOptions()
  }

  if (draggingStopId.value === stopId || dragOverStopId.value === stopId) {
    clearStopDragState()
  }
}

async function applySwapOption(option: LocalSwapOptionView | RemoteSwapOption) {
  const index = itineraryStops.value.findIndex((stop) => stop.id === activeSwapStopId.value)
  if (index === -1) return

  const currentStop = itineraryStops.value[index]

  if (option.kind === 'remote') {
    if (props.trip?.tripId && currentStop.stopId) {
      await replaceTripStop(props.trip.tripId, currentStop.stopId, option.candidateId)
    }

    itineraryStops.value[index] = {
      ...currentStop,
      poiId: option.candidateId.replace(/^alt_/, ''),
      title: option.title,
      tags: option.categoryTags.length ? [...option.categoryTags] : [...currentStop.tags],
      priceRange: parseRemotePriceRange(option.rawPriceRange, currentStop.priceRange),
    }

    closeSwapOptions()
    return
  }

  itineraryStops.value[index] = {
    ...currentStop,
    venueKey: option.venueKey,
    swapGroup: option.swapGroup,
    timeLabel: option.timeLabel,
    durationMinutes: option.durationMinutes,
    title: option.title,
    tags: [...option.tags],
    priceRange: clonePriceRange(option.priceRange),
    routePoint: clonePoint(option.routePoint),
  }

  closeSwapOptions()
}

function openStopDetail(stop: ItineraryStop) {
  emit(
    'viewDetail',
    {
      detail: resolvePlaceDetail({
        title: stop.title,
        tags: stop.tags,
        price: formatStopPrice(stop.priceRange),
      }),
      poiId: stop.poiId ?? null,
      returnScreen: 'itinerary',
    },
  )
}

const itineraryReminders = ref<ReminderItem[]>([
  { id: 'reminder-1', text: '暴晒 25℃', done: false },
  { id: 'reminder-2', text: 'RAC BAR 可能等位', done: false },
  { id: 'reminder-3', text: '已预留缓冲', done: false },
])

const itineraryPackingList = ref<PackingItem[]>([
  { id: 'packing-1', text: '遮阳伞', checked: false },
  { id: 'packing-2', text: '一台傻瓜胶片相机', checked: false },
  { id: 'packing-3', text: '充电宝', checked: false },
])

const itineraryAdjustments = ref<AdjustmentItem[]>([
  { id: 'adjustment-1', label: '更轻松一点', emphasized: false },
  { id: 'adjustment-2', label: '减少步行', emphasized: false },
  { id: 'adjustment-3', label: '避开排队', emphasized: false },
  { id: 'adjustment-4', label: '重新生成', emphasized: true },
])

const reminderDraft = ref('')
const packingDraft = ref('')
const adjustmentDraft = ref('')
const selectedAdjustmentId = ref<string | null>(null)
const itineraryPrompt = ref('今天突然下雨了，不去室外')

watch(
  () => props.trip,
  (trip) => {
    if (!trip) {
      itineraryStops.value = []
      remoteSwapOptions.value = {}
      itineraryReminders.value = []
      itineraryPackingList.value = []
      closeSwapOptions()
      clearStopDragState()
      clearRemovedStopNotice()
      return
    }

    const orderedStops = [...(trip.stops || [])]
      .sort((left, right) => left.index - right.index)
      .slice(0, maxVisibleStops)

    itineraryStops.value = orderedStops.length
      ? orderedStops.map((stop, index) => createStopFromTrip(stop, index))
      : []

    startLocation.value = defaultStartLocation
    endLocation.value = orderedStops.at(-1)?.address || orderedStops.at(-1)?.name || defaultEndLocation
    itineraryReminders.value = buildRemindersFromTrip(trip)
    remoteSwapOptions.value = {}
    itineraryPrompt.value = typeof trip.overview?.request === 'string' && trip.overview.request.trim()
      ? trip.overview.request
      : itineraryPrompt.value

    closeSwapOptions()
    clearStopDragState()
    clearRemovedStopNotice()

    void (async () => {
      const [reminderResult, weatherResult] = await Promise.allSettled([
        getTripReminders(trip.tripId),
        getTripWeather(trip.tripId),
      ])

      if (props.trip?.tripId !== trip.tripId) {
        return
      }

      const remoteReminders = reminderResult.status === 'fulfilled' ? reminderResult.value : null
      const remoteWeather = weatherResult.status === 'fulfilled' ? weatherResult.value : null

      itineraryReminders.value = buildRemindersFromApi(remoteReminders, remoteWeather, trip)

      if (remoteReminders?.packingChecklist?.length) {
        itineraryPackingList.value = buildPackingItems(remoteReminders.packingChecklist)
      }
    })()
  },
  { immediate: true },
)

function addReminder() {
  const text = reminderDraft.value.trim()
  if (!text) return

  itineraryReminders.value.push({
    id: createDynamicId('reminder'),
    text,
    done: false,
  })
  reminderDraft.value = ''
}

function toggleReminder(id: string) {
  const reminder = itineraryReminders.value.find((item) => item.id === id)
  if (!reminder) return

  reminder.done = !reminder.done
}

function removeReminder(id: string) {
  itineraryReminders.value = itineraryReminders.value.filter((item) => item.id !== id)
}

function addPackingItem() {
  const text = packingDraft.value.trim()
  if (!text) return

  itineraryPackingList.value.push({
    id: createDynamicId('packing'),
    text,
    checked: false,
  })
  packingDraft.value = ''
}

function togglePackingItem(id: string) {
  const packingItem = itineraryPackingList.value.find((item) => item.id === id)
  if (!packingItem) return

  packingItem.checked = !packingItem.checked
}

function removePackingItem(id: string) {
  itineraryPackingList.value = itineraryPackingList.value.filter((item) => item.id !== id)
}

function selectAdjustment(item: AdjustmentItem) {
  selectedAdjustmentId.value = selectedAdjustmentId.value === item.id ? null : item.id
  itineraryPrompt.value = item.label
}

function addAdjustment() {
  const label = adjustmentDraft.value.trim()
  if (!label) return

  const nextItem = {
    id: createDynamicId('adjustment'),
    label,
    emphasized: false,
  }

  itineraryAdjustments.value.push(nextItem)
  adjustmentDraft.value = ''
  selectAdjustment(nextItem)
}

function removeAdjustment(id: string) {
  itineraryAdjustments.value = itineraryAdjustments.value.filter((item) => item.id !== id)

  if (selectedAdjustmentId.value === id) {
    selectedAdjustmentId.value = null
  }
}

onMounted(() => {
  scrollRoot.value?.scrollTo({ top: 0 })
})

onBeforeUnmount(() => {
  clearRemovedStopNotice()
})
</script>

<template>
  <div class="itinerary-figma">
    <header class="itinerary-figma-status-bar">
      <div class="itinerary-figma-time">9:41</div>
      <div class="itinerary-figma-island"></div>
      <img :src="levelsAsset" alt="" class="itinerary-figma-levels" />
    </header>

    <section v-if="props.showList" class="itinerary-trip-list-screen">
      <div class="itinerary-trip-list-bg" aria-hidden="true">
        <div class="itinerary-figma-glow itinerary-figma-glow-white"></div>
        <div class="itinerary-figma-glow itinerary-figma-glow-rose"></div>
        <div class="itinerary-figma-glow itinerary-figma-glow-gold"></div>
      </div>

      <div class="itinerary-trip-list-header">
        <div>
          <p class="itinerary-trip-list-kicker">小薇行程</p>
          <h2 class="itinerary-trip-list-title">按时间查看计划</h2>
        </div>
        <button type="button" class="itinerary-trip-list-refresh" :disabled="props.loadingTrips" @click="emit('refreshTrips')">
          {{ props.loadingTrips ? '同步中' : '刷新' }}
        </button>
      </div>

      <div v-if="props.loadingTrips && !hasTripListItems" class="itinerary-trip-list-state">
        正在读取后端行程...
      </div>

      <div v-else-if="hasTripListItems" class="itinerary-trip-list">
        <button
          v-for="item in tripListItems"
          :key="item.tripId"
          type="button"
          class="itinerary-trip-list-item"
          :class="{ 'itinerary-trip-list-item-active': item.tripId === props.trip?.tripId }"
          @click="emit('selectTrip', item.tripId)"
        >
          <span class="itinerary-trip-list-avatar" aria-hidden="true">{{ item.stopCount || 0 }}</span>
          <span class="itinerary-trip-list-main">
            <span class="itinerary-trip-list-row">
              <strong class="itinerary-trip-list-name">{{ item.title || 'AI生成行程' }}</strong>
              <span class="itinerary-trip-list-time">{{ formatTripListTime(item) }}</span>
            </span>
            <span class="itinerary-trip-list-preview">{{ formatTripListPreview(item) }}</span>
            <span class="itinerary-trip-list-meta">{{ formatTripListMeta(item) }}</span>
          </span>
        </button>
      </div>

      <div v-else class="itinerary-trip-list-empty">
        <h3>还没有同步到行程</h3>
        <p>回到小薇聊天，说出时间、预算和想玩的方向；后端 agent 生成路线后会出现在这里。</p>
        <button type="button" class="itinerary-trip-list-primary" @click="emit('navigate', 'ai1')">找小薇规划</button>
      </div>
    </section>

    <div v-else ref="scrollRoot" class="itinerary-figma-scroll" :class="{ 'itinerary-figma-scroll-locked': activeSwapStop !== null }">
      <div class="itinerary-figma-canvas" :style="{ minHeight: hasStops ? '2031px' : '1400px' }">
        <div class="itinerary-figma-background" aria-hidden="true">
          <div class="itinerary-figma-glow itinerary-figma-glow-white"></div>
          <div class="itinerary-figma-glow itinerary-figma-glow-rose"></div>
          <div class="itinerary-figma-glow itinerary-figma-glow-ellipse"></div>
          <div class="itinerary-figma-glow itinerary-figma-glow-gold"></div>
        </div>

        <div class="itinerary-figma-map-stage">
          <ItineraryMap :start-point="startMapPoint" :end-point="endMapPoint" :route-points="mapRoutePoints" />
        </div>

        <button type="button" class="itinerary-figma-back-list" @click="emit('backToList')">返回行程列表</button>

        <section class="itinerary-figma-address-shell">
          <div class="itinerary-figma-address-card">
            <div class="itinerary-figma-address-details">
              <label class="itinerary-figma-address-line itinerary-figma-address-line-muted">
                <img :src="addressStartAsset" alt="" class="itinerary-figma-address-icon itinerary-figma-address-icon-muted" />
                <input
                  v-model="startLocation"
                  type="text"
                  class="itinerary-figma-address-input"
                  aria-label="起始点位置"
                  :placeholder="defaultStartLocation"
                />
              </label>
              <div class="itinerary-figma-address-divider"></div>
              <label class="itinerary-figma-address-line itinerary-figma-address-line-strong">
                <img :src="addressEndAsset" alt="" class="itinerary-figma-address-icon" />
                <input
                  v-model="endLocation"
                  type="text"
                  class="itinerary-figma-address-input"
                  aria-label="终点位置"
                  :placeholder="defaultEndLocation"
                />
              </label>
            </div>
          </div>

          <div class="itinerary-figma-address-actions">
            <button type="button" class="itinerary-figma-address-action" aria-label="恢复默认地点" @click="restoreLocationDefaults">
              <img :src="moreVerticalAsset" alt="" class="itinerary-figma-address-action-icon" />
            </button>
            <button type="button" class="itinerary-figma-address-action" aria-label="交换起终点" @click="swapLocations">
              <img :src="swapAsset" alt="" class="itinerary-figma-address-action-icon" />
            </button>
          </div>
        </section>

        <button type="button" class="itinerary-figma-start-nav" @click="emit('navigate', 'navigation')">
          <img :src="startAsset" alt="" class="itinerary-figma-start-nav-icon" />
          <span>开始导航</span>
        </button>

        <section class="itinerary-figma-summary-card">
          <div
            v-for="(item, index) in itinerarySummaryStats"
            :key="item.label"
            class="itinerary-figma-summary-item"
            :class="{ 'itinerary-figma-summary-item-divider': index < itinerarySummaryStats.length - 1 }"
          >
            <p class="itinerary-figma-summary-label">{{ item.label }}</p>
            <p class="itinerary-figma-summary-value">{{ item.value }}</p>
          </div>
        </section>

        <div class="itinerary-figma-route-point itinerary-figma-route-point-origin">
          <img :src="addressStartAsset" alt="" class="itinerary-figma-route-point-icon" />
          <span class="itinerary-figma-route-point-text">{{ routeOriginLabel }}</span>
        </div>

        <template v-if="hasStops">
          <template v-for="stop in positionedStops" :key="stop.id">
            <div class="itinerary-figma-step-walk" :style="{ top: `${stop.walkTop}px` }">
              <img :src="walkAsset" alt="" class="itinerary-figma-step-walk-icon" />
              <span>{{ stop.walkFromPreviousLabel }}</span>
            </div>

            <div class="itinerary-figma-step-connector" :style="{ top: `${stop.connectorTop}px`, height: `${stop.connectorHeight}px` }"></div>

            <div class="itinerary-figma-step-marker" :style="{ top: `${stop.markerTop}px` }">{{ stop.order }}</div>

            <article
              class="itinerary-figma-stop-card"
              :class="{
                'itinerary-figma-stop-card-draggable': itineraryStops.length > 1,
                'itinerary-figma-stop-card-dragging': stop.id === draggingStopId,
                'itinerary-figma-stop-card-drop-target': stop.id === dragOverStopId && stop.id !== draggingStopId,
              }"
              :style="{ top: `${stop.cardTop}px`, height: `${stop.cardHeight}px` }"
              :draggable="itineraryStops.length > 1"
              @dragstart="startStopDrag(stop.id, $event)"
              @dragenter.prevent="setStopDropTarget(stop.id)"
              @dragover.prevent="setStopDropTarget(stop.id)"
              @drop.prevent="dropStop(stop.id)"
              @dragend="clearStopDragState"
            >
              <div class="itinerary-figma-stop-card-inner">
                <div class="itinerary-figma-stop-header">
                  <p class="itinerary-figma-stop-time">
                    <img :src="clockAsset" alt="" class="itinerary-figma-stop-time-icon" />
                    <span>{{ stop.time }}</span>
                  </p>

                  <div class="itinerary-figma-stop-tools">
                    <button type="button" class="itinerary-figma-stop-tool-dot" :aria-label="`删除第 ${stop.order} 个站点`" @click="removeStop(stop.id)">
                      <span class="itinerary-figma-stop-tool-minus"></span>
                    </button>
                  </div>
                </div>

                <h3 class="itinerary-figma-stop-title" :class="{ 'itinerary-figma-stop-title-wide': stop.titleWide }">{{ stop.title }}</h3>

                <div class="itinerary-figma-stop-meta">
                  <div class="itinerary-figma-stop-tags">
                    <span v-for="tag in stop.tags" :key="tag" class="itinerary-figma-stop-tag">{{ tag }}</span>
                  </div>
                  <p class="itinerary-figma-stop-price">{{ stop.price }}</p>
                </div>

                <div class="itinerary-figma-stop-actions">
                  <button type="button" class="itinerary-figma-detail-btn" @click="openStopDetail(stop)">查看详情</button>
                  <button type="button" class="itinerary-figma-swap-btn" @click="openSwapOptions(stop.id)">换一个</button>
                </div>
              </div>
            </article>
          </template>

          <div v-if="finalWalkTop !== null" class="itinerary-figma-step-walk itinerary-figma-step-walk-final" :style="{ top: `${finalWalkTop}px` }">
            <img :src="walkAsset" alt="" class="itinerary-figma-step-walk-icon" />
            <span>{{ finalWalkLabel }}</span>
          </div>

          <div class="itinerary-figma-lower-content" :style="{ top: `${lowerContentTop}px` }">
            <div class="itinerary-figma-route-point itinerary-figma-route-point-destination">
              <img :src="addressEndAsset" alt="" class="itinerary-figma-route-point-icon" />
              <span class="itinerary-figma-route-point-text">{{ routeDestinationLabel }}</span>
            </div>

          <section class="itinerary-figma-reminder-section">
            <h3 class="itinerary-figma-section-title">出发前提醒</h3>

            <div class="itinerary-figma-reminder-grid">
              <article class="itinerary-figma-reminder-card">
                <h4 class="itinerary-figma-reminder-title">今日提醒</h4>
                <ul class="itinerary-figma-reminder-list">
                  <li
                    v-for="item in itineraryReminders"
                    :key="item.id"
                    :class="{ 'itinerary-figma-reminder-item-done': item.done }"
                  >
                    <button type="button" class="itinerary-figma-reminder-row" @click="toggleReminder(item.id)">
                      <span class="itinerary-figma-reminder-bullet" aria-hidden="true"></span>
                      <span>{{ item.text }}</span>
                    </button>
                    <button type="button" class="itinerary-figma-item-remove" aria-label="删除提醒" @click="removeReminder(item.id)">×</button>
                  </li>
                </ul>

                <form class="itinerary-figma-inline-form" @submit.prevent="addReminder">
                  <input
                    v-model="reminderDraft"
                    type="text"
                    class="itinerary-figma-inline-input"
                    aria-label="新增提醒"
                    placeholder="添加提醒"
                  />
                  <button type="submit" class="itinerary-figma-inline-btn">添加</button>
                </form>
              </article>

              <article class="itinerary-figma-reminder-card">
                <h4 class="itinerary-figma-reminder-title">建议携带</h4>
                <ul class="itinerary-figma-packing-list">
                  <li
                    v-for="item in itineraryPackingList"
                    :key="item.id"
                    :class="{ 'itinerary-figma-packing-item-checked': item.checked }"
                  >
                    <button type="button" class="itinerary-figma-packing-row" @click="togglePackingItem(item.id)">
                      <span class="itinerary-figma-checkbox" :class="{ 'itinerary-figma-checkbox-checked': item.checked }" aria-hidden="true"></span>
                      <span>{{ item.text }}</span>
                    </button>
                    <button type="button" class="itinerary-figma-item-remove" aria-label="删除携带物品" @click="removePackingItem(item.id)">×</button>
                  </li>
                </ul>

                <form class="itinerary-figma-inline-form" @submit.prevent="addPackingItem">
                  <input
                    v-model="packingDraft"
                    type="text"
                    class="itinerary-figma-inline-input"
                    aria-label="新增携带物品"
                    placeholder="添加物品"
                  />
                  <button type="submit" class="itinerary-figma-inline-btn">添加</button>
                </form>
              </article>
            </div>
          </section>

          <section class="itinerary-figma-adjust-section">
            <h3 class="itinerary-figma-section-title">想调整一下？</h3>

            <div class="itinerary-figma-adjust-grid">
              <div v-for="item in itineraryAdjustments" :key="item.id" class="itinerary-figma-adjust-item">
                <button
                  type="button"
                  class="itinerary-figma-adjust-btn"
                  :class="{
                    'itinerary-figma-adjust-btn-emphasis': item.emphasized,
                    'itinerary-figma-adjust-btn-selected': item.id === selectedAdjustmentId,
                  }"
                  @click="selectAdjustment(item)"
                >
                  {{ item.label }}
                </button>
                <button type="button" class="itinerary-figma-adjust-remove" aria-label="删除调整项" @click="removeAdjustment(item.id)">×</button>
              </div>
            </div>

            <form class="itinerary-figma-inline-form itinerary-figma-inline-form-adjust" @submit.prevent="addAdjustment">
              <input
                v-model="adjustmentDraft"
                type="text"
                class="itinerary-figma-inline-input"
                aria-label="新增调整项"
                placeholder="添加新的调整方向"
              />
              <button type="submit" class="itinerary-figma-inline-btn">添加</button>
            </form>
          </section>

            <label class="itinerary-figma-composer">
              <img :src="composerSparkAsset" alt="" class="itinerary-figma-composer-spark" />
              <input
                v-model="itineraryPrompt"
                type="text"
                class="itinerary-figma-composer-input"
                aria-label="输入行程要求"
                placeholder="今天突然下雨了，不去室外"
              />
              <img :src="composerMicAsset" alt="" class="itinerary-figma-composer-mic-icon" />
            </label>
          </div>
        </template>

        <section v-else class="itinerary-figma-empty-state">
          <div class="itinerary-figma-empty-badge">✦</div>
          <h3 class="itinerary-figma-empty-title">还没有生成路线</h3>
          <p class="itinerary-figma-empty-copy">先和小薇说说你的时间、心情、预算或想去的方向，路线会由 AI 生成后同步到这里。</p>

          <div class="itinerary-figma-empty-actions">
            <button type="button" class="itinerary-figma-empty-action itinerary-figma-empty-action-primary" @click="regenerateItinerary">
              去找小薇
            </button>
            <button type="button" class="itinerary-figma-empty-action" @click="addSuggestedStop">发现灵感</button>
          </div>
        </section>

        <footer class="itinerary-figma-home-indicator">
          <div class="itinerary-figma-home-indicator-bar"></div>
        </footer>
      </div>
    </div>

    <nav class="itinerary-figma-nav" aria-label="底部导航">
      <button type="button" class="itinerary-figma-nav-btn" aria-label="个人" @click="emit('navigate', 'profile')">
        <img :src="navProfileAsset" alt="" class="itinerary-figma-nav-icon itinerary-figma-nav-icon-profile" />
      </button>
      <button type="button" class="itinerary-figma-nav-btn" aria-label="发现" @click="emit('navigate', 'discover')">
        <img :src="navSearchAsset" alt="" class="itinerary-figma-nav-icon itinerary-figma-nav-icon-search" />
      </button>
      <button type="button" class="itinerary-figma-nav-btn" aria-label="AI" @click="emit('navigate', 'ai1')">
        <img :src="navAiAsset" alt="" class="itinerary-figma-nav-icon itinerary-figma-nav-icon-ai" />
      </button>
      <button type="button" class="itinerary-figma-nav-btn itinerary-figma-nav-btn-active" aria-label="行程" aria-current="page" @click="emit('navigate', 'itinerary')">
        <img :src="navTripAsset" alt="" class="itinerary-figma-nav-icon itinerary-figma-nav-icon-trip" />
      </button>
      <button type="button" class="itinerary-figma-nav-btn itinerary-figma-nav-btn-chat" aria-label="聊天" @click="emit('navigate', 'chat')">
        <img :src="navChatAsset" alt="" class="itinerary-figma-nav-icon itinerary-figma-nav-icon-chat" />
      </button>
    </nav>

    <Transition name="undo-toast">
      <aside v-if="removedStopNotice" class="itinerary-undo-toast">
        <div class="itinerary-undo-toast-copy">
          <p class="itinerary-undo-toast-title">已删除 {{ removedStopNotice.stop.title }}</p>
          <p class="itinerary-undo-toast-text">5 秒内可撤销</p>
        </div>
        <button type="button" class="itinerary-undo-toast-action" @click="undoRemoveStop">撤销</button>
      </aside>
    </Transition>

    <Transition name="swap-fade">
      <div v-if="activeSwapStop" class="itinerary-swap-backdrop" @click="closeSwapOptions"></div>
    </Transition>

    <Transition name="swap-sheet">
      <section v-if="activeSwapStop" class="itinerary-swap-sheet" @click.stop>
        <div class="itinerary-swap-sheet-handle"></div>

        <div class="itinerary-swap-sheet-header">
          <div class="itinerary-swap-sheet-title-wrap">
            <span class="itinerary-swap-sheet-title-icon" aria-hidden="true">✦</span>
            <h3 class="itinerary-swap-sheet-title">精选备选 | 替换第 {{ activeSwapStopOrder ?? activeSwapStop.id }} 站</h3>
          </div>

          <button type="button" class="itinerary-swap-sheet-close" aria-label="关闭备选方案" @click="closeSwapOptions">
            ×
          </button>
        </div>

        <div v-if="loadingSwapStopId === activeSwapStop?.id" style="padding: 28px 16px 12px; text-align: center; color: #6c6868; font-size: 13px; line-height: 20px;">
          正在获取可替换站点...
        </div>

        <div v-else-if="activeSwapOptions.length === 0" style="padding: 28px 16px 12px; text-align: center; color: #8b2f45; font-size: 13px; line-height: 20px;">
          当前没有可替换的附近站点
        </div>

        <div v-else class="itinerary-swap-sheet-grid">
          <article v-for="option in activeSwapOptions" :key="option.id" class="itinerary-swap-option-card">
            <div class="itinerary-swap-option-head">
              <h4 class="itinerary-swap-option-title">{{ option.title }}</h4>
              <span class="itinerary-swap-option-price">{{ option.priceLabel }}</span>
            </div>

            <p class="itinerary-swap-option-travel">
              <span class="itinerary-swap-option-travel-icon" aria-hidden="true">📍</span>
              <span>{{ option.travelLabel }}</span>
            </p>

            <p class="itinerary-swap-option-summary">{{ option.summary }}</p>

            <button type="button" class="itinerary-swap-option-action" @click="applySwapOption(option)">
              选用此站
            </button>
          </article>
        </div>
      </section>
    </Transition>
  </div>
</template>

<style scoped>
.itinerary-figma {
  position: relative;
  height: 100%;
  overflow: hidden;
  background: #f9f9f9;
}

.itinerary-trip-list-screen {
  position: relative;
  z-index: 2;
  height: 100%;
  padding: 82px 18px 112px;
  overflow-y: auto;
  background: #f4eff3;
}

.itinerary-trip-list-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.itinerary-trip-list-header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.itinerary-trip-list-kicker,
.itinerary-trip-list-title {
  margin: 0;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #000;
}

.itinerary-trip-list-kicker {
  font-size: 13px;
  line-height: 18px;
  opacity: 0.58;
}

.itinerary-trip-list-title {
  margin-top: 4px;
  font-size: 24px;
  line-height: 30px;
}

.itinerary-trip-list-refresh,
.itinerary-trip-list-primary,
.itinerary-figma-back-list {
  border: 0;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  cursor: pointer;
}

.itinerary-trip-list-refresh {
  min-width: 64px;
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: #461c3a;
  font-size: 13px;
}

.itinerary-trip-list {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.itinerary-trip-list-item {
  width: 100%;
  min-height: 86px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid rgba(255, 255, 255, 0.84);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: 0 12px 24px rgba(70, 28, 58, 0.07);
  text-align: left;
  cursor: pointer;
}

.itinerary-trip-list-item-active {
  border-color: rgba(70, 28, 58, 0.26);
  background: rgba(255, 255, 255, 0.92);
}

.itinerary-trip-list-avatar {
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: #461c3a;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
}

.itinerary-trip-list-main {
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 5px;
}

.itinerary-trip-list-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.itinerary-trip-list-name,
.itinerary-trip-list-time,
.itinerary-trip-list-preview,
.itinerary-trip-list-meta,
.itinerary-trip-list-state,
.itinerary-trip-list-empty {
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.itinerary-trip-list-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #000;
  font-size: 15px;
  line-height: 20px;
}

.itinerary-trip-list-time {
  flex: 0 0 auto;
  color: rgba(0, 0, 0, 0.48);
  font-size: 11px;
}

.itinerary-trip-list-preview,
.itinerary-trip-list-meta {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: rgba(0, 0, 0, 0.62);
  font-size: 12px;
  line-height: 17px;
}

.itinerary-trip-list-meta {
  color: rgba(70, 28, 58, 0.74);
}

.itinerary-trip-list-state,
.itinerary-trip-list-empty {
  position: relative;
  z-index: 2;
  margin-top: 80px;
  color: rgba(0, 0, 0, 0.62);
  text-align: center;
  font-size: 14px;
  line-height: 22px;
}

.itinerary-trip-list-empty {
  margin: 90px auto 0;
  width: 310px;
  padding: 22px 20px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.62);
}

.itinerary-trip-list-empty h3 {
  margin: 0 0 8px;
  color: #000;
  font-size: 17px;
}

.itinerary-trip-list-empty p {
  margin: 0;
}

.itinerary-trip-list-primary {
  margin-top: 16px;
  height: 38px;
  padding: 0 18px;
  border-radius: 999px;
  background: #461c3a;
  color: #fff;
  font-size: 13px;
}

.itinerary-figma-back-list {
  position: absolute;
  top: 82px;
  left: 18px;
  z-index: 11;
  height: 34px;
  padding: 0 13px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  color: #461c3a;
  font-size: 12px;
  box-shadow: 0 8px 20px rgba(70, 28, 58, 0.08);
}

.itinerary-figma-scroll {
  position: relative;
  z-index: 2;
  height: 100%;
  overflow-y: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.itinerary-figma-scroll::-webkit-scrollbar {
  display: none;
}

.itinerary-figma-scroll-locked {
  overflow: hidden;
}

.itinerary-figma-canvas {
  position: relative;
  width: 393px;
  min-height: 2031px;
  background: #f4eff3;
  overflow: hidden;
}

.itinerary-figma-background {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: #f4eff3;
}

.itinerary-figma-glow {
  position: absolute;
  border-radius: 999px;
  filter: blur(100px);
  pointer-events: none;
}

.itinerary-figma-glow-white {
  top: 1360px;
  left: 44px;
  width: 220px;
  height: 360px;
  background: rgba(255, 255, 255, 0.9);
  transform: rotate(-67deg) skewX(-45deg) scaleY(0.7);
}

.itinerary-figma-glow-rose {
  top: 744px;
  left: -98px;
  width: 160px;
  height: 520px;
  background: rgba(215, 164, 224, 0.45);
  transform: rotate(-67deg) skewX(-45deg) scaleY(0.7);
}

.itinerary-figma-glow-ellipse {
  top: 812px;
  left: -132px;
  width: 340px;
  height: 860px;
  background: rgba(255, 255, 255, 0.36);
  transform: rotate(74deg) skewX(44deg) scaleY(0.72);
}

.itinerary-figma-glow-gold {
  top: 1710px;
  right: -34px;
  width: 210px;
  height: 360px;
  background: rgba(255, 249, 142, 0.82);
  transform: rotate(114deg) skewX(-45deg) scaleY(0.7);
}

.itinerary-figma-status-bar {
  position: absolute;
  top: -4px;
  left: 0;
  z-index: 20;
  width: 100%;
  height: 54px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.96);
}

.itinerary-figma-time {
  width: 138px;
  text-align: center;
  font-family: 'SF Pro Text', sans-serif;
  font-size: 17px;
  font-weight: 600;
  line-height: 22px;
  letter-spacing: -0.51px;
  color: #000;
}

.itinerary-figma-island {
  width: 104px;
  height: 28px;
  border-radius: 999px;
  background: #2a2a2a;
}

.itinerary-figma-levels {
  width: 143px;
  height: 54px;
  object-fit: contain;
}

.itinerary-figma-map-stage {
  position: absolute;
  top: 55px;
  left: 50%;
  width: 417px;
  height: 551px;
  overflow: hidden;
  background: #ece4e5;
  transform: translateX(-50%);
}

.itinerary-figma-address-shell {
  position: absolute;
  top: 60px;
  left: 16px;
  z-index: 8;
  display: flex;
  gap: 8px;
  width: 361px;
}

.itinerary-figma-address-card {
  width: 297px;
  height: 92px;
  padding: 16px;
  border: 1px solid #f3f3f3;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.05);
}

.itinerary-figma-address-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.itinerary-figma-address-line {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  font-family: 'SF Pro Rounded', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  line-height: 1.7;
  color: #2c2828;
}

.itinerary-figma-address-line-muted {
  opacity: 0.5;
}

.itinerary-figma-address-line-strong {
  font-weight: 500;
}

.itinerary-figma-address-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.itinerary-figma-address-icon-muted {
  opacity: 0.8;
}

.itinerary-figma-address-divider {
  width: 100%;
  height: 1px;
  background: #e8e3e7;
}

.itinerary-figma-address-text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.itinerary-figma-address-input {
  min-width: 0;
  width: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  font: inherit;
  color: inherit;
}

.itinerary-figma-address-input::placeholder {
  color: rgba(44, 40, 40, 0.48);
}

.itinerary-figma-address-input:focus {
  outline: none;
}

.itinerary-figma-address-actions {
  display: flex;
  flex-direction: column;
  width: 56px;
  padding: 2px 8px;
  border: 1px solid #f3f3f3;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.05);
}

.itinerary-figma-address-action {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: #fff;
  cursor: pointer;
}

.itinerary-figma-address-action-icon {
  width: 16px;
  height: 16px;
}

.itinerary-figma-start-nav {
  position: absolute;
  top: 523px;
  left: 278px;
  z-index: 7;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  width: 90px;
  height: 44px;
  padding: 10px 8px;
  border: 1px solid rgba(255, 255, 255, 0.95);
  border-radius: 166px;
  background: rgba(0, 0, 0, 0.72);
  color: #fff;
  font-family: 'SF Pro Rounded', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 13px;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
}

.itinerary-figma-start-nav-icon {
  width: 14px;
  height: 14px;
}

.itinerary-figma-summary-card {
  position: absolute;
  top: 586px;
  left: 18px;
  z-index: 8;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  width: 358px;
  height: 61px;
  padding: 11px 13px 12px 21px;
  border: 1px solid #f3f3f3;
  border-radius: 24px 24px 18px 18px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.36);
}

.itinerary-figma-summary-item {
  position: relative;
  text-align: center;
}

.itinerary-figma-summary-item-divider::after {
  content: '';
  position: absolute;
  top: 6px;
  right: 0;
  width: 1px;
  height: 38px;
  background: #e8e3e7;
}

.itinerary-figma-summary-label,
.itinerary-figma-summary-value {
  margin: 0;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  color: #000;
}

.itinerary-figma-summary-label {
  font-size: 14px;
  line-height: 1.15;
}

.itinerary-figma-summary-value {
  margin-top: 8px;
  font-size: 10px;
  line-height: 1.2;
}

.itinerary-figma-route-point {
  position: relative;
  width: 380px;
  min-height: 30px;
  padding: 7px 14px;
  border: 0.5px solid #000;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.94);
}

.itinerary-figma-route-point-origin {
  position: absolute;
  top: 666px;
  left: 7px;
  z-index: 6;
}

.itinerary-figma-route-point-destination {
  width: 380px;
}

.itinerary-figma-route-point-icon {
  position: absolute;
  top: 50%;
  left: 14px;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.itinerary-figma-route-point-text {
  display: block;
  width: 100%;
  padding: 0 24px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 13px;
  line-height: 1;
  color: #000;
}

.itinerary-figma-step-walk {
  position: absolute;
  left: 30px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 12px;
  line-height: 17.5px;
  color: #000;
}

.itinerary-figma-step-walk-final {
  left: 28px;
}

.itinerary-figma-lower-content {
  position: absolute;
  top: 1346px;
  left: 0;
  z-index: 5;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.itinerary-figma-step-walk-icon {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}

.itinerary-figma-step-connector {
  position: absolute;
  left: 16px;
  z-index: 1;
  width: 1.5px;
  background: linear-gradient(180deg, #9e6c90 0%, #d7bccf 100%);
}

.itinerary-figma-step-marker {
  position: absolute;
  left: 5px;
  z-index: 3;
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1.5px solid rgba(255, 255, 255, 0.9);
  background: #5f3153;
  color: #fff;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 15px;
  line-height: 1;
  box-shadow: 0 0 0 3px rgba(230, 217, 227, 0.6) inset;
}

.itinerary-figma-stop-card {
  position: absolute;
  left: 29px;
  z-index: 4;
  width: 355px;
  border: 0.646px solid #b4b4b4;
  border-radius: 12.929px;
  background: rgba(244, 239, 241, 0.96);
  transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
}

.itinerary-figma-stop-card-draggable {
  cursor: grab;
}

.itinerary-figma-stop-card-dragging {
  opacity: 0.68;
  transform: scale(0.985);
  box-shadow: 0 18px 32px rgba(70, 28, 58, 0.12);
}

.itinerary-figma-stop-card-drop-target {
  box-shadow: 0 0 0 2px rgba(95, 49, 83, 0.22), 0 16px 28px rgba(70, 28, 58, 0.08);
}

.itinerary-figma-stop-card-inner {
  position: relative;
  height: 100%;
  padding: 14px 11px 11px;
}

.itinerary-figma-stop-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.itinerary-figma-stop-time {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 0;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 10px;
  line-height: 1.2;
  color: #000;
}

.itinerary-figma-stop-time-icon {
  width: 10px;
  height: 10px;
  flex-shrink: 0;
}

.itinerary-figma-stop-tools {
  display: flex;
  align-items: center;
  gap: 0;
}

.itinerary-figma-stop-tool-dot {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #5f3153;
  cursor: pointer;
}

.itinerary-figma-stop-tool-minus {
  width: 9px;
  height: 1.6px;
  border-radius: 999px;
  background: #fff;
}

.itinerary-figma-stop-title {
  margin: 12px 0 0;
  max-width: 252px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 16px;
  line-height: 1.2;
  color: #000;
}

.itinerary-figma-stop-title-wide {
  max-width: 268px;
}

.itinerary-figma-stop-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: 11px;
}

.itinerary-figma-stop-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  max-width: 228px;
}

.itinerary-figma-stop-tag {
  min-width: 51px;
  height: 19px;
  padding: 0 10px;
  border: 0.5px solid #b8b8b8;
  border-radius: 28.348px;
  background: #fff;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 10px;
  line-height: 18px;
  color: #000;
  text-align: center;
}

.itinerary-figma-stop-price {
  flex-shrink: 0;
  margin: 0;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 12.57px;
  line-height: 1.2;
  color: #000;
  white-space: nowrap;
}

.itinerary-figma-stop-actions {
  position: absolute;
  left: 11px;
  right: 11px;
  bottom: 11px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.itinerary-figma-detail-btn,
.itinerary-figma-swap-btn {
  width: 81px;
  height: 27px;
  padding: 0;
  border-radius: 4.654px;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 12.96px;
  line-height: 1;
  cursor: pointer;
}

.itinerary-figma-detail-btn {
  border: 0;
  background: #461c3a;
  color: #fff;
}

.itinerary-figma-swap-btn {
  border: 0.54px solid #461c3a;
  background: #e8e3e7;
  color: #000;
}

.itinerary-figma-nav {
  position: absolute;
  box-sizing: border-box;
  top: 765px;
  left: calc(50% - 327px / 2);
  z-index: 18;
  display: flex;
  align-items: flex-start;
  gap: 18px;
  width: 327px;
  height: 54px;
  padding: 3px 7px 3px 8px;
  border: 1px solid rgba(255, 255, 255, 0.92);
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.66);
  backdrop-filter: blur(18px);
}

.itinerary-figma-nav-btn {
  position: relative;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  border: 0;
  border-radius: 1000px;
  background: rgba(0, 0, 0, 0.02);
  cursor: pointer;
}

.itinerary-figma-nav-btn-active {
  background: #000;
}

.itinerary-figma-nav-icon {
  display: block;
  object-fit: contain;
}

.itinerary-figma-nav-icon-profile {
  width: 14.4px;
  height: 14.4px;
}

.itinerary-figma-nav-icon-search,
.itinerary-figma-nav-icon-chat {
  width: 16px;
  height: 16px;
}

.itinerary-figma-nav-icon-ai {
  width: 22px;
  height: 22px;
}

.itinerary-figma-nav-icon-trip {
  width: 12px;
  height: 11.83px;
  filter: brightness(0) invert(1);
}

.itinerary-figma-reminder-section {
  width: 354px;
}

.itinerary-figma-section-title {
  margin: 0 0 10px;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 17px;
  line-height: 20px;
  color: #000;
}

.itinerary-figma-reminder-grid {
  display: grid;
  grid-template-columns: 170px 170px;
  gap: 14px;
}

.itinerary-figma-reminder-card {
  min-height: 158px;
  display: flex;
  flex-direction: column;
  padding: 10px 15px 12px;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.47);
}

.itinerary-figma-reminder-title {
  margin: 0 0 10px;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  line-height: 1.15;
  color: #000;
}

.itinerary-figma-reminder-list,
.itinerary-figma-packing-list {
  list-style: none;
  margin: 0;
  padding: 0;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 12px;
  line-height: 17px;
  color: #000;
}

.itinerary-figma-reminder-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 31px;
}

.itinerary-figma-packing-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 31px;
}

.itinerary-figma-reminder-row,
.itinerary-figma-packing-row {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.itinerary-figma-reminder-bullet {
  width: 7px;
  height: 7px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #5f3153;
}

.itinerary-figma-checkbox {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 11px;
  height: 11px;
  border: 0.8px solid #ababab;
  border-radius: 2px;
  background: transparent;
  flex-shrink: 0;
}

.itinerary-figma-checkbox-checked {
  border-color: #5f3153;
  background: #5f3153;
}

.itinerary-figma-checkbox-checked::after {
  content: '';
  width: 5px;
  height: 3px;
  border-left: 1.5px solid #fff;
  border-bottom: 1.5px solid #fff;
  transform: rotate(-45deg) translateY(-1px);
}

.itinerary-figma-reminder-item-done .itinerary-figma-reminder-row span:last-child,
.itinerary-figma-packing-item-checked .itinerary-figma-packing-row span:last-child {
  color: #7f7f7f;
  text-decoration: line-through;
}

.itinerary-figma-item-remove {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(95, 49, 83, 0.12);
  color: #5f3153;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
}

.itinerary-figma-inline-form {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
  padding-top: 10px;
}

.itinerary-figma-inline-input {
  flex: 1;
  min-width: 0;
  height: 32px;
  padding: 0 12px;
  border: 1px solid rgba(95, 49, 83, 0.14);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.78);
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 12px;
  color: #2c2828;
}

.itinerary-figma-inline-input::placeholder {
  color: #9b9499;
}

.itinerary-figma-inline-input:focus {
  outline: none;
  border-color: rgba(95, 49, 83, 0.4);
}

.itinerary-figma-inline-btn {
  height: 32px;
  flex-shrink: 0;
  padding: 0 12px;
  border: 0;
  border-radius: 16px;
  background: #5f3153;
  color: #fff;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 12px;
  cursor: pointer;
}

.itinerary-figma-adjust-section {
  width: 354px;
}

.itinerary-figma-adjust-grid {
  display: grid;
  grid-template-columns: repeat(2, 175px);
  gap: 4px 4px;
}

.itinerary-figma-adjust-item {
  position: relative;
}

.itinerary-figma-adjust-btn {
  width: 100%;
  height: 35px;
  padding: 0 28px 0 14px;
  border: 1px solid #c5c5c5;
  border-radius: 52px;
  background: #fff;
  color: #404040;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  line-height: 16px;
  cursor: pointer;
}

.itinerary-figma-adjust-btn-emphasis {
  border-color: #461c3a;
  background: #e8e3e7;
  color: #000;
}

.itinerary-figma-adjust-btn-selected {
  border-color: #461c3a;
  box-shadow: inset 0 0 0 1px rgba(70, 28, 58, 0.14);
}

.itinerary-figma-adjust-remove {
  position: absolute;
  top: 50%;
  right: 8px;
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: #7b5471;
  font-size: 13px;
  line-height: 1;
  transform: translateY(-50%);
  cursor: pointer;
}

.itinerary-figma-inline-form-adjust {
  margin-top: 10px;
}

.itinerary-figma-composer {
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 357px;
  height: 47px;
  padding: 0 13px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 50px;
  background: rgba(255, 255, 255, 0.66);
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}

.itinerary-figma-composer-spark {
  width: 23px;
  height: 23px;
  display: block;
  flex-shrink: 0;
}

.itinerary-figma-composer-input {
  flex: 1;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  outline: none;
  font-family: inherit;
  font-size: 15px;
  line-height: normal;
  color: #000;
}

.itinerary-figma-composer-input::placeholder {
  color: #8f8f8f;
}

.itinerary-figma-composer-input:focus {
  outline: none;
}

.itinerary-figma-composer-mic-icon {
  width: 16.1px;
  height: 22.597px;
  display: block;
  flex-shrink: 0;
}

.itinerary-figma-empty-state {
  position: absolute;
  top: 711px;
  left: 20px;
  z-index: 6;
  width: 353px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 34px 22px 24px;
  border: 1px solid rgba(255, 255, 255, 0.92);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.68);
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 36px rgba(70, 28, 58, 0.08);
  text-align: center;
}

.itinerary-figma-empty-badge {
  display: grid;
  place-items: center;
  width: 54px;
  height: 54px;
  border-radius: 18px;
  background: linear-gradient(135deg, #5f3153 0%, #875776 100%);
  color: #fff;
  font-size: 22px;
  line-height: 1;
  box-shadow: 0 10px 24px rgba(95, 49, 83, 0.24);
}

.itinerary-figma-empty-title {
  margin: 18px 0 0;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 24px;
  line-height: 1.2;
  color: #22181f;
}

.itinerary-figma-empty-copy {
  margin: 10px 0 0;
  max-width: 248px;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(34, 24, 31, 0.72);
}

.itinerary-figma-empty-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
  margin-top: 22px;
}

.itinerary-figma-empty-action {
  width: 100%;
  height: 42px;
  padding: 0 14px;
  border: 1px solid rgba(95, 49, 83, 0.16);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  color: #39222f;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  cursor: pointer;
}

.itinerary-figma-empty-action-primary {
  border-color: #4a1e43;
  background: #4a1e43;
  color: #fff;
}

.itinerary-figma-empty-action-wide {
  grid-column: 1 / -1;
}

.itinerary-figma-home-indicator {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 8px;
  display: flex;
  justify-content: center;
}

.itinerary-figma-home-indicator-bar {
  width: 144px;
  height: 5px;
  border-radius: 100px;
  background: #2a2a2a;
}

.itinerary-swap-backdrop {
  position: absolute;
  inset: 0;
  z-index: 28;
  background: rgba(24, 18, 23, 0.12);
  backdrop-filter: blur(4px);
}

.itinerary-undo-toast {
  position: absolute;
  left: 20px;
  right: 20px;
  bottom: 96px;
  z-index: 30;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 20px;
  background: rgba(35, 24, 32, 0.94);
  color: #fff;
  box-shadow: 0 14px 30px rgba(20, 10, 18, 0.24);
  backdrop-filter: blur(14px);
}

.itinerary-undo-toast-copy {
  min-width: 0;
}

.itinerary-undo-toast-title,
.itinerary-undo-toast-text {
  margin: 0;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.itinerary-undo-toast-title {
  font-size: 14px;
  line-height: 1.3;
}

.itinerary-undo-toast-text {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.3;
  color: rgba(255, 255, 255, 0.74);
}

.itinerary-undo-toast-action {
  flex-shrink: 0;
  height: 34px;
  padding: 0 16px;
  border: 0;
  border-radius: 999px;
  background: #fff;
  color: #39222f;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 13px;
  cursor: pointer;
}

.itinerary-swap-sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 29;
  padding: 8px 11px 16px;
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 -8px 30px rgba(0, 0, 0, 0.08);
  transform-origin: bottom center;
  will-change: transform, opacity;
}

.itinerary-swap-sheet-handle {
  width: 40px;
  height: 5px;
  margin: 0 auto 14px;
  border-radius: 100px;
  background: #dedede;
}

.itinerary-swap-sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.itinerary-swap-sheet-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.itinerary-swap-sheet-title-icon {
  color: #8f8f8f;
  font-size: 16px;
  line-height: 1;
}

.itinerary-swap-sheet-title {
  margin: 0;
  font-size: 16px;
  line-height: 1.4;
  font-weight: 600;
  color: #6f6f6f;
}

.itinerary-swap-sheet-close {
  width: 32px;
  height: 32px;
  border: 1px solid #ececec;
  border-radius: 50%;
  background: #fff;
  color: #7a7a7a;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
}

.itinerary-swap-sheet-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.itinerary-swap-option-card {
  position: relative;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 131px;
  padding: 10px 11px 0;
  border: 0;
  border-radius: 16px;
  background: #fff;
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(25, 16, 24, 0.08);
  will-change: transform, opacity;
}

.itinerary-swap-option-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 6px;
  min-height: 29px;
}

.itinerary-swap-option-title {
  margin: 0;
  flex: 1;
  min-width: 0;
  max-width: calc(100% - 66px);
  overflow: hidden;
  color: #000;
  font-size: 13px;
  line-height: 17px;
  font-weight: 400;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  line-clamp: 2;
  -webkit-line-clamp: 2;
}

.itinerary-swap-option-price {
  flex: none;
  width: 60px;
  height: 23px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  background: rgba(214, 197, 249, 0.5);
  color: #51373f;
  font-size: 10px;
  line-height: 13px;
}

.itinerary-swap-option-travel {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 8px 0 0;
  font-size: 10px;
  line-height: 13px;
  color: #000;
}

.itinerary-swap-option-travel-icon {
  flex: none;
  font-size: 9px;
  line-height: 17px;
}

.itinerary-swap-option-summary {
  display: flex;
  align-items: center;
  min-height: 21px;
  margin: 8px 0 0;
  padding: 4px 5px;
  border-radius: 5px;
  background: #efefef;
  color: #000;
  font-size: 9px;
  line-height: 13px;
  overflow: hidden;
}

.itinerary-swap-option-action {
  margin-top: auto;
  width: calc(100% + 22px);
  height: 28px;
  margin-left: -11px;
  border: 0;
  background: #4a1e43;
  color: #fff;
  border-radius: 0 0 16px 16px;
  font-size: 10px;
  line-height: 13px;
  cursor: pointer;
}

.swap-fade-enter-active,
.swap-fade-leave-active {
  transition: opacity 220ms ease;
}

.swap-fade-enter-from,
.swap-fade-leave-to {
  opacity: 0;
}

.swap-sheet-enter-active {
  transition: transform 320ms cubic-bezier(0.22, 1, 0.36, 1), opacity 240ms ease;
}

.swap-sheet-leave-active {
  transition: transform 220ms ease, opacity 180ms ease;
}

.swap-sheet-enter-from,
.swap-sheet-leave-to {
  transform: translateY(32px) scale(0.98);
  opacity: 0;
}

.swap-sheet-enter-active .itinerary-swap-option-card,
.swap-sheet-leave-active .itinerary-swap-option-card {
  transition: transform 260ms cubic-bezier(0.22, 1, 0.36, 1), opacity 180ms ease;
}

.swap-sheet-enter-from .itinerary-swap-option-card,
.swap-sheet-leave-to .itinerary-swap-option-card {
  transform: translateY(18px);
  opacity: 0;
}

.swap-sheet-enter-active .itinerary-swap-option-card:nth-child(2),
.swap-sheet-leave-active .itinerary-swap-option-card:nth-child(2) {
  transition-delay: 50ms;
}

.undo-toast-enter-active,
.undo-toast-leave-active {
  transition: transform 220ms ease, opacity 180ms ease;
}

.undo-toast-enter-from,
.undo-toast-leave-to {
  transform: translateY(14px);
  opacity: 0;
}
</style>
