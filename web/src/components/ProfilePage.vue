<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, useTemplateRef, watch } from 'vue'
import { getUserFootprints, getUserProfile, type UserProfilePayload } from '../api'

type Screen = 'discover' | 'ai1' | 'itinerary' | 'chat' | 'settings'

type SettingsMenuItem = {
  label: string
  screen?: Extract<Screen, 'settings'>
}

const emit = defineEmits<{
  navigate: [screen: Screen]
  back: []
}>()

const props = withDefaults(defineProps<{
  userId?: string
}>(), {
  userId: 'u_demo_001',
})

const levelsAsset = '/Levels.svg'
const avatarAsset = '/User Profile.png'
const backAsset = '/icon-park-outline_left-1.svg'
const settingsAsset = '/settings.svg'
const userAsset = '/user.svg'
const searchAsset = '/MagnifyingGlass.svg'
const aiAsset = '/Icon-3.svg'
const tripAsset = '/lucide_map.svg'
const chatAsset = '/ChatTeardrop-dark.svg'
const settingsMenuItems: SettingsMenuItem[] = [
  { label: '设置', screen: 'settings' },
  { label: '主页编辑' },
  { label: '历史发帖' },
]

const isSettingsMenuOpen = ref(false)
const settingsButton = useTemplateRef<HTMLButtonElement>('settingsButton')
const settingsMenu = useTemplateRef<HTMLDivElement>('settingsMenu')
const profileData = ref<UserProfilePayload | null>(null)
const footprints = ref<Array<{ title: string; meta: string }>>([])
const footprintTotal = ref<number | null>(null)
const isLoading = ref(false)
const loadError = ref('')

const stats = computed(() => {
  const remoteStats = profileData.value?.stats
  if (!remoteStats) {
    return [
      { label: '收藏', value: isLoading.value ? '...' : '0' },
      { label: '去过', value: isLoading.value ? '...' : '0' },
      { label: '足迹', value: isLoading.value ? '...' : '0' },
    ]
  }

  return [
    { label: '收藏', value: String(remoteStats.favorites ?? 0) },
    { label: '去过', value: String(remoteStats.completedTrips ?? 0) },
    { label: '足迹', value: String(footprintTotal.value ?? remoteStats.footprints ?? 0) },
  ]
})

function inferPreferenceKey(label: string) {
  if (/拍|照|摄影/.test(label)) return 'camera'
  if (/书|阅读|文字/.test(label)) return 'book'
  if (/展|艺术|美术/.test(label)) return 'gallery'
  return 'food'
}

const preferences = computed(() => {
  const labels = [
    ...(profileData.value?.personaTags || []),
    ...(profileData.value?.favoriteTags || []),
    ...((profileData.value?.favoriteCategories || []).map((item) => item.category)),
  ]

  const uniqueLabels = Array.from(new Set(labels.filter(Boolean))).slice(0, 4)

  return uniqueLabels.map((label) => ({
    key: inferPreferenceKey(label),
    label,
  }))
})

const recentTrails = computed(() => {
  return footprints.value
})

const displayName = computed(() => profileData.value?.nickname || '探索者小李')
const displayMotto = computed(() => profileData.value?.personaSummary || '让生活在慢节奏中开花')
const displayAvatar = computed(() => profileData.value?.avatar || avatarAsset)

async function loadProfileData() {
  isLoading.value = true
  loadError.value = ''

  try {
    const [profile, userFootprints] = await Promise.all([
      getUserProfile(props.userId),
      getUserFootprints(props.userId),
    ])

    profileData.value = profile
    footprintTotal.value = userFootprints.total ?? userFootprints.footprints?.length ?? 0
    footprints.value = (userFootprints.footprints || []).slice(0, 3).map((item) => ({
      title: item.poiName || item.category || '最近足迹',
      meta: [item.date, item.locationContext || item.category].filter(Boolean).join(' · '),
    }))
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '个人页数据加载失败'
  } finally {
    isLoading.value = false
  }
}

function toggleSettingsMenu() {
  isSettingsMenuOpen.value = !isSettingsMenuOpen.value
}

function closeSettingsMenu() {
  isSettingsMenuOpen.value = false
}

function handleSettingsMenuClick(item: SettingsMenuItem) {
  closeSettingsMenu()

  if (item.screen) {
    emit('navigate', item.screen)
  }
}

