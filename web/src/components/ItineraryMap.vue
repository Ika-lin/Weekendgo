<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { RoutePoint } from '../data/itineraryRoute'

const props = defineProps<{
  startPoint: RoutePoint
  endPoint: RoutePoint
  routePoints: RoutePoint[]
}>()

const mapBackgroundAsset = '/itinerary-map-bg.png'
const startMarkerAsset = '/Start Icon.svg'
const endMarkerAsset = '/MapPin.svg'
const amapKey = import.meta.env.VITE_AMAP_KEY as string | undefined
const amapSecurityCode = import.meta.env.VITE_AMAP_SECURITY_CODE as string | undefined

type AMapNamespace = any
type AMapMap = any
type AMapOverlay = any

const mapContainerRef = ref<HTMLElement | null>(null)
const liveMapStatus = ref<'idle' | 'loading' | 'ready' | 'failed'>('idle')

let AMapRuntime: AMapNamespace | null = null
let liveMap: AMapMap | null = null
let routeLine: AMapOverlay | null = null
let trafficLayer: AMapOverlay | null = null
let mapOverlays: AMapOverlay[] = []

const hasRoute = computed(() => props.routePoints.length > 1)
const canUseLiveMap = computed(() => Boolean(amapKey))

const routePolylinePoints = computed(() => props.routePoints.map((point) => `${point.x},${point.y}`).join(' '))

const startMarkerStyle = computed(() => ({
  left: `${props.startPoint.x - 20}px`,
  top: `${props.startPoint.y - 20}px`,
}))

const endMarkerStyle = computed(() => ({
  left: `${props.endPoint.x - 20}px`,
  top: `${props.endPoint.y - 40}px`,
}))

const liveMapStatusText = computed(() => {
  if (!canUseLiveMap.value) return '未配置高德地图 Key，展示路线草图'
  if (liveMapStatus.value === 'loading') return '正在加载实时地图'
  if (liveMapStatus.value === 'failed') return '实时地图暂不可用，展示路线草图'
  return '高德实时底图'
})

function toLngLat(point: RoutePoint): [number, number] {
  const lngMin = 121.4322
  const lngMax = 121.4555
  const latMin = 31.1965
  const latMax = 31.2226

  return [
    Number((lngMin + (point.x / 417) * (lngMax - lngMin)).toFixed(6)),
    Number((latMax - (point.y / 551) * (latMax - latMin)).toFixed(6)),
  ]
}

function getOrderedRoutePoints() {
  if (props.routePoints.length > 1) return props.routePoints
  return [props.startPoint, props.endPoint]
}

function clearLiveMapRoute() {
  if (!liveMap) return

  const overlays = [...mapOverlays]
  if (routeLine) overlays.push(routeLine)

  if (overlays.length) {
    liveMap.remove(overlays)
  }

  mapOverlays = []
  routeLine = null
}

function renderLiveMapRoute() {
  if (!liveMap || !AMapRuntime) return

  clearLiveMapRoute()

  const routePoints = getOrderedRoutePoints()
  const lngLats = routePoints.map(toLngLat)

  routeLine = new AMapRuntime.Polyline({
    path: lngLats,
    strokeColor: '#5f3153',
    strokeOpacity: 0.9,
    strokeWeight: 7,
    lineJoin: 'round',
    lineCap: 'round',
    zIndex: 60,
  })

  const markers = lngLats.map((lngLat, index) => {
    const isStart = index === 0
    const isEnd = index === lngLats.length - 1
    const label = isStart ? '起' : isEnd ? '终' : String(index)

    return new AMapRuntime.Marker({
      position: lngLat,
      title: isStart ? '起点' : isEnd ? '终点' : `第 ${index} 站`,
      content: `<div class="amap-route-marker ${isStart ? 'amap-route-marker-start' : isEnd ? 'amap-route-marker-end' : ''}">${label}</div>`,
      offset: new AMapRuntime.Pixel(-15, -15),
      zIndex: isStart || isEnd ? 90 : 80,
    })
  })

  mapOverlays = markers
  liveMap.add([routeLine, ...markers])
  liveMap.setFitView([routeLine, ...markers], false, [36, 36, 36, 36])
}

