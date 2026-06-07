<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { getDiscoverCategories, getDiscoverPlaces, type DiscoverPlaceItem } from '../api'
import { resolvePlaceDetail, type PlaceDetail } from '../data/placeDetails'

type Screen = 'discover' | 'createPost' | 'ai1' | 'itinerary' | 'chat' | 'profile'

const emit = defineEmits<{
  navigate: [screen: Screen]
  viewDetail: [payload: { detail: PlaceDetail; poiId?: string | null; returnScreen: 'discover' }]
}>()

type DiscoverCard = {
  id: string
  poiId: string
  title: string
  subtitle?: string
  tags: string[]
  distance: string
  price?: string
  image: string
  layoutClass: string
  footer: 'price' | 'actions'
}

const levelsAsset = '/Levels.svg'
const plusAsset = '/Plus Icon.svg'
const headerSearchAsset = '/Group 59.svg'
const heartOutlineAsset = '/Icon-8.svg'
const heartFilledAsset = '/Icon-5.svg'
const searchAsset = '/MagnifyingGlass.svg'
const userAsset = '/user.svg'
const aiAsset = '/Icon-3.svg'
const tripAsset = '/lucide_map.svg'
const chatAsset = '/ChatTeardrop-dark.svg'
const locationAsset = '/Icon-4.svg'
const cafeStarAsset = '/Item 2_ Cafe/Icon-6.svg'

const cardLayouts = [
  'discover-card-building',
  'discover-card-bread',
  'discover-card-museum',
  'discover-card-park',
  'discover-card-cafe',
]

const cardImages = [
  '/discover-building.png',
  '/discover-bread.png',
  '/discover-museum.png',
  '/discover-park.png',
  '/discover-cafe.png',
]

const categories = ref<string[]>(['全部'])
const selectedCategory = ref('全部')
const discoverCards = ref<DiscoverCard[]>([])
const isLoading = ref(false)
const loadError = ref('')

function buildDiscoverCard(item: DiscoverPlaceItem, index: number): DiscoverCard {
  return {
    id: item.itemId,
    poiId: item.itemId,
    title: item.name,
    subtitle: item.subtitle,
    tags: [item.category, item.badge].filter(Boolean),
    distance: item.subtitle || item.category,
    price: item.badge || '推荐',
    image: cardImages[index % cardImages.length],
    layoutClass: cardLayouts[index % cardLayouts.length],
    footer: 'price',
  }
}

async function loadCategories() {
  const data = await getDiscoverCategories()
  if (data.categories.length) {
    categories.value = data.categories
    if (!data.categories.includes(selectedCategory.value)) {
      selectedCategory.value = data.categories[0]
    }
  }
}

async function loadPlaces() {
  isLoading.value = true
  loadError.value = ''

  try {
    const data = await getDiscoverPlaces(selectedCategory.value)
    discoverCards.value = data.items.slice(0, 5).map((item, index) => buildDiscoverCard(item, index))
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '发现页数据加载失败'
  } finally {
    isLoading.value = false
  }
}

function openCard(card: DiscoverCard) {
  emit('viewDetail', {
    detail: resolvePlaceDetail({
      title: card.title,
      tags: card.tags,
      price: card.price,
    }),
    poiId: card.poiId,
    returnScreen: 'discover',
  })
}

function isActiveCategory(label: string) {
  return label === selectedCategory.value
}

watch(selectedCategory, (nextCategory, previousCategory) => {
  if (nextCategory !== previousCategory) {
    void loadPlaces()
  }
})

onMounted(async () => {
  await loadCategories()
  await loadPlaces()
})
</script>

