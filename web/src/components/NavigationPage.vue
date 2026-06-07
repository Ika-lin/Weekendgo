<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const emit = defineEmits<{
  back: []
}>()

const levelsAsset = '/Levels.svg'
const destinationLabel = '上海市徐汇区上海图书馆地铁站'

const mapContainer = ref<HTMLElement | null>(null)
const map = ref<L.Map | null>(null)

const currentLocation: [number, number] = [31.1916, 121.4422]
const destinationLocation: [number, number] = [31.1945, 121.4438]

onMounted(() => {
  if (!mapContainer.value) return

  const leafletMap = L.map(mapContainer.value, {
    zoomControl: false,
    attributionControl: false,
    dragging: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    boxZoom: false,
    keyboard: false,
    touchZoom: false,
  }).setView([31.1931, 121.4401], 16)

  map.value = leafletMap

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    className: 'navigation-map-tile',
  }).addTo(leafletMap)

  const destinationIcon = L.divIcon({
    className: 'navigation-marker-shell',
    html: '<div class="navigation-destination-marker"><img src="/MapPin.svg" alt="" /></div>',
    iconSize: [40, 40],
    iconAnchor: [20, 36],
  })

  const currentIcon = L.divIcon({
    className: 'navigation-marker-shell',
    html: `
      <div class="navigation-current-marker-wrap">
        <div class="navigation-current-marker-rotate">
          <div class="navigation-current-marker">
            <img src="/Start Icon.svg" alt="" />
          </div>
        </div>
      </div>
    `,
    iconSize: [48, 48],
    iconAnchor: [24, 24],
  })

  L.marker(destinationLocation, { icon: destinationIcon, interactive: false }).addTo(leafletMap)
  L.marker(currentLocation, { icon: currentIcon, interactive: false }).addTo(leafletMap)

  leafletMap.fitBounds(L.latLngBounds([currentLocation, destinationLocation]).pad(0.65), {
    paddingTopLeft: [24, 150],
    paddingBottomRight: [24, 180],
  })
})

onBeforeUnmount(() => {
  map.value?.remove()
  map.value = null
})
</script>

<template>
  <div class="navigation-page">
    <div class="navigation-page-top-glow" aria-hidden="true"></div>

    <div ref="mapContainer" class="navigation-map"></div>

    <header class="navigation-status-bar">
      <div class="navigation-time">9:41</div>
      <div class="navigation-island"></div>
      <img :src="levelsAsset" alt="" class="navigation-levels" />
    </header>

    <section class="navigation-info-card">
      <div class="navigation-info-icon-box">
        <img src="/ArrowBendUpLeft.svg" alt="" />
      </div>

      <div class="navigation-info-copy">
        <p class="navigation-info-caption">目的地在您的左侧</p>
        <p class="navigation-info-distance">0m</p>
      </div>

      <button type="button" class="navigation-info-icon-box navigation-info-icon-box-muted" aria-label="静音导航">
        <img src="/volume-x.svg" alt="" />
      </button>
    </section>

    <section class="navigation-arrival-sheet">
      <div class="navigation-arrival-handle"></div>

      <div class="navigation-arrival-row">
        <button type="button" class="navigation-arrival-btn" aria-label="关闭导航" @click="emit('back')">
          <img src="/iconamoon_close-light.svg" alt="" />
        </button>

        <div class="navigation-arrival-copy">
          <h2 class="navigation-arrival-title">已到达目的地</h2>

          <div class="navigation-arrival-address-row">
            <span class="navigation-arrival-address-icon">
              <img src="/CastleTurret.svg" alt="" />
            </span>
            <p class="navigation-arrival-address">{{ destinationLabel }}</p>
          </div>
        </div>

        <div class="navigation-arrival-btn navigation-arrival-btn-next" aria-hidden="true">
          <img src="/icon-park-outline_left.svg" alt="" />
        </div>
      </div>

      <footer class="navigation-home-indicator">
        <div class="navigation-home-indicator-bar"></div>
      </footer>
    </section>
  </div>
</template>

<style scoped>
.navigation-page {
  position: relative;
  height: 100%;
  overflow: hidden;
  background: #f9f9f9;
}

.navigation-page-top-glow {
  position: absolute;
  left: 50%;
  top: -204px;
  z-index: 0;
  width: 808px;
  height: 420px;
  border-radius: 50%;
  transform: translateX(-50%);
  background: radial-gradient(circle at center, rgba(246, 246, 246, 0.96) 0%, rgba(246, 246, 246, 0.5) 38%, rgba(246, 246, 246, 0) 74%);
}

