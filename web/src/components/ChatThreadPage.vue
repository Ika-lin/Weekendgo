<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { friendChat, getUserProfile, groupChat, groupPlan, type GroupPayload, type UserProfilePayload } from '../api'

const props = withDefaults(defineProps<{
  userId?: string
  threadType?: 'group' | 'friend'
  friendId?: string
  groupMemberIds?: string[]
}>(), {
  userId: 'u_demo_001',
  threadType: 'group',
  friendId: '',
  groupMemberIds: () => [],
})

const emit = defineEmits<{
  back: []
}>()

type ThreadMessage = {
  id: string
  sender: string
  time: string
  side: 'left' | 'right'
  kind?: 'chat' | 'planner' | 'plan'
  text?: string
  image?: string
  imageCount?: number
  avatar?: string
  tone?: 'pink' | 'lavender' | 'soft'
  accentColor?: string
  planTitle?: string
  planMeta?: string[]
  planStops?: Array<{ name: string; time?: string; desc?: string }>
}

const levelsAsset = '/Levels.svg'
const backAsset = '/chevron-left.svg'
const phoneAsset = '/Phone.svg'
const paperclipAsset = '/Paperclip.svg'
const microphoneAsset = '/Microphone.svg'
const paperPlaneAsset = '/PaperPlane.svg'
const groupCoverAsset = '/group-chat-cover.png'

const demoGroupSeedIds = ['u_demo_001', 'u_demo_002', 'u_demo_003']
const groupSessionId = 'weekendgo-demo-group'
const messageDraft = ref('')
const isSendingGroupMessage = ref(false)
const threadBodyRef = ref<HTMLElement | null>(null)
const groupMemberProfiles = ref<UserProfilePayload[]>([])
const friendProfile = ref<UserProfilePayload | null>(null)

const threadMessages = ref<ThreadMessage[]>([])

const isGroupThread = computed(() => props.threadType === 'group')

const resolvedGroupMemberIds = computed(() => {
  const incomingIds = props.groupMemberIds?.length ? props.groupMemberIds : demoGroupSeedIds
  return Array.from(new Set([props.userId, ...incomingIds]))
})

const groupTitle = computed(() => {
  const names = groupMemberProfiles.value.map((profile) => profile.nickname).filter(Boolean)
  return names.length ? `${names.join('、')} 的周末群` : '小薇群规划'
})

const groupMeta = computed(() => {
  const count = groupMemberProfiles.value.length || resolvedGroupMemberIds.value.length
  return `${count} 位成员 · @小薇生成群路线`
})

const threadTitle = computed(() => {
  if (isGroupThread.value) return groupTitle.value
  return friendProfile.value?.nickname || '好友'
})

const threadMeta = computed(() => {
  if (isGroupThread.value) return groupMeta.value
  const profile = friendProfile.value
  if (!profile) return '好友资料加载中'
  return profile.personaSummary || `${profile.socialStyle || '好友'} · 偏好${(profile.favoriteTags || []).slice(0, 2).join('、') || '周末出行'}`
})

const threadAvatar = computed(() => {
  if (isGroupThread.value) return groupCoverAsset
  return friendProfile.value?.avatar || groupCoverAsset
})

const contextPanelTitle = computed(() => (isGroupThread.value ? '群成员画像' : '好友画像'))
const contextPanelChip = computed(() => (isGroupThread.value ? '后端动态分析' : '后端 profile'))
const composerPlaceholder = computed(() => (
  isGroupThread.value ? '@小薇 生成群路线，或直接聊天' : `问小薇怎么约${threadTitle.value}`
))