<template>
  <div class="discover-page">
    <header class="discover-status-bar">
      <div class="discover-time">9:41</div>
      <div class="discover-island"></div>
      <img :src="levelsAsset" alt="" class="discover-levels" />
    </header>

    <button type="button" class="discover-plus-btn" aria-label="新增内容" @click="emit('navigate', 'createPost')">
      <img :src="plusAsset" alt="" />
    </button>

    <button type="button" class="discover-header-search-btn" aria-label="搜索发现内容">
      <img :src="headerSearchAsset" alt="" />
    </button>

    <div class="discover-category-bar">
      <button
        v-for="category in categories"
        :key="category"
        type="button"
        class="discover-category-btn"
        :class="{ 'discover-category-btn-active': isActiveCategory(category) }"
        @click="selectedCategory = category"
      >
        {{ category }}
      </button>

      <button type="button" class="discover-category-more" aria-label="更多分类">
        <img src="/chevron-left.svg" alt="" />
      </button>
    </div>

    <p v-if="isLoading || loadError" :style="{ position: 'absolute', top: '124px', left: '24px', right: '24px', zIndex: '2', margin: '0', color: loadError ? '#8b2f45' : '#6c6868', fontSize: '12px', lineHeight: '18px' }">
      {{ loadError || '正在加载附近灵感...' }}
    </p>

    <section class="discover-scroll" aria-label="发现内容列表">
      <article
        v-for="card in discoverCards"
        :key="card.id"
        class="discover-card"
        :class="card.layoutClass"
        role="button"
        tabindex="0"
        :aria-label="`查看 ${card.title} 详情`"
        style="cursor: pointer;"
        @click="openCard(card)"
        @keyup.enter="openCard(card)"
      >
        <div class="discover-card-media">
          <img :src="card.image" :alt="card.title.replace('\n', '')" class="discover-card-image" />

          <button type="button" class="discover-card-favorite" aria-label="收藏" @click.stop>
            <img :src="heartOutlineAsset" alt="" />
          </button>
        </div>

        <div class="discover-card-body">
          <h3 class="discover-card-title">{{ card.title }}</h3>

          <p v-if="card.subtitle" class="discover-card-subtitle">{{ card.subtitle }}</p>

          <div class="discover-card-tags">
            <span v-for="tag in card.tags" :key="tag" class="discover-card-tag">{{ tag }}</span>
          </div>

          <div class="discover-card-footer">
            <template v-if="card.footer === 'price'">
              <div class="discover-card-distance">
                <img :src="locationAsset" alt="" />
                <span>{{ card.distance }}</span>
              </div>

              <span class="discover-card-price">{{ card.price }}</span>
            </template>

            <template v-else>
              <span class="discover-card-distance-plain">{{ card.distance }}</span>

              <div class="discover-card-actions">
                <img :src="heartFilledAsset" alt="" />
                <img :src="cafeStarAsset" alt="" />
              </div>
            </template>
          </div>
        </div>
      </article>
    </section>

    <nav class="discover-nav" aria-label="底部导航">
      <div class="discover-nav-bg"></div>

      <button
        type="button"
        class="discover-nav-btn discover-nav-btn-muted discover-nav-btn-user"
        aria-label="个人"
        @click="emit('navigate', 'profile')"
      >
        <img :src="userAsset" alt="" class="discover-nav-user-icon" />
      </button>

      <button
        type="button"
        class="discover-nav-btn discover-nav-btn-active discover-nav-btn-search"
        aria-label="发现"
        aria-current="page"
      >
        <img :src="searchAsset" alt="" class="discover-nav-search-icon" />
      </button>

      <button
        type="button"
        class="discover-nav-btn discover-nav-btn-muted discover-nav-btn-ai"
        aria-label="AI"
        @click="emit('navigate', 'ai1')"
      >
        <img :src="aiAsset" alt="" class="discover-nav-ai-icon" />
      </button>

      <button
        type="button"
        class="discover-nav-btn discover-nav-btn-muted discover-nav-btn-trip"
        aria-label="行程"
        @click="emit('navigate', 'itinerary')"
      >
        <img :src="tripAsset" alt="" class="discover-nav-trip-icon" />
      </button>

      <button
        type="button"
        class="discover-nav-btn discover-nav-btn-muted discover-nav-btn-chat"
        aria-label="聊天"
        @click="emit('navigate', 'chat')"
      >
        <img :src="chatAsset" alt="" class="discover-nav-chat-icon" />
      </button>
    </nav>

    <footer class="discover-home-indicator-wrap">
      <div class="discover-home-indicator"></div>
    </footer>
  </div>
</template>

<style scoped>
.discover-page {
  position: relative;
  height: 100%;
  overflow: hidden;
  background:
    radial-gradient(circle at 12% 82%, rgba(245, 214, 228, 0.75) 0, rgba(245, 214, 228, 0) 34%),
    radial-gradient(circle at 72% 95%, rgba(255, 237, 148, 0.8) 0, rgba(255, 237, 148, 0) 26%),
    linear-gradient(180deg, #f9f9f9 0%, #f9f8f7 48%, #f8f2f0 100%);
  font-family: 'SF Pro Rounded', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.discover-status-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 54px;
  background: rgba(255, 255, 255, 0.5);
}

.discover-time {
  width: 138px;
  font-size: 17px;
  font-weight: 600;
  line-height: 22px;
  text-align: center;
  color: #000;
}

.discover-island {
  width: 104px;
  height: 28px;
  border-radius: 999px;
  background: #2a2a2a;
}

.discover-levels {
  width: 143px;
  height: 54px;
  object-fit: contain;
}

.discover-plus-btn,
.discover-header-search-btn,
.discover-category-btn,
.discover-category-more,
.discover-card-favorite,
.discover-floating-search,
.discover-nav-btn {
  border: 0;
  padding: 0;
  cursor: pointer;
}

.discover-plus-btn {
  position: absolute;
  top: 55px;
  left: 7px;
  z-index: 3;
  width: 24px;
  height: 24px;
  background: transparent;
}

.discover-plus-btn img,
.discover-header-search-btn img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.discover-header-search-btn {
  position: absolute;
  top: 55px;
  right: 6px;
  z-index: 3;
  width: 24px;
  height: 24px;
  background: transparent;
}

.discover-category-bar {
  position: absolute;
  top: 86px;
  left: 0;
  right: 0;
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 7px 6px 0 5px;
  border-top: 1px solid rgba(95, 49, 83, 0.08);
}

.discover-category-btn {
  height: 23px;
  background: transparent;
  color: #000;
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
}

.discover-category-btn-active {
  min-width: 54px;
  padding: 0 10px;
  border: 1px solid #000;
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.58);
}

