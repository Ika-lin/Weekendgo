<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getUserProfile, type UserProfilePayload } from '../api'

type Screen = 'discover' | 'ai1' | 'itinerary' | 'chat' | 'chatDetail' | 'profile'

type ChatConversationPayload = {
  id: string
  title: string
  preview: string
  time: string
  image: string
  unread?: number
  isGroup?: boolean
  memberIds?: string[]
}

type CreatedGroupConversationPayload = ChatConversationPayload & {
  isGroup: true
  memberIds: string[]
}

const props = withDefaults(defineProps<{
  userId?: string
  createdGroups?: CreatedGroupConversationPayload[]
}>(), {
  userId: 'u_demo_001',
  createdGroups: () => [],
})

const emit = defineEmits<{
  navigate: [screen: Screen]
  openConversation: [conversation: { id: string; isGroup: boolean; memberIds?: string[] }]
  createGroup: [conversation: CreatedGroupConversationPayload]
}>()

type Story = {
  id: string
  label: string
  image: string
  highlighted?: boolean
  isSelf?: boolean
}

type Conversation = ChatConversationPayload

const levelsAsset = '/Levels.svg'
const searchAsset = '/uil_search.svg'
const caretAsset = '/CaretRight.svg'
const userAsset = '/user.svg'
const aiAsset = '/Icon-3.svg'
const tripAsset = '/lucide_map.svg'
const chatAsset = '/ChatTeardrop-light.svg'
const groupChatCoverAsset = '/group-chat-cover.png'

const demoFriendIds = ['u_demo_002', 'u_demo_003', 'u_demo_004', 'u_demo_005']
const friendProfiles = ref<UserProfilePayload[]>([])
const isCreateGroupOpen = ref(false)
const selectedGroupMemberIds = ref<string[]>([])

const fallbackStories: Story[] = [
  {
    id: 'self',
    label: '我',
    image: '/3b7a548733ee2a58982b32aae111822d65320db9.jpg',
    isSelf: true,
  },
  {
    id: 'xiaoyou',
    label: '小优',
    image: '/2149265200 1.png',
    highlighted: true,
  },
  {
    id: 'xiaoai',
    label: '小艾',
    image: '/Chat Image.png',
    highlighted: true,
  },
  {
    id: 'jack',
    label: '杰克',
    image: '/Chat Image-2.png',
  },
  {
    id: 'xiaogai',
    label: '小盖',
    image: '/Profile Image.png',
  },
  {
    id: 'xiaoqian',
    label: '小千',
    image: '/Chat Image-1.png',
  },
]

const fallbackConversations: Conversation[] = [
  {
    id: 'group',
    title: '武康路老洋房摄影',
    preview: 'OK!',
    time: '2.12PM',
    image: groupChatCoverAsset,
    isGroup: true,
    memberIds: ['u_demo_001', 'u_demo_002', 'u_demo_003'],
  },
  {
    id: 'xiaoai',
    title: '小艾',
    preview: '你们拍的照片好漂亮，可以分享一下技巧吗？',
    time: '2.35 PM',
    image: '/Chat Image.png',
    unread: 1,
  },
  {
    id: 'xiaogai',
    title: '小盖',
    preview: '你们拍的下午阳光很好！',
    time: '2.25 PM',
    image: '/Profile Image.png',
    unread: 1,
  },
  {
    id: 'xiaoyou',
    title: '小优',
    preview: '回头我把照片传给你。',
    time: '2.16PM',
    image: '/2149265200 1.png',
  },
  {
    id: 'xiaoqian',
    title: '小千',
    preview: '你带相机了吗？',
    time: '1.56 PM',
    image: '/Chat Image-1.png',
    unread: 1,
  },
  {
    id: 'jack',
    title: '杰克',
    preview: '我们约在校外Manner咖啡店吧。',
    time: '11月1日',
    image: '/Chat Image-2.png',
  },
]

const stories = computed<Story[]>(() => {
  if (!friendProfiles.value.length) return fallbackStories

  return [
    {
      id: props.userId,
      label: '我',
      image: '/3b7a548733ee2a58982b32aae111822d65320db9.jpg',
      isSelf: true,
    },
    ...friendProfiles.value.map((profile, index) => ({
      id: profile.userId,
      label: profile.nickname || `好友 ${index + 1}`,
      image: profile.avatar || fallbackStories[index + 1]?.image || '/Profile Image.png',
      highlighted: index < 2,
    })),
  ]
})