const memberSummaries = computed(() => {
  if (!isGroupThread.value) {
    const profile = friendProfile.value
    if (!profile) return []

    return [{
      id: profile.userId,
      name: profile.nickname || profile.userId,
      avatar: profile.avatar || groupCoverAsset,
      summary: profile.personaSummary || `${profile.socialStyle || '好友'} · 偏好${(profile.favoriteTags || []).slice(0, 3).join('、') || '城市闲逛'}`,
    }]
  }

  return groupMemberProfiles.value.map((profile) => ({
    id: profile.userId,
    name: profile.nickname || profile.userId,
    avatar: profile.avatar || groupCoverAsset,
    summary: profile.personaSummary || `${profile.socialStyle || '周末搭子'} · 偏好${(profile.favoriteTags || []).slice(0, 2).join('、') || '城市闲逛'}`,
  }))
})

async function scrollThreadToBottom() {
  await nextTick()
  const el = threadBodyRef.value
  if (!el) return

  el.scrollTop = el.scrollHeight
}

function appendUserMessage(text: string) {
  threadMessages.value.push({
    id: `user-${Date.now()}`,
    sender: '我',
    time: '现在',
    side: 'right',
    kind: 'chat',
    text,
    tone: 'lavender',
  })
}

function appendAgentMessages(messages: Array<{ persona: string; emoji?: string; color?: string; text: string }>) {
  for (const message of messages) {
    threadMessages.value.push({
      id: `agent-${Date.now()}-${Math.random().toString(16).slice(2)}`,
      sender: `${message.emoji || ''}${message.persona}`.trim(),
      time: '小薇',
      side: 'left',
      kind: 'chat',
      text: message.text,
      avatar: groupCoverAsset,
      tone: 'soft',
      accentColor: normalizePersonaColor(message.color),
    })
  }
}

function appendFriendAgentReply(text: string) {
  threadMessages.value.push({
    id: `friend-agent-${Date.now()}`,
    sender: '小薇私聊协调',
    time: '刚刚',
    side: 'left',
    kind: 'planner',
    text,
    avatar: groupCoverAsset,
    tone: 'soft',
    accentColor: '#4a7db8',
  })
}

function appendSystemReply(text: string, result?: GroupPayload) {
  const trip = result?.trip
  threadMessages.value.push({
    id: `system-${Date.now()}`,
    sender: isGroupThread.value ? '小薇群规划' : '小薇',
    time: '刚刚',
    side: 'left',
    kind: trip ? 'plan' : 'planner',
    text: buildPlannerText(text, result),
    avatar: groupCoverAsset,
    tone: 'soft',
    accentColor: '#461c3a',
    planTitle: trip?.title,
    planMeta: buildPlanMeta(trip),
    planStops: buildPlanStops(trip),
  })
}

function shouldUseGroupPlanner(text: string) {
  return /@小薇|@AI|@ai|群路线|群规划|生成路线|一起规划/.test(text)
}