.discover-category-more {
  margin-left: auto;
  width: 16px;
  height: 16px;
  background: transparent;
}

.discover-category-more img {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.discover-scroll {
  position: absolute;
  top: 120px;
  right: 0;
  bottom: 84px;
  left: 0;
  z-index: 2;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.discover-scroll::-webkit-scrollbar {
  display: none;
}

.discover-scroll::after {
  content: '';
  display: block;
  height: 980px;
}

.discover-card {
  position: absolute;
  overflow: hidden;
  border: 1px solid #d8d2bf;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}

.discover-card-building {
  top: 16px;
  left: 4px;
  width: 188px;
  height: 423px;
}

.discover-card-bread {
  top: 16px;
  left: 200px;
  width: 190px;
  height: 274px;
}

.discover-card-museum {
  top: 305px;
  left: 201px;
  width: 189px;
  height: 316px;
}

.discover-card-park {
  top: 450px;
  left: 4px;
  width: 192px;
  height: 237px;
}

.discover-card-cafe {
  top: 635px;
  left: 202px;
  width: 188px;
  height: 321px;
}

.discover-card-media {
  position: relative;
  overflow: hidden;
}

.discover-card-building .discover-card-media {
  height: 317px;
}

.discover-card-bread .discover-card-media {
  height: 160px;
}

.discover-card-museum .discover-card-media {
  height: 224px;
}

.discover-card-park .discover-card-media {
  height: 192px;
}

.discover-card-cafe .discover-card-media {
  height: 200px;
}

.discover-card-image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.discover-card-favorite {
  position: absolute;
  top: 8px;
  right: 8px;
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(238, 235, 237, 0.88);
  backdrop-filter: blur(4px);
}

.discover-card-favorite img {
  width: 16px;
  height: 16px;
}

.discover-card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
}

.discover-card-building .discover-card-body,
.discover-card-park .discover-card-body {
  gap: 7px;
}

.discover-card-title {
  margin: 0;
  color: #1b1c1c;
  font-size: 15px;
  line-height: 20.63px;
  font-weight: 400;
  white-space: pre-line;
}

.discover-card-building .discover-card-title {
  font-size: 16px;
  line-height: 20px;
}

.discover-card-subtitle {
  margin: 0;
  color: #4d4732;
  font-size: 14px;
  line-height: 20px;
}

.discover-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.discover-card-tag {
  padding: 2px 8px;
  border-radius: 4px;
  background: #ebe3fc;
  color: #373737;
  font-size: 10px;
  line-height: 15px;
}

.discover-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 4px;
}

.discover-card-distance {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #7d7d7d;
  font-size: 11px;
  line-height: 16.5px;
}

.discover-card-distance img {
  width: 10px;
  height: 12px;
}

.discover-card-distance-plain,
.discover-card-price {
  color: #000;
  font-size: 12px;
  line-height: 18px;
}

.discover-card-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.discover-card-actions img {
  width: 12px;
  height: 12px;
  object-fit: contain;
}

.discover-nav {
  position: absolute;
  inset: 0;
  z-index: 4;
  pointer-events: none;
}

.discover-nav-bg {
  position: absolute;
  top: 765px;
  left: 33px;
  width: 327px;
  height: 54px;
  border: 1px solid #fff;
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.66);
  pointer-events: auto;
}

.discover-nav-btn {
  position: absolute;
  top: 768px;
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  pointer-events: auto;
}

.discover-nav-btn-muted {
  background: rgba(0, 0, 0, 0.02);
}

.discover-nav-btn-active {
  background: #000;
}

.discover-nav-btn-user {
  left: 41px;
}

.discover-nav-btn-search {
  left: 113px;
}

.discover-nav-btn-ai {
  left: 177px;
}

.discover-nav-btn-trip {
  left: 240px;
}

.discover-nav-btn-chat {
  left: 305px;
}

.discover-nav-user-icon {
  width: 14.4px;
  height: 14.4px;
  filter: brightness(0);
}

.discover-nav-search-icon,
.discover-nav-chat-icon {
  width: 16px;
  height: 16px;
}

.discover-nav-ai-icon,
.discover-nav-trip-icon {
  width: 18px;
  height: 18px;
}

.discover-nav-btn-active .discover-nav-search-icon {
  filter: brightness(0) invert(1);
}


.discover-home-indicator-wrap {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 4;
  display: flex;
  justify-content: center;
  padding: 8px 124px;
}

.discover-home-indicator {
  width: 144px;
  height: 5px;
  border-radius: 100px;
  background: #2c2828;
}
</style>