function handleDocumentPointerDown(event: PointerEvent) {
  if (!isSettingsMenuOpen.value) return

  const target = event.target as Node | null
  if (!target) return

  if (settingsButton.value?.contains(target) || settingsMenu.value?.contains(target)) {
    return
  }

  closeSettingsMenu()
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
  void loadProfileData()
})

watch(() => props.userId, () => {
  void loadProfileData()
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
})
</script>

<template>
  <div class="profile-page" data-node-id="156:729">
    <div class="profile-page-bg" aria-hidden="true"></div>

    <header class="profile-status-bar">
      <div class="profile-status-time">9:41</div>
      <div class="profile-status-island"></div>
      <img :src="levelsAsset" alt="" class="profile-status-levels" />
    </header>

    <div class="profile-top-actions">
      <button type="button" class="profile-circle-btn" aria-label="返回" @click="emit('back')">
        <img :src="backAsset" alt="" class="profile-back-icon" />
      </button>

      <button
        ref="settingsButton"
        type="button"
        class="profile-circle-btn"
        aria-label="设置"
        aria-haspopup="menu"
        :aria-expanded="isSettingsMenuOpen"
        @click="toggleSettingsMenu"
      >
        <img :src="settingsAsset" alt="" class="profile-settings-icon" />
      </button>

      <div v-if="isSettingsMenuOpen" ref="settingsMenu" class="profile-settings-menu" role="menu" aria-label="设置菜单">
        <button
          v-for="item in settingsMenuItems"
          :key="item.label"
          type="button"
          class="profile-settings-menu-item"
          role="menuitem"
          @click="handleSettingsMenuClick(item)"
        >
          {{ item.label }}
        </button>
      </div>
    </div>

    <div class="profile-scroll">
      <section class="profile-hero">
        <div class="profile-avatar-wrap">
          <div class="profile-avatar-ring">
            <img :src="displayAvatar" :alt="`${displayName}头像`" class="profile-avatar-image" />
          </div>

          <button type="button" class="profile-avatar-edit" aria-label="编辑头像">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M4 17.25V20h2.75L16.81 9.94l-2.75-2.75L4 17.25Zm14.71-8.79a1 1 0 0 0 0-1.42l-1.75-1.75a1 1 0 0 0-1.42 0l-1.12 1.12 3.17 3.17 1.12-1.12Z"
                fill="currentColor"
              />
            </svg>
          </button>
        </div>

        <h1 class="profile-name">{{ displayName }}</h1>
        <p class="profile-motto">{{ displayMotto }}</p>
        <p v-if="isLoading || loadError" :style="{ margin: '8px 0 0', color: loadError ? '#8b2f45' : '#6c6868', fontSize: '12px', lineHeight: '18px' }">
          {{ loadError || '正在同步个人画像...' }}
        </p>
      </section>

      <section class="profile-stats-card">
        <div
          v-for="(item, index) in stats"
          :key="item.label"
          class="profile-stat-item"
          :class="{ 'profile-stat-item-divider': index < stats.length - 1 }"
        >
          <p class="profile-stat-value">{{ item.value }}</p>
          <p class="profile-stat-label">{{ item.label }}</p>
        </div>
      </section>

      <section class="profile-section profile-preference-section">
        <div class="profile-section-row">
          <h2 class="profile-section-title">我的偏好</h2>
          <span class="profile-section-chevron" aria-hidden="true">›</span>
        </div>

        <div v-if="preferences.length" class="profile-preference-list">
          <button v-for="preference in preferences" :key="preference.label" type="button" class="profile-chip">
            <span class="profile-chip-icon" aria-hidden="true">
              <svg v-if="preference.key === 'camera'" viewBox="0 0 24 24">
                <path
                  d="M7 7.5h2l1.25-1.5h3.5L15 7.5h2A2.5 2.5 0 0 1 19.5 10v6A2.5 2.5 0 0 1 17 18.5H7A2.5 2.5 0 0 1 4.5 16v-6A2.5 2.5 0 0 1 7 7.5Zm5 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm0-1.3a1.7 1.7 0 1 1 0-3.4 1.7 1.7 0 0 1 0 3.4Z"
                  fill="currentColor"
                />
              </svg>

              <svg v-else-if="preference.key === 'book'" viewBox="0 0 24 24">
                <path
                  d="M5 6.5A2.5 2.5 0 0 1 7.5 4H19v14H8a3 3 0 0 0-3 3V6.5Zm2.5-1.2c-.72 0-1.3.58-1.3 1.3v11.42A4.13 4.13 0 0 1 8 17.6h9.8V5.3H7.5Zm.7 14.9h10.6v1.2H8.2a1.8 1.8 0 1 1 0-3.6h1v2.4Z"
                  fill="currentColor"
                />
              </svg>

              <svg v-else-if="preference.key === 'gallery'" viewBox="0 0 24 24">
                <path
                  d="M6.5 5h11A2.5 2.5 0 0 1 20 7.5v9a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 16.5v-9A2.5 2.5 0 0 1 6.5 5Zm0 1.3c-.66 0-1.2.54-1.2 1.2v9c0 .66.54 1.2 1.2 1.2h11c.66 0 1.2-.54 1.2-1.2v-9c0-.66-.54-1.2-1.2-1.2h-11Zm2.1 1.8a1.4 1.4 0 1 1 0 2.8 1.4 1.4 0 0 1 0-2.8Zm8.6 7.9H6.8l2.9-3.6 2.2 2.5 1.7-2.1 3.6 3.2Z"
                  fill="currentColor"
                />
              </svg>

              <svg v-else viewBox="0 0 24 24">
                <path
                  d="M7 4.5a2.5 2.5 0 0 0-2.5 2.5v5.4a3.1 3.1 0 0 1 1.3-.3h1.4V7A1.2 1.2 0 0 1 8.4 5.8h.4c.66 0 1.2.54 1.2 1.2v5.1h1.3V7a1.2 1.2 0 0 1 1.2-1.2h.4c.66 0 1.2.54 1.2 1.2v5.1h1.3V8.1A1.2 1.2 0 0 1 16.8 7h.4c.66 0 1.2.54 1.2 1.2v4.9h1.1c1.66 0 3 1.34 3 3v.6H14a5 5 0 0 1-5-5V4.5H7Zm5.5 17a4.5 4.5 0 0 1-4.5-4.5v-1.7h14v1.7a4.5 4.5 0 0 1-4.5 4.5h-5Z"
                  fill="currentColor"
                />
              </svg>
            </span>

            <span>{{ preference.label }}</span>
          </button>
        </div>
        <p v-else class="profile-empty-text">
          {{ isLoading ? '正在读取你的偏好...' : '还没有形成稳定偏好，继续和小薇聊聊或完成一次行程后会更新。' }}
        </p>
      </section>

      <section class="profile-section profile-trail-section">
        <h2 class="profile-section-title">最近足迹</h2>

        <div v-if="recentTrails.length" class="profile-trail-list">
          <div
            v-for="(trail, index) in recentTrails"
            :key="trail.title"
            class="profile-trail-item"
            :class="{ 'profile-trail-item-last': index === recentTrails.length - 1 }"
          >
            <div class="profile-trail-track" aria-hidden="true">
              <span class="profile-trail-ring"></span>
              <span class="profile-trail-dot"></span>
            </div>

            <article class="profile-trail-card">
              <div class="profile-trail-card-head">
                <h3 class="profile-trail-title">{{ trail.title }}</h3>
                <span class="profile-trail-status">已完成</span>
              </div>

              <p class="profile-trail-meta">{{ trail.meta }}</p>
            </article>
          </div>
        </div>
        <p v-else class="profile-empty-text">
          {{ isLoading ? '正在读取最近足迹...' : '还没有最近足迹，完成一次路线或打卡后会出现在这里。' }}
        </p>
      </section>
    </div>

    <p class="profile-footer-caption">你的闲时逛逛搭子</p>

    <nav class="profile-nav" aria-label="底部导航">
      <button type="button" class="profile-nav-btn profile-nav-btn-active" aria-label="个人" aria-current="page">
        <img :src="userAsset" alt="" class="profile-nav-user-icon" />
      </button>

      <button type="button" class="profile-nav-btn profile-nav-btn-muted" aria-label="发现" @click="emit('navigate', 'discover')">
        <img :src="searchAsset" alt="" class="profile-nav-search-icon" />
      </button>

      <button type="button" class="profile-nav-btn profile-nav-btn-muted" aria-label="AI" @click="emit('navigate', 'ai1')">
        <img :src="aiAsset" alt="" class="profile-nav-ai-icon" />
      </button>

      <button type="button" class="profile-nav-btn profile-nav-btn-muted" aria-label="行程" @click="emit('navigate', 'itinerary')">
        <img :src="tripAsset" alt="" class="profile-nav-trip-icon" />
      </button>

      <button type="button" class="profile-nav-btn profile-nav-btn-muted profile-nav-btn-chat" aria-label="聊天" @click="emit('navigate', 'chat')">
        <img :src="chatAsset" alt="" class="profile-nav-chat-icon" />
      </button>
    </nav>

    <footer class="profile-home-indicator-wrap">
      <div class="profile-home-indicator"></div>
    </footer>
  </div>