function normalizePersonaColor(color?: string) {
  if (!color) return '#fa63a9'
  if (/^#[0-9a-fA-F]{3,8}$/.test(color)) return color
  const colorMap: Record<string, string> = {
    pink: '#fa63a9',
    purple: '#8b5cf6',
    blue: '#4a7db8',
    green: '#18a058',
    orange: '#f59e0b',
  }
  return colorMap[color] || '#fa63a9'
}

function compactReply(reply: string) {
  const lines = reply
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  if (lines.length <= 5) return reply
  return lines.slice(0, 5).join('\n')
}

function buildPlannerText(reply: string, result?: GroupPayload) {
  if (!result?.trip) return compactReply(reply)

  const groupPreferences = result.metadata?.groupPreferences || {}
  const conflicts = Array.isArray(groupPreferences.conflicts) ? groupPreferences.conflicts : []
  const categories = Array.isArray(groupPreferences.preferredCategories) ? groupPreferences.preferredCategories : []
  const areas = Array.isArray(groupPreferences.preferredAreas) ? groupPreferences.preferredAreas : []
  const memberCount = result.members?.length || groupMemberProfiles.value.length || resolvedGroupMemberIds.value.length
  const lines = [`已合并 ${memberCount} 位成员画像，生成了群路线草稿。`]

  if (categories.length || areas.length) {
    lines.push(`综合偏好：${[categories.slice(0, 2).join('、'), areas.slice(0, 2).join('、')].filter(Boolean).join(' · ')}`)
  }
  if (conflicts.length) {
    lines.push(`冲突处理：${conflicts[0]}`)
  }

  return lines.join('\n')
}

function buildPlanMeta(trip: any): string[] {
  if (!trip) return []
  return [trip.city, trip.date, trip.totalBudget || trip.budgetText, trip.duration]
    .filter(Boolean)
    .map(String)
}

function buildPlanStops(trip: any): Array<{ name: string; time?: string; desc?: string }> {
  const stops = Array.isArray(trip?.stops) ? trip.stops : []
  return stops.slice(0, 4).map((stop: any) => ({
    name: stop.name,
    time: stop.time || stop.startTime,
    desc: stop.desc || stop.category || stop.address,
  }))
}

async function loadGroupMembers() {
  const profiles = await Promise.allSettled(resolvedGroupMemberIds.value.map((id) => getUserProfile(id)))
  groupMemberProfiles.value = profiles
    .filter((item): item is PromiseFulfilledResult<UserProfilePayload> => item.status === 'fulfilled')
    .map((item) => item.value)

  if (!threadMessages.value.length) {
    appendSystemReply(
      `我已经接入 ${groupMemberProfiles.value.length || resolvedGroupMemberIds.value.length} 位成员画像。你可以直接聊天，也可以 @小薇 说时间、预算、区域，我会合并偏好后生成统一路线。`,
    )
  }
}

async function loadFriendThread() {
  const friendId = props.friendId || 'u_demo_002'

  try {
    friendProfile.value = await getUserProfile(friendId)
  } catch {
    friendProfile.value = {
      userId: friendId,
      nickname: '好友',
      personaSummary: '好友资料暂时没有加载完整',
      favoriteTags: ['周末出行'],
    }
  }

  if (!threadMessages.value.length) {
    appendSystemReply(`已加载你和 ${friendProfile.value.nickname || '好友'} 的画像。这里由小薇私聊协调 Agent 帮你找共同偏好、组织邀约，也可以继续生成两人路线。`)
  }
}

async function requestGroupPlan(text: string) {
  appendUserMessage(text)
  isSendingGroupMessage.value = true
  void scrollThreadToBottom()

  try {
    const result = await groupPlan({
      user_ids: resolvedGroupMemberIds.value,
      message: text,
      sessionId: groupSessionId,
    })

    const tripTitle = result.trip?.title ? `\n\n路线草稿：${result.trip.title}` : ''
    appendSystemReply(`${result.reply || '已经生成群路线草稿。'}${tripTitle}`, result)
  } catch (error) {
    appendSystemReply(error instanceof Error ? error.message : '群路线生成失败')
  } finally {
    isSendingGroupMessage.value = false
    void scrollThreadToBottom()
  }
}

async function sendGroupMessage() {
  const text = messageDraft.value.trim()
  if (!text || isSendingGroupMessage.value) return

  messageDraft.value = ''

  if (!isGroupThread.value) {
    appendUserMessage(text)
    isSendingGroupMessage.value = true
    void scrollThreadToBottom()

    try {
      const result = await friendChat({
        message: text,
        sessionId: `friend-${props.userId}-${props.friendId || 'u_demo_002'}`,
        userId: props.userId,
        friendId: props.friendId || 'u_demo_002',
      })
      appendFriendAgentReply(result.reply || '我已经看过你们两个人的偏好，可以继续告诉我时间、预算或想约的区域。')
    } catch (error) {
      appendFriendAgentReply(error instanceof Error ? error.message : '小薇私聊协调暂时没有连上')
    } finally {
      isSendingGroupMessage.value = false
      void scrollThreadToBottom()
    }
    return
  }

  if (shouldUseGroupPlanner(text)) {
    await requestGroupPlan(text)
    return
  }

  appendUserMessage(text)
  isSendingGroupMessage.value = true
  void scrollThreadToBottom()

  try {
    const result = await groupChat({
      message: text,
      sessionId: groupSessionId,
      user_ids: resolvedGroupMemberIds.value,
      action: 'chat',
    })

    if (result.messages?.length) {
      appendAgentMessages(result.messages)
    } else if (result.reply) {
      appendSystemReply(result.reply)
    }
  } catch (error) {
    appendSystemReply(error instanceof Error ? error.message : '群聊暂时没有连上')
  } finally {
    isSendingGroupMessage.value = false
    void scrollThreadToBottom()
  }
}

async function loadThreadContext() {
  threadMessages.value = []
  isSendingGroupMessage.value = false
  groupMemberProfiles.value = []
  friendProfile.value = null

  if (isGroupThread.value) {
    await loadGroupMembers()
    return
  }

  await loadFriendThread()
}

onMounted(() => {
  void loadThreadContext()
})

watch(
  () => [props.threadType, props.friendId, props.userId, props.groupMemberIds.join('|')],
  () => {
    void loadThreadContext()
  },
)
</script>

<template>
  <div class="chat-thread-page" :class="{ 'chat-thread-page-friend': !isGroupThread }">
    <div class="chat-thread-bg" aria-hidden="true"></div>

    <header class="chat-thread-status-bar">
      <div class="chat-thread-time">9:41</div>
      <div class="chat-thread-island"></div>
      <img :src="levelsAsset" alt="" class="chat-thread-levels" />
    </header>

    <section class="chat-thread-header">
      <button type="button" class="chat-thread-header-btn" aria-label="返回聊天列表" @click="emit('back')">
        <img :src="backAsset" alt="" class="chat-thread-back-icon" />
      </button>

      <div class="chat-thread-header-main">
        <img :src="threadAvatar" :alt="threadTitle" class="chat-thread-group-avatar" />

        <div class="chat-thread-group-copy">
          <h1 class="chat-thread-group-title">{{ threadTitle }}</h1>
          <p class="chat-thread-group-meta">{{ threadMeta }}</p>
        </div>
      </div>

      <button type="button" class="chat-thread-header-btn" aria-label="发起通话">
        <img :src="phoneAsset" alt="" class="chat-thread-phone-icon" />
      </button>
    </section>

    <section ref="threadBodyRef" class="chat-thread-body">
      <div class="chat-thread-member-panel" :aria-label="contextPanelTitle">
        <div class="chat-thread-member-panel-head">
          <span class="chat-thread-member-panel-title">{{ contextPanelTitle }}</span>
          <span class="chat-thread-member-panel-chip">{{ contextPanelChip }}</span>
        </div>

        <div class="chat-thread-member-list">
          <article v-for="member in memberSummaries" :key="member.id" class="chat-thread-member-card">
            <img :src="member.avatar" :alt="member.name" class="chat-thread-member-avatar" />
            <div class="chat-thread-member-copy">
              <h2>{{ member.name }}</h2>
              <p>{{ member.summary }}</p>
            </div>
          </article>
        </div>
      </div>

      <article
        v-for="message in threadMessages"
        :key="message.id"
        class="chat-thread-message"
        :class="{
          'chat-thread-message-left': message.side === 'left',
          'chat-thread-message-right': message.side === 'right',
        }"
      >
        <template v-if="message.side === 'left'">
          <div class="chat-thread-left-shell" :style="{ '--bubble-accent': message.accentColor || '#fa63a9' }">
            <div class="chat-thread-left-meta">
              <img v-if="message.avatar" :src="message.avatar" :alt="message.sender" class="chat-thread-avatar" />
              <span class="chat-thread-sender">{{ message.sender }}</span>
              <span class="chat-thread-stamp">{{ message.time }}</span>
            </div>

            <div
              v-if="message.text"
              :class="[
                'chat-thread-bubble',
                'chat-thread-bubble-left',
                { 'chat-thread-bubble-planner': message.kind === 'planner' || message.kind === 'plan' },
              ]"
            >
              {{ message.text }}
            </div>

            <div v-if="message.planTitle" class="chat-thread-plan-card">
              <div class="chat-thread-plan-head">
                <span>路线草稿</span>
                <strong>{{ message.planTitle }}</strong>
              </div>

              <div v-if="message.planMeta?.length" class="chat-thread-plan-meta">
                <span v-for="item in message.planMeta" :key="item">{{ item }}</span>
              </div>

              <ol v-if="message.planStops?.length" class="chat-thread-plan-stops">
                <li v-for="stop in message.planStops" :key="`${message.id}-${stop.name}-${stop.time}`">
                  <span class="chat-thread-plan-stop-time">{{ stop.time || '待定' }}</span>
                  <div>
                    <h3>{{ stop.name }}</h3>
                    <p v-if="stop.desc">{{ stop.desc }}</p>
                  </div>
                </li>
              </ol>
            </div>

            <div v-if="message.image" class="chat-thread-image-row">
              <img :src="message.image" :alt="message.sender + ' 分享的照片'" class="chat-thread-photo" />
              <span v-if="message.imageCount" class="chat-thread-photo-count">+{{ message.imageCount }}</span>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="chat-thread-right-shell">
            <div class="chat-thread-right-meta">
              <span class="chat-thread-sender">{{ message.sender }}</span>
              <span class="chat-thread-stamp">{{ message.time }}</span>
            </div>

            <div v-if="message.text" class="chat-thread-bubble chat-thread-bubble-lavender">
              {{ message.text }}
            </div>
          </div>
        </template>
      </article>
    </section>

    <footer class="chat-thread-composer-wrap">
      <form class="chat-thread-composer" @submit.prevent="sendGroupMessage">
        <button type="button" class="chat-thread-composer-side-btn" aria-label="添加附件">
          <img :src="paperclipAsset" alt="" class="chat-thread-composer-icon" />
        </button>

        <label class="chat-thread-input-shell">
          <img :src="microphoneAsset" alt="" class="chat-thread-input-mic" />
          <input
            v-model="messageDraft"
            type="text"
            class="chat-thread-input"
            :aria-label="isGroupThread ? '输入群聊消息' : '输入私聊消息'"
            :placeholder="composerPlaceholder"
            :disabled="isSendingGroupMessage"
          />
        </label>

        <button
          type="submit"
          class="chat-thread-send-btn"
          :disabled="isSendingGroupMessage"
          :aria-label="isGroupThread ? '发送群聊消息' : '发送私聊消息'"
        >
          <img :src="paperPlaneAsset" alt="" class="chat-thread-send-icon" />
        </button>
      </form>

      <div class="chat-thread-home-indicator"></div>
    </footer>
  </div>