const conversations = computed<Conversation[]>(() => {
  if (!friendProfiles.value.length) return [...props.createdGroups, ...fallbackConversations]

  const groupNames = friendProfiles.value.slice(0, 3).map((profile) => profile.nickname || profile.userId)
  const defaultGroupMemberIds = [props.userId, ...friendProfiles.value.slice(0, 2).map((profile) => profile.userId)]

  return [
    {
      id: 'group',
      title: `${groupNames.join('、')} 的周末群`,
      preview: '小薇可读取成员画像，生成统一路线',
      time: '现在',
      image: groupChatCoverAsset,
      unread: 1,
      isGroup: true,
      memberIds: defaultGroupMemberIds,
    },
    ...props.createdGroups,
    ...friendProfiles.value.map((profile, index) => ({
      id: profile.userId,
      title: profile.nickname || `好友 ${index + 1}`,
      preview: profile.personaSummary || `${profile.socialStyle || '好友'} · 偏好${(profile.favoriteTags || []).slice(0, 2).join('、') || '周末出行'}`,
      time: index < 2 ? '在线' : '今天',
      image: profile.avatar || fallbackConversations[index + 1]?.image || '/Profile Image.png',
      unread: index === 0 ? 1 : undefined,
    })),
  ]
})

const selectedGroupMembers = computed(() => {
  return friendProfiles.value.filter((profile) => selectedGroupMemberIds.value.includes(profile.userId))
})

async function loadFriends() {
  const profiles = await Promise.allSettled(demoFriendIds.map((id) => getUserProfile(id)))
  friendProfiles.value = profiles
    .filter((item): item is PromiseFulfilledResult<UserProfilePayload> => item.status === 'fulfilled')
    .map((item) => item.value)
}

function openConversation(conversation: Conversation) {
  emit('openConversation', {
    id: conversation.id,
    isGroup: Boolean(conversation.isGroup),
    memberIds: conversation.memberIds,
  })
}

function openCreateGroup() {
  selectedGroupMemberIds.value = friendProfiles.value.slice(0, 2).map((profile) => profile.userId)
  isCreateGroupOpen.value = true
}

function closeCreateGroup() {
  isCreateGroupOpen.value = false
}

function toggleGroupMember(userId: string) {
  if (selectedGroupMemberIds.value.includes(userId)) {
    selectedGroupMemberIds.value = selectedGroupMemberIds.value.filter((id) => id !== userId)
    return
  }

  selectedGroupMemberIds.value = [...selectedGroupMemberIds.value, userId]
}

function createGroupConversation() {
  const memberIds = Array.from(new Set([props.userId, ...selectedGroupMemberIds.value]))
  if (memberIds.length < 2) return

  const names = selectedGroupMembers.value.map((profile) => profile.nickname || profile.userId)
  const group: CreatedGroupConversationPayload = {
    id: `created-group-${Date.now()}`,
    title: names.length ? `${names.slice(0, 3).join('、')} 的群聊` : '新的群聊',
    preview: '已接入小薇群协调 Agent，可 @小薇 生成群路线',
    time: '刚刚',
    image: groupChatCoverAsset,
    isGroup: true,
    unread: 1,
    memberIds,
  }

  emit('createGroup', group)
  closeCreateGroup()
  openConversation(group)
}

onMounted(() => {
  void loadFriends()
})
</script>