</template>

<style scoped>
.profile-page {
  position: relative;
  height: 100%;
  overflow: hidden;
  background: #f9f9f9;
  font-family: 'SF Pro Rounded', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.profile-page-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(42% 28% at 11% 78%, rgba(245, 193, 209, 0.92) 0%, rgba(245, 193, 209, 0) 72%),
    radial-gradient(34% 24% at 87% 90%, rgba(255, 245, 145, 0.88) 0%, rgba(255, 245, 145, 0) 68%),
    radial-gradient(36% 18% at 57% 96%, rgba(255, 255, 255, 0.94) 0%, rgba(255, 255, 255, 0) 78%),
    linear-gradient(180deg, #f4eff3 0%, #f8f6f4 47%, #f7f3ee 100%);
}

.profile-status-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 54px;
}

.profile-status-time {
  width: 138px;
  text-align: center;
  font-family: 'SF Pro Text', 'SF Pro Rounded', sans-serif;
  font-size: 17px;
  font-weight: 600;
  line-height: 22px;
  letter-spacing: -0.51px;
  color: #000;
}

.profile-status-island {
  width: 104px;
  height: 28px;
  border-radius: 999px;
  background: #2a2a2a;
}

.profile-status-levels {
  width: 143px;
  height: 54px;
  object-fit: contain;
}