.navigation-map {
  position: absolute;
  inset: 0;
  z-index: 1;
  background: #eef0f1;
}

.navigation-status-bar {
  position: absolute;
  left: 0;
  top: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 54px;
}

.navigation-time {
  width: 138px;
  text-align: center;
  color: #111;
  font-size: 17px;
  line-height: 22px;
  font-weight: 600;
  letter-spacing: -0.51px;
}

.navigation-island {
  width: 104px;
  height: 28px;
  border-radius: 999px;
  background: #2c2828;
}

.navigation-levels {
  width: 143px;
  height: 54px;
  object-fit: contain;
}

.navigation-info-card {
  position: absolute;
  top: 58px;
  left: 16px;
  right: 16px;
  z-index: 6;
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 12px;
  padding: 8px;
  border-radius: 24px;
  background: #fff;
  box-shadow:
    0 57px 16px rgba(70, 68, 68, 0),
    0 37px 15px rgba(70, 68, 68, 0.01),
    0 21px 12px rgba(70, 68, 68, 0.05),
    0 9px 9px rgba(70, 68, 68, 0.09),
    0 2px 5px rgba(70, 68, 68, 0.1);
}

.navigation-info-icon-box {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  background: #f7f7f7;
  flex-shrink: 0;
}

.navigation-info-icon-box-muted {
  background: #fff;
  border-color: #f3f3f3;
}

.navigation-info-icon-box img {
  width: 24px;
  height: 24px;
}

.navigation-info-copy {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.navigation-info-caption,
.navigation-info-distance,
.navigation-arrival-title,
.navigation-arrival-address {
  margin: 0;
}

.navigation-info-caption {
  color: #999;
  font-size: 12px;
  line-height: 18px;
  font-weight: 400;
}

.navigation-info-distance {
  color: #2c2828;
  font-size: 28px;
  line-height: 36px;
  font-weight: 500;
}

.navigation-arrival-sheet {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 6;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 8px 16px 0;
  border-top-left-radius: 24px;
  border-top-right-radius: 24px;
  background: #fff;
  box-shadow: 0 1px 10px rgba(0, 0, 0, 0.05);
}

.navigation-arrival-handle {
  width: 40px;
  height: 5px;
  border-radius: 100px;
  background: #dedede;
}

.navigation-arrival-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.navigation-arrival-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #f3f3f3;
  border-radius: 999px;
  background: #fff;
  flex-shrink: 0;
}

.navigation-arrival-btn img {
  width: 16px;
  height: 16px;
}

.navigation-arrival-btn-next img {
  transform: rotate(90deg);
}

.navigation-arrival-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.navigation-arrival-title {
  color: #2c2828;
  font-size: 20px;
  line-height: 28px;
  font-weight: 500;
}

.navigation-arrival-address-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.navigation-arrival-address-icon {
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #f3f3f3;
}

.navigation-arrival-address-icon img {
  width: 12px;
  height: 12px;
}

.navigation-arrival-address {
  color: #2c2828;
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
}

.navigation-home-indicator {
  width: calc(100% + 32px);
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.navigation-home-indicator-bar {
  width: 144px;
  height: 5px;
  border-radius: 100px;
  background: #2c2828;
}

:deep(.leaflet-container) {
  width: 100%;
  height: 100%;
  font-family: 'SF Pro Rounded', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #eef0f1 !important;
}

:deep(.navigation-map-tile) {
  filter: saturate(0.78) brightness(1.06) contrast(0.94);
}

:deep(.leaflet-control-container),
:deep(.leaflet-top),
:deep(.leaflet-bottom) {
  display: none;
}

:deep(.navigation-marker-shell) {
  background: transparent;
  border: 0;
}

:deep(.navigation-destination-marker) {
  width: 40px;
  height: 40px;
}

:deep(.navigation-destination-marker img) {
  width: 40px;
  height: 40px;
  display: block;
}

:deep(.navigation-current-marker-wrap) {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.navigation-current-marker-rotate) {
  transform: rotate(-104.55deg);
}

:deep(.navigation-current-marker) {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3.333px solid #fff;
  border-radius: 333px;
  background: #000;
  box-shadow: 0 0 16.667px rgba(0, 0, 0, 0.25);
}

:deep(.navigation-current-marker img) {
  width: 20px;
  height: 20px;
  display: block;
}
</style>