<template>
  <div class="chat-page">
    <div class="chat-page-bg" aria-hidden="true"></div>

    <header class="chat-status-bar">
      <div class="chat-status-time">9:41</div>
      <div class="chat-status-island"></div>
      <img :src="levelsAsset" alt="" class="chat-status-levels" />
    </header>

    <section class="chat-content">
      <button type="button" class="chat-search">
        <span class="chat-search-main">
          <img :src="searchAsset" alt="" class="chat-search-icon" />
          <span class="chat-search-placeholder">Search</span>
        </span>

        <span class="chat-search-action" aria-hidden="true">
          <img :src="caretAsset" alt="" class="chat-search-caret" />
        </span>
      </button>

      <div class="chat-stories" role="list" aria-label="聊天动态">
        <div v-for="story in stories" :key="story.id" class="chat-story" role="listitem">
          <div
            class="chat-story-avatar"
            :class="{
              'chat-story-avatar-highlight': story.highlighted,
              'chat-story-avatar-self': story.isSelf,
            }"
          >
            <img :src="story.image" :alt="story.label" />
            <span v-if="story.isSelf" class="chat-story-add" aria-hidden="true">+</span>
          </div>

          <p class="chat-story-label">{{ story.label }}</p>
        </div>
      </div>

      <div class="chat-divider"></div>

      <div class="chat-list-head">
        <span>会话</span>
        <button type="button" class="chat-create-group-btn" @click="openCreateGroup">
          创建群聊
        </button>
      </div>

      <div class="chat-list">
        <button
          v-for="conversation in conversations"
          :key="conversation.id"
          type="button"
          :class="['chat-row', conversation.isGroup ? 'chat-row-group' : 'chat-row-friend']"
          @click="openConversation(conversation)"
        >
          <div class="chat-row-main">
            <div class="chat-avatar" :class="{ 'chat-avatar-group': conversation.isGroup }">
              <img :src="conversation.image" :alt="conversation.title" />
            </div>

            <div class="chat-copy">
              <div class="chat-title-row">
                <h2 class="chat-title">{{ conversation.title }}</h2>
                <span
                  class="chat-kind-pill"
                  :class="{ 'chat-kind-pill-group': conversation.isGroup }"
                >
                  {{ conversation.isGroup ? '群聊' : '好友' }}
                </span>
              </div>
              <p class="chat-preview">{{ conversation.preview }}</p>
            </div>
          </div>

          <div class="chat-meta">
            <span class="chat-time">{{ conversation.time }}</span>
            <span v-if="conversation.unread" class="chat-badge">{{ conversation.unread }}</span>
          </div>
        </button>
      </div>
    </section>

    <div v-if="isCreateGroupOpen" class="chat-group-sheet" role="dialog" aria-modal="true" aria-label="创建群聊">
      <button type="button" class="chat-group-sheet-backdrop" aria-label="关闭创建群聊" @click="closeCreateGroup"></button>

      <section class="chat-group-sheet-panel">
        <header class="chat-group-sheet-head">
          <div>
            <p>新群聊</p>
            <h2>选择好友加入</h2>
          </div>
          <button type="button" class="chat-group-sheet-close" aria-label="关闭" @click="closeCreateGroup">×</button>
        </header>

        <div class="chat-group-selected-row">
          <span>{{ selectedGroupMembers.length }} 位好友</span>
          <strong>小薇会根据成员画像协调路线</strong>
        </div>

        <div class="chat-group-member-list">
          <button
            v-for="profile in friendProfiles"
            :key="profile.userId"
            type="button"
            class="chat-group-member-row"
            :class="{ active: selectedGroupMemberIds.includes(profile.userId) }"
            @click="toggleGroupMember(profile.userId)"
          >
            <img
              :src="profile.avatar || '/Profile Image.png'"
              :alt="profile.nickname || profile.userId"
              class="chat-group-member-avatar"
            />
            <span class="chat-group-member-copy">
              <strong>{{ profile.nickname || profile.userId }}</strong>
              <small>{{ profile.personaSummary || (profile.favoriteTags || []).slice(0, 3).join('、') || '周末出行偏好' }}</small>
            </span>
            <span class="chat-group-member-check" aria-hidden="true">
              {{ selectedGroupMemberIds.includes(profile.userId) ? '✓' : '' }}
            </span>
          </button>
        </div>

        <button
          type="button"
          class="chat-group-create-submit"
          :disabled="selectedGroupMembers.length === 0"
          @click="createGroupConversation"
        >
          创建并进入群聊
        </button>
      </section>
    </div>

    <nav class="chat-nav" aria-label="底部导航">
      <button
        type="button"
        class="chat-nav-btn chat-nav-btn-muted"
        aria-label="个人"
        @click="emit('navigate', 'profile')"
      >
        <img :src="userAsset" alt="" class="chat-nav-user-icon" />
      </button>

      <button
        type="button"
        class="chat-nav-btn chat-nav-btn-muted"
        aria-label="发现"
        @click="emit('navigate', 'discover')"
      >
        <img src="/MagnifyingGlass.svg" alt="" class="chat-nav-search-icon" />
      </button>

      <button
        type="button"
        class="chat-nav-btn chat-nav-btn-muted"
        aria-label="AI"
        @click="emit('navigate', 'ai1')"
      >
        <img :src="aiAsset" alt="" class="chat-nav-ai-icon" />
      </button>

      <button
        type="button"
        class="chat-nav-btn chat-nav-btn-muted"
        aria-label="行程"
        @click="emit('navigate', 'itinerary')"
      >
        <img :src="tripAsset" alt="" class="chat-nav-trip-icon" />
      </button>

      <button
        type="button"
        class="chat-nav-btn chat-nav-btn-active"
        aria-label="聊天"
        aria-current="page"
      >
        <span class="chat-nav-chat-wrap" aria-hidden="true">
          <img :src="chatAsset" alt="" class="chat-nav-chat-icon" />
          <span class="chat-nav-chat-dot"></span>
        </span>
      </button>
    </nav>

    <footer class="chat-home-indicator-wrap">
      <div class="chat-home-indicator"></div>
    </footer>
  </div>