.profile-top-actions {
  position: absolute;
  top: 58px;
  left: 16px;
  right: 16px;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.profile-circle-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #f0f0f0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  cursor: pointer;
}

.profile-circle-btn:focus-visible,
.profile-settings-menu-item:focus-visible {
  outline: 2px solid rgba(70, 28, 58, 0.45);
  outline-offset: 2px;
}

.profile-back-icon {
  width: 16px;
  height: 16px;
}

.profile-settings-icon {
  width: 18px;
  height: 18px;
}

.profile-settings-menu {
  position: absolute;
  top: 47px;
  right: -8px;
  z-index: 7;
  width: 160px;
  overflow: hidden;
  border: 1px solid rgba(216, 216, 216, 0.95);
  border-radius: 21px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
  backdrop-filter: blur(10px);
}

.profile-settings-menu-item {
  width: 100%;
  min-height: 51px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 16px;
  border: 0;
  border-bottom: 1px solid rgba(240, 240, 240, 0.95);
  background: transparent;
  color: #6e6e6e;
  font-size: 16px;
  line-height: 24px;
  font-weight: 500;
  cursor: pointer;
}

.profile-settings-menu-item:last-child {
  border-bottom: 0;
}

.profile-settings-menu-item:hover {
  background: rgba(247, 247, 247, 0.92);
}

.profile-scroll {
  position: relative;
  z-index: 2;
  height: 100%;
  overflow-y: auto;
  padding: 96px 16px 160px;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.profile-scroll::-webkit-scrollbar {
  display: none;
}

.profile-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 34px;
}

.profile-avatar-wrap {
  position: relative;
}

.profile-avatar-ring {
  width: 84px;
  height: 84px;
  padding: 4px;
  border: 3px solid #fff;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
}

.profile-avatar-image {
  width: 100%;
  height: 100%;
  display: block;
  border-radius: 50%;
  object-fit: cover;
}

.profile-avatar-edit {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 25px;
  height: 25px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #fff;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.95);
  color: #5d344f;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);
  cursor: pointer;
}

.profile-avatar-edit svg {
  width: 12px;
  height: 12px;
}

.profile-name {
  margin: 14px 0 4px;
  font-size: 20px;
  line-height: 28px;
  font-weight: 700;
  color: #111;
}

.profile-motto {
  margin: 0;
  font-size: 13px;
  line-height: 18px;
  font-weight: 600;
  color: rgba(70, 28, 58, 0.82);
}

.profile-stats-card {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border: 1px solid #d8d8d8;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.62);
  backdrop-filter: blur(4px);
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.04);
}

.profile-stat-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 76px;
  padding: 12px 8px;
}

.profile-stat-item-divider::after {
  content: '';
  position: absolute;
  top: 22px;
  right: 0;
  width: 1px;
  height: 32px;
  background: #d8d2bf;
}