</template>

<style scoped>
.chat-thread-page {
  position: relative;
  height: 100%;
  overflow: hidden;
  background: linear-gradient(180deg, #f9f9f9 0%, #f8f4f4 62%, #f7f3ef 100%);
  font-family: 'SF Pro Rounded', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.chat-thread-page-friend {
  background: linear-gradient(180deg, #f9f9f9 0%, #f4f7f8 62%, #eff4f6 100%);
}

.chat-thread-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(44% 26% at 10% 82%, rgba(245, 195, 211, 0.86) 0%, rgba(245, 195, 211, 0) 72%),
    radial-gradient(34% 16% at 92% 98%, rgba(255, 236, 170, 0.84) 0%, rgba(255, 236, 170, 0) 72%),
    radial-gradient(46% 24% at 56% 64%, rgba(255, 255, 255, 0.92) 0%, rgba(255, 255, 255, 0) 80%);
}

.chat-thread-status-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 54px;
}

.chat-thread-time {
  width: 138px;
  color: #000;
  text-align: center;
  font-size: 17px;
  line-height: 22px;
  font-weight: 600;
  letter-spacing: -0.51px;
}

.chat-thread-island {
  width: 104px;
  height: 28px;
  border-radius: 999px;
  background: #2a2a2a;
}

.chat-thread-levels {
  width: 143px;
  height: 54px;
  object-fit: contain;
}

.chat-thread-header {
  position: absolute;
  top: 58px;
  left: 16px;
  right: 16px;
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-thread-header-btn,
.chat-thread-composer-side-btn,
.chat-thread-send-btn {
  padding: 0;
  border: 0;
  cursor: pointer;
}

.chat-thread-header-btn {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 20px rgba(35, 31, 32, 0.06);
  flex-shrink: 0;
}

.chat-thread-back-icon {
  width: 16px;
  height: 16px;
}

.chat-thread-phone-icon {
  width: 20px;
  height: 20px;
}

.chat-thread-header-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-thread-group-avatar {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  object-fit: cover;
  flex-shrink: 0;
  box-shadow: 0 10px 20px rgba(70, 28, 58, 0.08);
}

.chat-thread-page-friend .chat-thread-group-avatar {
  border-radius: 50%;
  box-shadow: 0 10px 20px rgba(47, 91, 124, 0.08);
}

.chat-thread-group-copy {
  min-width: 0;
}

.chat-thread-group-title,
.chat-thread-group-meta,
.chat-thread-sender,
.chat-thread-stamp {
  margin: 0;
}

.chat-thread-group-title {
  color: #2c2828;
  font-size: 16px;
  line-height: 22px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-thread-group-meta {
  color: #b0b0b0;
  font-size: 12px;
  line-height: 18px;
}

.chat-thread-body {
  position: absolute;
  top: 124px;
  left: 0;
  right: 0;
  bottom: 96px;
  z-index: 3;
  overflow-y: auto;
  padding: 8px 16px 24px;
  scrollbar-width: none;
}

.chat-thread-body::-webkit-scrollbar {
  display: none;
}

.chat-thread-member-panel {
  margin-bottom: 18px;
  padding: 14px;
  border: 1px solid rgba(70, 28, 58, 0.12);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 14px 30px rgba(70, 28, 58, 0.06);
}

.chat-thread-member-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.chat-thread-member-panel-title {
  color: #461c3a;
  font-size: 14px;
  line-height: 20px;
  font-weight: 800;
}

.chat-thread-member-panel-chip {
  flex-shrink: 0;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(70, 28, 58, 0.08);
  color: #461c3a;
  font-size: 10px;
  line-height: 14px;
  font-weight: 700;
}

.chat-thread-page-friend .chat-thread-member-panel {
  border-color: rgba(74, 125, 184, 0.14);
}

.chat-thread-page-friend .chat-thread-member-panel-title {
  color: #2f5b7c;
}

.chat-thread-page-friend .chat-thread-member-panel-chip {
  background: rgba(74, 125, 184, 0.1);
  color: #2f5b7c;
}

.chat-thread-member-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-thread-member-card {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.chat-thread-member-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.chat-thread-member-copy {
  min-width: 0;
}

.chat-thread-member-copy h2,
.chat-thread-member-copy p {
  margin: 0;
}

.chat-thread-member-copy h2 {
  color: #2c2828;
  font-size: 13px;
  line-height: 18px;
  font-weight: 700;
}

.chat-thread-member-copy p {
  overflow: hidden;
  color: #8b8585;
  font-size: 11px;
  line-height: 16px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chat-thread-message {
  display: flex;
  margin-bottom: 18px;
}

.chat-thread-message-left {
  justify-content: flex-start;
}

.chat-thread-message-right {
  justify-content: flex-end;
}

.chat-thread-left-shell,
.chat-thread-right-shell {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-thread-left-shell {
  max-width: 320px;
}

.chat-thread-right-shell {
  align-items: flex-end;
  max-width: 300px;
}

.chat-thread-left-meta,
.chat-thread-right-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-thread-right-meta {
  justify-content: flex-end;
}

.chat-thread-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.chat-thread-sender {
  color: #2c2828;
  font-size: 16px;
  line-height: 22px;
  font-weight: 600;
}

.chat-thread-stamp {
  color: #999;
  font-size: 12px;
  line-height: 18px;
}

.chat-thread-bubble {
  border-radius: 28px;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 24px;
  letter-spacing: 0;
  white-space: pre-line;
  box-shadow: 0 10px 24px rgba(53, 44, 54, 0.04);
}

.chat-thread-bubble-left {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(70, 28, 58, 0.08);
  background: rgba(255, 255, 255, 0.92);
  color: #343330;
}

.chat-thread-bubble-left::before {
  content: '';
  position: absolute;
  top: 12px;
  bottom: 12px;
  left: 0;
  width: 4px;
  border-radius: 0 999px 999px 0;
  background: var(--bubble-accent, #fa63a9);
}

.chat-thread-bubble-planner {
  border-color: rgba(70, 28, 58, 0.14);
  background: linear-gradient(135deg, rgba(255, 249, 222, 0.92), rgba(255, 235, 246, 0.92));
  color: #461c3a;
}

.chat-thread-bubble-lavender {
  background: #461c3a;
  color: #fff;
}

.chat-thread-plan-card {
  width: min(300px, 100%);
  padding: 14px;
  border: 1px solid rgba(70, 28, 58, 0.12);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14px 26px rgba(70, 28, 58, 0.08);
}

.chat-thread-plan-head {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.chat-thread-plan-head span {
  color: #8b8585;
  font-size: 11px;
  line-height: 16px;
  font-weight: 700;
}

.chat-thread-plan-head strong {
  color: #461c3a;
  font-size: 15px;
  line-height: 21px;
  font-weight: 800;
}

.chat-thread-plan-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.chat-thread-plan-meta span {
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(70, 28, 58, 0.08);
  color: #461c3a;
  font-size: 11px;
  line-height: 15px;
  font-weight: 700;
}

.chat-thread-plan-stops {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.chat-thread-plan-stops li {
  display: flex;
  gap: 10px;
}

.chat-thread-plan-stop-time {
  flex-shrink: 0;
  width: 46px;
  color: #8b8585;
  font-size: 11px;
  line-height: 18px;
  font-weight: 700;
}

.chat-thread-plan-stops h3,
.chat-thread-plan-stops p {
  margin: 0;
}

.chat-thread-plan-stops h3 {
  color: #2c2828;
  font-size: 13px;
  line-height: 18px;
  font-weight: 800;
}

.chat-thread-plan-stops p {
  color: #8b8585;
  font-size: 11px;
  line-height: 16px;
}

.chat-thread-image-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-left: 42px;
}

.chat-thread-photo {
  display: block;
  width: 204px;
  height: 254px;
  border-radius: 18px;
  object-fit: cover;
}

.chat-thread-photo-count {
  padding-bottom: 12px;
  color: #999;
  font-size: 14px;
  line-height: 20px;
}

.chat-thread-composer-wrap {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 4;
  padding: 8px 16px 8px;
}

.chat-thread-composer {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-thread-composer-side-btn {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
}

.chat-thread-composer-icon {
  width: 24px;
  height: 24px;
}

.chat-thread-input-shell {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  height: 48px;
  padding: 0 16px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
}

.chat-thread-input-mic {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.chat-thread-input {
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  color: #343330;
  font-size: 14px;
}

.chat-thread-send-btn {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #000;
}

.chat-thread-send-btn:disabled {
  opacity: 0.58;
}

.chat-thread-send-icon {
  width: 22px;
  height: 22px;
  filter: brightness(0) invert(1);
}

.chat-thread-home-indicator {
  width: 144px;
  height: 5px;
  margin: 10px auto 0;
  border-radius: 100px;
  background: #2a2a2a;
}
</style>