</template>

<style scoped>
.chat-page {
  position: relative;
  height: 100%;
  overflow: hidden;
  background: linear-gradient(180deg, #f9f9f9 0%, #f8f5f4 56%, #f6f0ee 100%);
  font-family: 'SF Pro Rounded', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.chat-page-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(42% 22% at 10% 84%, rgba(243, 194, 210, 0.84) 0%, rgba(243, 194, 210, 0) 70%),
    radial-gradient(36% 18% at 92% 96%, rgba(255, 236, 177, 0.82) 0%, rgba(255, 236, 177, 0) 72%),
    radial-gradient(44% 25% at 50% 86%, rgba(255, 255, 255, 0.86) 0%, rgba(255, 255, 255, 0) 76%);
}

.chat-status-bar {
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

.chat-status-time {
  width: 138px;
  color: #000;
  text-align: center;
  font-size: 17px;
  line-height: 22px;
  font-weight: 600;
  letter-spacing: -0.51px;
}

.chat-status-island {
  width: 104px;
  height: 28px;
  border-radius: 999px;
  background: #2a2a2a;
}

.chat-status-levels {
  width: 143px;
  height: 54px;
  object-fit: contain;
}

.chat-content {
  position: absolute;
  top: 58px;
  left: 16px;
  right: 16px;
  bottom: 84px;
  z-index: 3;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.chat-search,
.chat-row,
.chat-nav-btn {
  padding: 0;
  border: 0;
  cursor: pointer;
}

.chat-search {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 4px 4px 4px 16px;
  border: 1px solid #f3f3f3;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
}

.chat-search-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-search-icon {
  width: 14px;
  height: 14px;
}

.chat-search-placeholder {
  color: #b0b0b0;
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
}

.chat-search-action {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1.275px solid #f3f3f3;
  border-radius: 999px;
  background: #f9f9f9;
  flex-shrink: 0;
}

.chat-search-caret {
  width: 18px;
  height: 18px;
}

.chat-stories {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding-right: 20px;
  padding-bottom: 2px;
  scrollbar-width: none;
}

.chat-stories::-webkit-scrollbar,
.chat-list::-webkit-scrollbar {
  display: none;
}

.chat-story {
  flex: 0 0 auto;
  width: 56px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.chat-story-avatar {
  position: relative;
  width: 56px;
  height: 56px;
  padding: 2px;
  border-radius: 50%;
  border: 2px solid #eee;
  background: #f7f7f7;
}

.chat-story-avatar img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.chat-story-avatar-highlight {
  border-color: transparent;
  background: linear-gradient(135deg, #57d4ff 0%, #7d60ff 100%);
}

.chat-story-avatar-self {
  padding: 0;
  border: 0;
  overflow: hidden;
  background: #000;
}

.chat-story-avatar-self img {
  opacity: 0.5;
}

.chat-story-add {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 28px;
  line-height: 1;
  font-weight: 300;
}

.chat-story-label {
  margin: 0;
  color: #000;
  font-size: 12px;
  line-height: 18px;
  white-space: nowrap;
}

.chat-divider {
  height: 1px;
  background: rgba(224, 224, 224, 0.92);
}

.chat-list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: -8px;
  color: #2c2828;
  font-size: 16px;
  line-height: 22px;
  font-weight: 800;
}

.chat-create-group-btn {
  min-width: 86px;
  height: 34px;
  padding: 0 12px;
  border: 1px solid rgba(70, 28, 58, 0.12);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  color: #461c3a;
  font-size: 12px;
  line-height: 18px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(70, 28, 58, 0.06);
}

.chat-create-group-btn:active {
  transform: scale(0.98);
}

.chat-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 2px;
  padding-bottom: 110px;
}

.chat-row {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  min-height: 76px;
  padding: 10px 12px;
  border: 1px solid transparent;
  border-radius: 20px;
  text-align: left;
  transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
}

.chat-row:active {
  transform: scale(0.985);
}

.chat-row-friend {
  background: rgba(255, 255, 255, 0.5);
  border-color: rgba(255, 255, 255, 0.6);
}

.chat-row-group {
  padding: 13px 12px;
  overflow: hidden;
  border-color: rgba(70, 28, 58, 0.15);
  background: linear-gradient(135deg, rgba(255, 249, 222, 0.94) 0%, rgba(255, 234, 246, 0.94) 100%);
  box-shadow: 0 14px 28px rgba(70, 28, 58, 0.08);
}

.chat-row-group::before {
  content: '';
  position: absolute;
  top: 14px;
  bottom: 14px;
  left: 0;
  width: 4px;
  border-radius: 0 999px 999px 0;
  background: #461c3a;
}

.chat-row-main {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-avatar {
  position: relative;
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  overflow: hidden;
  background: #f7f7f7;
}

.chat-avatar img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.chat-avatar-group {
  display: grid;
  place-items: center;
  overflow: visible;
  border-radius: 18px;
  background: #461c3a;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.38);
}

.chat-avatar-group img {
  width: 46px;
  height: 46px;
  border: 2px solid rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  box-shadow: 0 6px 14px rgba(70, 28, 58, 0.18);
}

.chat-avatar-group::after {
  content: '群';
  position: absolute;
  right: -4px;
  bottom: -3px;
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: #461c3a;
  color: #fff;
  font-size: 11px;
  line-height: 1;
  font-weight: 700;
}

.chat-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chat-title,
.chat-preview {
  margin: 0;
}

.chat-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.chat-title {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: #2c2828;
  font-size: 16px;
  line-height: 22px;
  font-weight: 600;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chat-row-group .chat-title {
  color: #461c3a;
  font-weight: 700;
}

.chat-kind-pill {
  flex-shrink: 0;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(44, 40, 40, 0.06);
  color: #8b8585;
  font-size: 10px;
  line-height: 14px;
  font-weight: 700;
}

.chat-kind-pill-group {
  background: rgba(70, 28, 58, 0.1);
  color: #461c3a;
}

.chat-preview {
  overflow: hidden;
  color: #999;
  font-size: 12px;
  line-height: 18px;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chat-row-group .chat-preview {
  color: rgba(70, 28, 58, 0.66);
}

.chat-meta {
  flex-shrink: 0;
  min-height: 42px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
}

.chat-time {
  color: #999;
  font-size: 12px;
  line-height: 18px;
}

.chat-badge {
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: #461c3a;
  color: #fff;
  text-align: center;
  font-size: 12px;
  line-height: 16px;
}

.chat-nav {
  position: absolute;
  box-sizing: border-box;
  top: 756px;
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

.chat-nav-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  padding: 12px;
  border-radius: 1000px;
}

.chat-nav-btn-muted {
  background: rgba(0, 0, 0, 0.02);
}

.chat-nav-btn-active {
  background: #000;
}

.chat-nav-user-icon {
  display: block;
  width: 14.4px;
  height: 14.4px;
  filter: brightness(0);
}

.chat-nav-search-icon,
.chat-nav-chat-icon {
  display: block;
  width: 16px;
  height: 16px;
}

.chat-nav-chat-wrap {
  position: relative;
  display: block;
  width: 16px;
  height: 16px;
}

.chat-nav-ai-icon,
.chat-nav-trip-icon {
  display: block;
}

.chat-nav-ai-icon {
  width: 22px;
  height: 22px;
}

.chat-nav-trip-icon {
  width: 12px;
  height: 11.83px;
}

.chat-nav-chat-dot {
  position: absolute;
  top: 0;
  right: 0;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4a7db8;
}

.chat-group-sheet {
  position: absolute;
  inset: 0;
  z-index: 40;
}

.chat-group-sheet-backdrop {
  position: absolute;
  inset: 0;
  border: 0;
  background: rgba(42, 32, 38, 0.26);
  cursor: pointer;
}

.chat-group-sheet-panel {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 12px;
  max-height: 620px;
  padding: 18px 16px 16px;
  border: 1px solid rgba(255, 255, 255, 0.86);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 24px 60px rgba(42, 32, 38, 0.2);
}

.chat-group-sheet-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.chat-group-sheet-head p,
.chat-group-sheet-head h2 {
  margin: 0;
}

.chat-group-sheet-head p {
  color: #8b8585;
  font-size: 12px;
  line-height: 18px;
  font-weight: 700;
}

.chat-group-sheet-head h2 {
  color: #2c2828;
  font-size: 22px;
  line-height: 28px;
  font-weight: 900;
}

.chat-group-sheet-close {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(70, 28, 58, 0.08);
  color: #461c3a;
  font-size: 24px;
  line-height: 1;
  cursor: pointer;
}

.chat-group-selected-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin: 14px 0 12px;
  padding: 10px 12px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(255, 249, 222, 0.94), rgba(255, 235, 246, 0.94));
}

.chat-group-selected-row span {
  color: #461c3a;
  font-size: 13px;
  line-height: 18px;
  font-weight: 900;
  white-space: nowrap;
}

.chat-group-selected-row strong {
  min-width: 0;
  overflow: hidden;
  color: rgba(70, 28, 58, 0.66);
  font-size: 11px;
  line-height: 16px;
  font-weight: 700;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chat-group-member-list {
  display: flex;
  max-height: 310px;
  overflow-y: auto;
  flex-direction: column;
  gap: 8px;
  padding-right: 2px;
  scrollbar-width: none;
}

.chat-group-member-list::-webkit-scrollbar {
  display: none;
}

.chat-group-member-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 64px;
  padding: 8px 10px;
  border: 1px solid rgba(44, 40, 40, 0.06);
  border-radius: 18px;
  background: rgba(248, 245, 244, 0.72);
  text-align: left;
  cursor: pointer;
}

.chat-group-member-row.active {
  border-color: rgba(70, 28, 58, 0.18);
  background: rgba(255, 240, 248, 0.92);
}

.chat-group-member-avatar {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  object-fit: cover;
}

.chat-group-member-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chat-group-member-copy strong,
.chat-group-member-copy small {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chat-group-member-copy strong {
  color: #2c2828;
  font-size: 14px;
  line-height: 20px;
  font-weight: 800;
}

.chat-group-member-copy small {
  color: #8b8585;
  font-size: 11px;
  line-height: 16px;
  font-weight: 600;
}

.chat-group-member-check {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border: 1px solid rgba(70, 28, 58, 0.16);
  border-radius: 50%;
  background: #fff;
  color: #461c3a;
  font-size: 14px;
  line-height: 1;
  font-weight: 900;
}

.chat-group-create-submit {
  width: 100%;
  height: 48px;
  margin-top: 14px;
  border: 0;
  border-radius: 999px;
  background: #461c3a;
  color: #fff;
  font-size: 14px;
  line-height: 20px;
  font-weight: 900;
  cursor: pointer;
}

.chat-group-create-submit:disabled {
  cursor: default;
  opacity: 0.42;
}


.chat-home-indicator-wrap {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 4;
  display: flex;
  justify-content: center;
  padding: 8px 124px;
}

.chat-home-indicator {
  width: 144px;
  height: 5px;
  border-radius: 100px;
  background: #2a2a2a;
}
</style>