.profile-stat-value,
.profile-stat-label,
.profile-section-title,
.profile-trail-title,
.profile-trail-meta {
  margin: 0;
}

.profile-stat-value {
  font-size: 18px;
  line-height: 28px;
  font-weight: 700;
  color: #000;
}

.profile-stat-label {
  font-size: 13px;
  line-height: 18px;
  color: #8a8187;
}

.profile-section {
  margin-top: 18px;
}

.profile-section-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.profile-section-title {
  font-size: 16px;
  line-height: 28px;
  font-weight: 700;
  color: #1b1c1c;
}

.profile-section-chevron {
  font-size: 24px;
  line-height: 1;
  color: #767676;
  transform: translateY(-1px);
}

.profile-preference-list {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px 8px;
}

.profile-chip {
  min-height: 29px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0 12px;
  border: 1px solid #a7a7a7;
  border-radius: 999px;
  background: #fff;
  color: #111;
  font-size: 11px;
  font-weight: 600;
  cursor: default;
}

.profile-chip-icon {
  width: 14px;
  height: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #6a6a6a;
}

.profile-chip-icon svg {
  width: 100%;
  height: 100%;
}

.profile-empty-text {
  margin: 12px 0 0;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.62);
  color: #746b70;
  font-size: 12px;
  line-height: 18px;
}

.profile-trail-section {
  margin-top: 22px;
}

.profile-trail-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.profile-trail-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.profile-trail-track {
  position: relative;
  width: 18px;
  flex: 0 0 18px;
  min-height: 84px;
}

.profile-trail-item:not(.profile-trail-item-last) .profile-trail-track::after {
  content: '';
  position: absolute;
  top: 19px;
  left: 8px;
  bottom: -12px;
  width: 1px;
  background: #b7b7b7;
}

.profile-trail-ring,
.profile-trail-dot {
  position: absolute;
  border-radius: 50%;
}

.profile-trail-ring {
  top: 2px;
  left: 0;
  width: 18px;
  height: 18px;
  background: #d8b7ff;
}

.profile-trail-dot {
  top: 7px;
  left: 5px;
  width: 8px;
  height: 8px;
  background: #461c3a;
}

.profile-trail-card {
  flex: 1;
  min-width: 0;
  padding: 14px 16px;
  border: 1px solid #d8d8d8;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.profile-trail-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.profile-trail-title {
  font-size: 14px;
  line-height: 24px;
  font-weight: 700;
  color: #1b1c1c;
}

.profile-trail-status {
  flex-shrink: 0;
  padding: 2px 10px;
  border-radius: 999px;
  background: #ebe3fc;
  font-size: 10px;
  line-height: 15px;
  font-weight: 600;
  color: #000;
}

.profile-trail-meta {
  margin-top: 4px;
  font-size: 12px;
  line-height: 18px;
  color: #7d7d7d;
}

.profile-footer-caption {
  position: absolute;
  bottom: 108px;
  left: 50%;
  z-index: 3;
  margin: 0;
  transform: translateX(-50%);
  font-size: 14px;
  line-height: 20px;
  font-weight: 600;
  color: #6e6e6e;
  white-space: nowrap;
}

.profile-nav {
  position: absolute;
  right: 33px;
  bottom: 30px;
  left: 33px;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 54px;
  padding: 3px 8px;
  border: 1px solid rgba(255, 255, 255, 0.92);
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.66);
  backdrop-filter: blur(10px);
}

.profile-nav-btn {
  position: relative;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
}

.profile-nav-btn-muted {
  background: rgba(0, 0, 0, 0.02);
}

.profile-nav-btn-active {
  background: #000;
}

.profile-nav-user-icon {
  width: 14.4px;
  height: 14.4px;
  filter: brightness(0) invert(1);
}

.profile-nav-search-icon,
.profile-nav-chat-icon {
  width: 16px;
  height: 16px;
}

.profile-nav-ai-icon {
  width: 22px;
  height: 22px;
  filter: brightness(0);
}

.profile-nav-trip-icon {
  width: 12px;
  height: 11.83px;
  filter: brightness(0);
}


.profile-home-indicator-wrap {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 4;
  display: flex;
  justify-content: center;
  padding: 8px 124px;
}

.profile-home-indicator {
  width: 144px;
  height: 5px;
  border-radius: 100px;
  background: #2a2a2a;
}
</style>
