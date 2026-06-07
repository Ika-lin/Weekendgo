<script setup lang="ts">
const emit = defineEmits<{
  back: []
  logout: []
}>()

type SettingsOption = {
  label: string
  icon: string
  danger?: boolean
}

type SettingsSection = {
  title: string
  items: SettingsOption[]
}

const levelsAsset = '/Levels.svg'
const backAsset = '/icon-park-outline_left-1.svg'
const arrowAsset = '/icon-park-outline_left-1.svg'

const settingsSections: SettingsSection[] = [
  {
    title: '系统',
    items: [
      { label: '语言设置', icon: '/System Option Icon.svg' },
      { label: '出行提醒', icon: '/System Option Icon-1.svg' },
      { label: '显示模式', icon: '/System Option Icon-2.svg' },
      { label: '消息通知', icon: '/System Option Icon-3.svg' },
    ],
  },
  {
    title: '导航与出行',
    items: [
      { label: '地图使用设置', icon: '/Navigation Option Icon.svg' },
      { label: '位置权限设置', icon: '/Navigation Option Icon-1.svg' },
      { label: '出行偏好', icon: '/Navigation Option Icon-2.svg' },
    ],
  },
  {
    title: '帮助中心',
    items: [
      { label: '意见反馈', icon: '/Help Center Option Icon.svg' },
      { label: '问题上报', icon: '/Help Center Option Icon-1.svg' },
      { label: '出行帮助', icon: '/Help Center Option Icon-2.svg' },
    ],
  },
  {
    title: '账号',
    items: [
      { label: '安全设置', icon: '/Account Option Icon.svg' },
      { label: '退出登录', icon: '/Account Option Icon-1.svg', danger: true },
    ],
  },
]

function handleOptionClick(item: SettingsOption) {
  if (item.danger && item.label === '退出登录') {
    emit('logout')
  }
}
</script>

<template>
  <div class="settings-page" data-node-id="187:265">
    <div class="settings-page-bg" aria-hidden="true"></div>

    <header class="settings-status-bar">
      <div class="settings-status-time">9:41</div>
      <div class="settings-status-island"></div>
      <img :src="levelsAsset" alt="" class="settings-status-levels" />
    </header>

    <header class="settings-header">
      <button type="button" class="settings-back-btn" aria-label="返回设置上一级" @click="emit('back')">
        <img :src="backAsset" alt="" class="settings-back-icon" />
      </button>

      <h1 class="settings-title">设置</h1>

      <div class="settings-header-spacer" aria-hidden="true"></div>
    </header>

    <div class="settings-scroll">
      <section v-for="section in settingsSections" :key="section.title" class="settings-section">
        <h2 class="settings-section-title">{{ section.title }}</h2>

        <div class="settings-option-list">
          <button
            v-for="item in section.items"
            :key="item.label"
            type="button"
            class="settings-option-card"
            :class="{ 'settings-option-card-danger': item.danger }"
            @click="handleOptionClick(item)"
          >
            <span class="settings-option-main">
              <img :src="item.icon" alt="" class="settings-option-icon" />
              <span class="settings-option-label">{{ item.label }}</span>
            </span>

            <img v-if="!item.danger" :src="arrowAsset" alt="" class="settings-option-arrow" />
          </button>
        </div>
      </section>
    </div>

    <footer class="settings-home-indicator-wrap">
      <div class="settings-home-indicator"></div>
    </footer>
  </div>
</template>

<style scoped>
.settings-page {
  position: relative;
  height: 100%;
  overflow: hidden;
  background: #f9f9f9;
  font-family: 'SF Pro Rounded', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.settings-page-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(36% 26% at 14% 72%, rgba(244, 190, 206, 0.94) 0%, rgba(244, 190, 206, 0) 76%),
    radial-gradient(26% 20% at 92% 96%, rgba(255, 242, 139, 0.88) 0%, rgba(255, 242, 139, 0) 74%),
    radial-gradient(26% 14% at 62% 58%, rgba(255, 255, 255, 0.96) 0%, rgba(255, 255, 255, 0) 82%),
    linear-gradient(180deg, #f4eff3 0%, #f8f5f4 48%, #f8f3ee 100%);
}

.settings-status-bar {
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

.settings-status-time {
  width: 138px;
  text-align: center;
  font-family: 'SF Pro Text', 'SF Pro Rounded', sans-serif;
  font-size: 17px;
  line-height: 22px;
  font-weight: 600;
  letter-spacing: -0.51px;
  color: #000;
}

.settings-status-island {
  width: 104px;
  height: 28px;
  border-radius: 999px;
  background: #2a2a2a;
}

.settings-status-levels {
  width: 143px;
  height: 54px;
  object-fit: contain;
}

.settings-header {
  position: absolute;
  top: 58px;
  left: 16px;
  right: 16px;
  z-index: 5;
  display: grid;
  grid-template-columns: 40px 1fr 40px;
  align-items: center;
}

.settings-back-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 1px solid #f3f3f3;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  cursor: pointer;
}

.settings-back-btn:focus-visible,
.settings-option-card:focus-visible {
  outline: 2px solid rgba(70, 28, 58, 0.45);
  outline-offset: 2px;
}

.settings-back-icon {
  width: 16px;
  height: 16px;
}

.settings-title {
  margin: 0;
  text-align: center;
  font-size: 18px;
  line-height: 24px;
  font-weight: 700;
  color: #1e1e1e;
}

.settings-header-spacer {
  width: 40px;
  height: 40px;
}

.settings-scroll {
  position: relative;
  z-index: 2;
  height: 100%;
  overflow-y: auto;
  padding: 128px 15px 36px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.settings-scroll::-webkit-scrollbar {
  display: none;
}

.settings-section + .settings-section {
  margin-top: 22px;
}

.settings-section-title {
  margin: 0;
  font-size: 16px;
  line-height: 22px;
  font-weight: 700;
  color: #000;
}

.settings-option-list {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.settings-option-card {
  width: 100%;
  min-height: 49px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.01);
  cursor: pointer;
}

.settings-option-card-danger {
  justify-content: flex-start;
}

.settings-option-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.settings-option-icon {
  width: 16px;
  height: 16px;
  display: block;
  flex-shrink: 0;
}

.settings-option-label {
  font-size: 12px;
  line-height: 18px;
  font-weight: 400;
  color: #000;
  white-space: nowrap;
}

.settings-option-card-danger .settings-option-label {
  color: #b71c1c;
}

.settings-option-arrow {
  width: 16px;
  height: 16px;
  display: block;
  flex-shrink: 0;
  transform: rotate(180deg);
}

.settings-home-indicator-wrap {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 4;
  display: flex;
  justify-content: center;
  padding: 8px 124px;
}

.settings-home-indicator {
  width: 144px;
  height: 5px;
  border-radius: 100px;
  background: #2a2a2a;
}
</style>