async function initLiveMap() {
  if (!canUseLiveMap.value || !mapContainerRef.value || liveMap) return

  liveMapStatus.value = 'loading'

  try {
    if (amapSecurityCode) {
      window._AMapSecurityConfig = {
        securityJsCode: amapSecurityCode,
      }
    }

    const { default: AMapLoader } = await import('@amap/amap-jsapi-loader')
    AMapRuntime = await AMapLoader.load({
      key: amapKey || '',
      version: '2.0',
      plugins: ['AMap.Scale', 'AMap.ToolBar'],
    })

    liveMap = new AMapRuntime.Map(mapContainerRef.value, {
      center: toLngLat(props.startPoint),
      zoom: 15,
      viewMode: '2D',
      resizeEnable: true,
      mapStyle: 'amap://styles/normal',
    })

    liveMap.addControl(new AMapRuntime.Scale())
    liveMap.addControl(new AMapRuntime.ToolBar({ position: 'RB' }))

    try {
      trafficLayer = new AMapRuntime.TileLayer.Traffic({
        zIndex: 12,
        autoRefresh: true,
        interval: 180,
      })
      liveMap.add(trafficLayer)
    } catch {
      trafficLayer = null
    }

    liveMapStatus.value = 'ready'
    renderLiveMapRoute()
  } catch {
    liveMapStatus.value = 'failed'
  }
}

onMounted(async () => {
  await nextTick()
  void initLiveMap()
})

watch(
  () => [props.startPoint, props.endPoint, props.routePoints],
  () => {
    if (liveMapStatus.value === 'ready') {
      renderLiveMapRoute()
    }
  },
  { deep: true },
)

onBeforeUnmount(() => {
  if (liveMap) {
    clearLiveMapRoute()
    if (trafficLayer) {
      liveMap.remove(trafficLayer)
    }
    liveMap.destroy()
  }

  liveMap = null
  routeLine = null
  trafficLayer = null
  mapOverlays = []
})
</script>

<script lang="ts">
declare global {
  interface Window {
    _AMapSecurityConfig?: {
      securityJsCode: string
    }
  }
}
</script>

<template>
  <div class="itinerary-map-wrapper">
    <img :src="mapBackgroundAsset" alt="" class="itinerary-map-background" aria-hidden="true" />

    <div
      ref="mapContainerRef"
      class="itinerary-live-map"
      :class="{ 'itinerary-live-map-ready': liveMapStatus === 'ready' }"
      aria-label="实时路线地图"
    ></div>

    <svg
      v-if="liveMapStatus !== 'ready'"
      class="itinerary-map-route-layer"
      viewBox="0 0 417 551"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <polyline v-if="hasRoute" :points="routePolylinePoints" class="itinerary-map-route-shadow" />
      <polyline v-if="hasRoute" :points="routePolylinePoints" class="itinerary-map-route" />
    </svg>

    <div v-if="liveMapStatus !== 'ready'" class="itinerary-map-start-marker" :style="startMarkerStyle" aria-hidden="true">
      <img :src="startMarkerAsset" alt="" class="itinerary-map-start-icon" />
    </div>

    <img
      v-if="liveMapStatus !== 'ready'"
      :src="endMarkerAsset"
      alt=""
      class="itinerary-map-end-marker"
      :style="endMarkerStyle"
      aria-hidden="true"
    />

    <div class="itinerary-map-live-badge" :class="{ active: liveMapStatus === 'ready' }">
      {{ liveMapStatusText }}
    </div>
  </div>
</template>

<style scoped>
.itinerary-map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #ece4e5;
}

.itinerary-map-background {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.itinerary-live-map {
  position: absolute;
  inset: 0;
  z-index: 3;
  opacity: 0;
  transition: opacity 240ms ease;
}

.itinerary-live-map-ready {
  opacity: 1;
}

.itinerary-map-route-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.itinerary-map-route-shadow {
  fill: none;
  stroke: rgba(95, 49, 83, 0.16);
  stroke-width: 18px;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.itinerary-map-route {
  fill: none;
  stroke: #5f3153;
  stroke-width: 9px;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: 0.88;
}

.itinerary-map-start-marker {
  position: absolute;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid #fff;
  border-radius: 50%;
  background: #000;
  box-shadow: 0 0 16px rgba(0, 0, 0, 0.25);
}

.itinerary-map-start-icon {
  width: 14px;
  height: 14px;
  display: block;
}

.itinerary-map-end-marker {
  position: absolute;
  width: 40px;
  height: 40px;
  display: block;
}

.itinerary-map-live-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 8;
  max-width: calc(100% - 24px);
  padding: 7px 10px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: #5f3153;
  font-size: 11px;
  line-height: 15px;
  font-weight: 800;
  box-shadow: 0 8px 18px rgba(95, 49, 83, 0.12);
  backdrop-filter: blur(12px);
}

.itinerary-map-live-badge.active {
  color: #165a3f;
}

:global(.amap-route-marker) {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 3px solid #fff;
  border-radius: 50%;
  background: #5f3153;
  color: #fff;
  font-size: 12px;
  line-height: 1;
  font-weight: 900;
  box-shadow: 0 8px 18px rgba(95, 49, 83, 0.26);
}

:global(.amap-route-marker-start) {
  background: #111;
}

:global(.amap-route-marker-end) {
  background: #f04f7b;
}
</style>
