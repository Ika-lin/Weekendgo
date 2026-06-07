<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { getPoiArrivalHints, getPoiDetail, getPoiReviewInsights, type PoiArrivalHintsPayload, type PoiDetailPayload, type PoiReviewInsightsPayload } from '../api'
import type { PlaceDetail, PlaceReview } from '../data/placeDetails'

const props = defineProps<{
  detail: PlaceDetail
  poiId?: string | null
}>()

const emit = defineEmits<{
  back: []
}>()

const levelsAsset = '/Levels.svg'
const topBackAsset = '/place-detail/back.svg'
const heroChevronAsset = '/place-detail/chevron-light.svg'
const shareAsset = '/place-detail/share.svg'
const mapPinAsset = '/place-detail/map-pin.svg'
const groupAsset = '/place-detail/group-121.svg'
const clockAsset = '/place-detail/clock.svg'
const userAsset = '/place-detail/user.svg'
const starAsset = '/place-detail/star.svg'
const starOutlineAsset = '/place-detail/star-outline.svg'
const mapAsset = '/place-detail/map.svg'
const likeAsset = '/place-detail/like.svg'
const dislikeAsset = '/place-detail/dislike.svg'
const loadMoreAsset = '/place-detail/load-more.svg'
const bulletAsset = '/place-detail/bullet.svg'
const dividerAsset = '/place-detail/divider.svg'

const paginationDots = Array.from({ length: 9 }, (_, index) => index)
const activeDotIndex = 1

const detailVisualsByTitle = {
  'FILM电影时光书店': {
    heroLayers: ['/place-detail/hero-base.png', '/place-detail/hero-overlay.png'],
    reviewAvatarLayers: [
      ['/place-detail/reviewer-1-bg.png', '/place-detail/reviewer-1.png'],
      ['/place-detail/reviewer-2.png'],
      ['/place-detail/reviewer-3.png', '/place-detail/reviewer-3-overlay.png'],
    ],
  },
} as const

const poiDetail = ref<PoiDetailPayload | null>(null)
const reviewInsights = ref<PoiReviewInsightsPayload | null>(null)
const arrivalHints = ref<PoiArrivalHintsPayload | null>(null)
const isRemoteLoading = ref(false)
const remoteLoadError = ref('')

function formatBusinessStatus(status: string | undefined) {
  if (status === 'open') return '营业中'
  if (status === 'closed') return '已打烊'
  if (status === 'temporary_closed') return '暂停营业'
  return status || '营业中'
}

function formatPriceText(pricePerCapita: number | undefined) {
  if (!pricePerCapita || pricePerCapita <= 0) {
    return '免费'
  }

  return `人均 ¥${pricePerCapita}`
}

function buildRemoteReviews(): PlaceReview[] {
  if (!reviewInsights.value) {
    return props.detail.reviews
  }

  const ratingValue = Math.max(1, Math.min(5, Math.round(reviewInsights.value.rating || 4)))
  const reviewCards: PlaceReview[] = []
  const palette = ['#e9d8cf', '#d9e4f5', '#f0dfc8']

  if (reviewInsights.value.sampleQuote) {
    reviewCards.push({
      id: 'remote-review-quote',
      name: '近期评论',
      time: '实时同步',
      text: reviewInsights.value.sampleQuote,
      rating: ratingValue,
      likes: 128,
      dislikes: 3,
      avatarBg: palette[0],
    })
  }

  if (reviewInsights.value.highlights?.length) {
    reviewCards.push({
      id: 'remote-review-highlights',
      name: '高频亮点',
      time: '评论聚合',
      text: reviewInsights.value.highlights.join('；'),
      rating: ratingValue,
      likes: 96,
      dislikes: 2,
      avatarBg: palette[1],
    })
  }

  if (reviewInsights.value.riskNotes?.length) {
    reviewCards.push({
      id: 'remote-review-risk',
      name: '避坑提示',
      time: '评论聚合',
      text: reviewInsights.value.riskNotes.join('；'),
      rating: Math.max(3, ratingValue - 1),
      likes: 67,
      dislikes: 1,
      avatarBg: palette[2],
    })
  }

  return reviewCards.length ? reviewCards : props.detail.reviews
}

function buildRemoteReminders() {
  if (!poiDetail.value) {
    return props.detail.reminders
  }

  const nextReminders = [
    arrivalHints.value?.bestArrivalWindow ? `建议到达：${arrivalHints.value.bestArrivalWindow}` : '',
    arrivalHints.value?.trafficNote || '',
    arrivalHints.value?.weatherImpact || '',
    ...(poiDetail.value.attention || []),
  ].filter((item): item is string => typeof item === 'string' && item.trim().length > 0)

  return nextReminders.length ? nextReminders : props.detail.reminders
}

const displayDetail = computed<PlaceDetail>(() => {
  if (!poiDetail.value) {
    return props.detail
  }

  const ratingValue = Number(poiDetail.value.rating || 0)
  const ratingCount = reviewInsights.value?.reviewCount || poiDetail.value.reviewCount || Number(props.detail.ratingCount) || 0
  const reminderNote = [
    arrivalHints.value?.queueRisk ? `排队风险：${arrivalHints.value.queueRisk}` : '',
    arrivalHints.value?.weatherImpact || '',
    reviewInsights.value?.riskNotes?.[0] || '',
  ].filter(Boolean).join('；')

  return {
    ...props.detail,
    title: poiDetail.value.name || props.detail.title,
    address: poiDetail.value.address || props.detail.address,
    hours: poiDetail.value.openHoursText || props.detail.hours,
    status: formatBusinessStatus(poiDetail.value.businessStatus),
    description: poiDetail.value.about || props.detail.description,
    price: formatPriceText(poiDetail.value.pricePerCapita),
    rating: ratingValue ? ratingValue.toFixed(1) : props.detail.rating,
    ratingCount: String(ratingCount || props.detail.ratingCount),
    heroWordmark: poiDetail.value.name || props.detail.heroWordmark,
    heroCaption: poiDetail.value.category || props.detail.heroCaption,
    heroMarquee: poiDetail.value.impressionTags?.[0] || poiDetail.value.tags?.[0] || poiDetail.value.category || props.detail.heroMarquee,
    reviews: buildRemoteReviews(),
    reminders: buildRemoteReminders(),
    reminderNote: reminderNote || props.detail.reminderNote,
  }
})

const pageVisuals = computed(() => detailVisualsByTitle[displayDetail.value.title as keyof typeof detailVisualsByTitle] ?? null)

function getAvatarLabel(name: string) {
  return name.slice(0, 1)
}

function getReviewAvatarLayers(index: number) {
  return pageVisuals.value?.reviewAvatarLayers[index] ?? []
}

function getDisplayStars(rating: number) {
  return Array.from({ length: 5 }, (_, index) => index < rating)
}

function getStarIcon(filled: boolean) {
  return filled ? starAsset : starOutlineAsset
}

watch(
  () => props.poiId,
  async (poiId) => {
    poiDetail.value = null
    reviewInsights.value = null
    arrivalHints.value = null
    remoteLoadError.value = ''

    if (!poiId) {
      return
    }

    isRemoteLoading.value = true

    const [detailResult, reviewResult, arrivalResult] = await Promise.allSettled([
      getPoiDetail(poiId),
      getPoiReviewInsights(poiId),
      getPoiArrivalHints(poiId),
    ])

    if (detailResult.status === 'fulfilled') {
      poiDetail.value = detailResult.value
    } else {
      remoteLoadError.value = detailResult.reason instanceof Error ? detailResult.reason.message : '地点详情同步失败'
    }

    if (reviewResult.status === 'fulfilled') {
      reviewInsights.value = reviewResult.value
    }

    if (arrivalResult.status === 'fulfilled') {
      arrivalHints.value = arrivalResult.value
    }

    isRemoteLoading.value = false
  },
  { immediate: true },
)
</script>

<template>
  <div class="place-detail-page">
    <div class="place-detail-scroll">
      <div class="place-detail-canvas">
        <section class="place-detail-hero">
          <div class="place-detail-hero-media">
            <template v-if="pageVisuals">
              <img :src="pageVisuals.heroLayers[0]" alt="" class="place-detail-hero-image" />
              <img :src="pageVisuals.heroLayers[1]" alt="" class="place-detail-hero-image" />
              <div class="place-detail-hero-wash"></div>
            </template>
            <div v-else class="place-detail-hero-fallback" :style="{ background: displayDetail.heroBackground }"></div>
          </div>

          <div class="place-detail-dots" aria-hidden="true">
            <span
              v-for="dot in paginationDots"
              :key="dot"
              class="place-detail-dot"
              :class="{ 'place-detail-dot-active': dot === activeDotIndex }"
            ></span>
          </div>

          <div class="place-detail-hero-nav-wrap">
            <button type="button" class="place-detail-hero-nav place-detail-hero-nav-left" aria-label="上一张">
              <img :src="heroChevronAsset" alt="" />
            </button>

            <button type="button" class="place-detail-hero-nav place-detail-hero-nav-right" aria-label="下一张">
              <img :src="heroChevronAsset" alt="" />
            </button>
          </div>
        </section>

        <header class="place-detail-status-bar">
          <div class="place-detail-time">9:41</div>
          <div class="place-detail-island"></div>
          <img :src="levelsAsset" alt="" class="place-detail-levels" />
        </header>

        <div class="place-detail-top-actions">
          <button type="button" class="place-detail-top-btn" aria-label="返回" @click="emit('back')">
            <img :src="topBackAsset" alt="" />
          </button>

          <button type="button" class="place-detail-top-btn" aria-label="分享">
            <img :src="shareAsset" alt="" />
          </button>
        </div>

        <section class="place-detail-content">
          <div class="place-detail-info-card">
            <div class="place-detail-heading-row">
              <div class="place-detail-heading-copy">
                <h2 class="place-detail-title">{{ displayDetail.title }}</h2>

                <p class="place-detail-address">
                  <img :src="mapPinAsset" alt="" />
                  <span>{{ displayDetail.address }}</span>
                </p>
              </div>

              <img :src="groupAsset" alt="" class="place-detail-heading-actions" />
            </div>

            <div class="place-detail-meta-row">
              <div class="place-detail-meta-pill place-detail-meta-pill-hours">
                <img :src="clockAsset" alt="" />
                <span>{{ displayDetail.hours }}</span>
              </div>

              <div class="place-detail-meta-pill place-detail-meta-pill-status">
                <img :src="userAsset" alt="" />
                <span>{{ displayDetail.status }}</span>
              </div>
            </div>

            <p class="place-detail-description">{{ displayDetail.description }}</p>

            <div class="place-detail-rating-row">
              <p class="place-detail-price">{{ displayDetail.price }}</p>

              <div class="place-detail-rating">
                <img :src="starAsset" alt="" />
                <span>{{ displayDetail.rating }} ({{ displayDetail.ratingCount }})</span>
              </div>
            </div>

            <p v-if="isRemoteLoading || remoteLoadError" :style="{ margin: '12px 0 0', color: remoteLoadError ? '#8b2f45' : '#6c6868', fontSize: '12px', lineHeight: '18px' }">
              {{ remoteLoadError || '正在同步地点信息...' }}
            </p>

            <div class="place-detail-cta-row">
              <button type="button" class="place-detail-cta place-detail-cta-dark">加入收藏</button>
              <button type="button" class="place-detail-cta place-detail-cta-gold">美团团购</button>

              <button type="button" class="place-detail-map-btn" aria-label="查看地图">
                <img :src="mapAsset" alt="" />
              </button>
            </div>
          </div>

          <section class="place-detail-reviews">
            <h3 class="place-detail-section-title">评价</h3>

            <div class="place-detail-review-list">
              <article
                v-for="(review, index) in displayDetail.reviews.slice(0, 3)"
                :key="review.id"
                class="place-detail-review-card"
                :class="index === 0 ? 'place-detail-review-card-compact' : 'place-detail-review-card-tall'"
              >
                <div class="place-detail-review-header">
                  <div class="place-detail-reviewer">
                    <div class="place-detail-avatar-frame">
                      <template v-if="getReviewAvatarLayers(index).length">
                        <img
                          v-for="layer in getReviewAvatarLayers(index)"
                          :key="layer"
                          :src="layer"
                          alt=""
                          class="place-detail-avatar-layer"
                        />
                      </template>

                      <div v-else class="place-detail-avatar-fallback" :style="{ background: review.avatarBg }">
                        {{ getAvatarLabel(review.name) }}
                      </div>
                    </div>

                    <div class="place-detail-reviewer-copy">
                      <p class="place-detail-reviewer-name">{{ review.name }}</p>
                      <p class="place-detail-reviewer-time">{{ review.time }}</p>
                    </div>
                  </div>

                  <div class="place-detail-stars">
                    <img
                      v-for="(filled, starIndex) in getDisplayStars(review.rating)"
                      :key="`${review.id}-${starIndex}`"
                      :src="getStarIcon(filled)"
                      alt=""
                    />
                  </div>
                </div>

                <p class="place-detail-review-text" :class="index === 0 ? 'place-detail-review-text-compact' : 'place-detail-review-text-tall'">
                  {{ review.text }}
                </p>

                <div class="place-detail-review-actions">
                  <div class="place-detail-review-action">
                    <img :src="likeAsset" alt="" />
                    <span>{{ review.likes }}</span>
                  </div>

                  <div class="place-detail-review-action">
                    <img :src="dislikeAsset" alt="" />
                    <span>{{ review.dislikes }}</span>
                  </div>
                </div>
              </article>
            </div>

            <button type="button" class="place-detail-load-more">
              <img :src="loadMoreAsset" alt="" class="place-detail-load-more-icon" />
              <span>Load More</span>
            </button>
          </section>
        </section>

        <footer class="place-detail-home-indicator">
          <div class="place-detail-home-indicator-bar"></div>
        </footer>

        <section class="place-detail-reminder-section">
          <h3 class="place-detail-reminder-title">到店前提醒</h3>

          <img :src="dividerAsset" alt="" class="place-detail-reminder-divider place-detail-reminder-divider-left" />
          <img :src="dividerAsset" alt="" class="place-detail-reminder-divider place-detail-reminder-divider-right" />

          <div class="place-detail-reminder-listing">
            <div v-for="item in displayDetail.reminders.slice(0, 3)" :key="item" class="place-detail-reminder-item">
              <img :src="bulletAsset" alt="" class="place-detail-reminder-bullet" />
              <span>{{ item }}</span>
            </div>
          </div>

          <p class="place-detail-reminder-note">{{ displayDetail.reminderNote }}</p>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.place-detail-page {
  position: relative;
  height: 100%;
  overflow: hidden;
  background: #ffffff;
  border-radius: 40px;
  font-family: 'SF Pro Rounded', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.place-detail-scroll {
  height: 100%;
  overflow-y: auto;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.place-detail-scroll::-webkit-scrollbar {
  display: none;
}

.place-detail-canvas {
  position: relative;
  width: 100%;
  min-height: 1525px;
  background: #ffffff;
}

.place-detail-hero {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 398px;
  overflow: hidden;
  background: #ffffff;
}

.place-detail-hero-media {
  position: absolute;
  top: 0;
  left: 50%;
  width: 597px;
  height: 398px;
  transform: translateX(-50%);
}

.place-detail-hero-image,
.place-detail-hero-fallback,
.place-detail-hero-wash {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.place-detail-hero-image {
  display: block;
  object-fit: cover;
}

.place-detail-hero-wash {
  background: rgba(255, 255, 255, 0.1);
}

.place-detail-hero-nav-wrap {
  position: absolute;
  top: 183px;
  left: 16px;
  right: 16px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.place-detail-hero-nav {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0.5px solid rgba(255, 255, 255, 0.2);
  border-radius: 100px;
  background: rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(2px);
}

.place-detail-hero-nav img {
  width: 16px;
  height: 16px;
  display: block;
}

.place-detail-hero-nav-right img {
  transform: scaleX(-1);
}

.place-detail-dots {
  position: absolute;
  left: 50%;
  bottom: 8px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 4px;
  transform: translateX(calc(-50% + 0.5px));
}

.place-detail-dot {
  width: 6px;
  height: 6px;
  border-radius: 100px;
  background: #b2b2b2;
  backdrop-filter: blur(2px);
}

.place-detail-dot-active {
  width: 8px;
  height: 8px;
  background: #ffffff;
}

.place-detail-status-bar {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 54px;
}

.place-detail-time {
  width: 138px;
  color: #111111;
  text-align: center;
  font-family: 'SF Pro', 'PingFang SC', sans-serif;
  font-size: 17px;
  font-weight: 590;
  line-height: 22px;
  letter-spacing: -0.03em;
}

.place-detail-island {
  width: 104px;
  height: 28px;
  border-radius: 10000px;
  background: #2c2828;
}

.place-detail-levels {
  width: 143px;
  height: 54px;
  object-fit: contain;
}

.place-detail-top-actions {
  position: absolute;
  top: 58px;
  left: 16px;
  right: 16px;
  z-index: 5;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.place-detail-top-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  border: 1px solid #f3f3f3;
  border-radius: 1000px;
  background: #ffffff;
}

.place-detail-top-btn img {
  width: 16px;
  height: 16px;
  display: block;
}

.place-detail-content {
  position: absolute;
  top: 414px;
  left: 16px;
  width: 361px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.place-detail-info-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 361px;
}

.place-detail-heading-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  width: 361px;
  min-height: 48px;
}

.place-detail-heading-copy {
  width: 262px;
}

.place-detail-title,
.place-detail-address,
.place-detail-description,
.place-detail-price,
.place-detail-rating span,
.place-detail-reviewer-name,
.place-detail-reviewer-time,
.place-detail-review-text,
.place-detail-review-action span,
.place-detail-load-more span,
.place-detail-reminder-title,
.place-detail-reminder-note,
.place-detail-reminder-item span,
.place-detail-section-title {
  margin: 0;
}

.place-detail-title {
  width: 262px;
  color: #000000;
  font-size: 16px;
  font-weight: 500;
  line-height: 22px;
}

.place-detail-address {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  width: 262px;
}

.place-detail-address img {
  width: 12px;
  height: 12px;
  display: block;
}

.place-detail-address span {
  flex: 1;
  min-width: 0;
  color: #999999;
  font-size: 12px;
  font-weight: 400;
  line-height: 18px;
}

.place-detail-heading-actions {
  width: 98px;
  height: 28px;
  display: block;
  flex-shrink: 0;
}

.place-detail-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 262px;
}

.place-detail-meta-pill {
  height: 34px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border: 1px solid #f7f7f7;
  border-radius: 1000px;
  background: #f7f7f7;
  color: #b0b0b0;
  font-size: 12px;
  font-weight: 400;
  line-height: 18px;
  white-space: nowrap;
}

.place-detail-meta-pill-hours {
  width: 178px;
}

.place-detail-meta-pill-status {
  width: 76px;
}

.place-detail-meta-pill img {
  width: 12px;
  height: 12px;
  display: block;
  flex-shrink: 0;
}

.place-detail-description {
  width: 357px;
  color: #1e1e1e;
  font-size: 14px;
  font-weight: 400;
  line-height: 170%;
}

.place-detail-rating-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  width: 361px;
}

.place-detail-price {
  color: #000000;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', sans-serif;
  font-size: 11.4601px;
  font-weight: 400;
  line-height: 13px;
}

.place-detail-rating {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.place-detail-rating img {
  width: 14px;
  height: 14px;
  display: block;
}

.place-detail-rating span {
  color: #999999;
  font-size: 12px;
  font-weight: 500;
  line-height: 18px;
}

.place-detail-cta-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  width: 361px;
}

.place-detail-cta {
  width: 153px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  border: 0;
  border-radius: 166.667px;
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
}

.place-detail-cta-dark {
  background: #0b0b0b;
  color: #ffffff;
}

.place-detail-cta-gold {
  background: #ffc300;
  color: #000000;
}

.place-detail-map-btn {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
  border: 1px solid #f0f0f0;
  border-radius: 1100px;
  background: #ffffff;
}

.place-detail-map-btn img {
  width: 18px;
  height: 18px;
  display: block;
}

.place-detail-reviews {
  width: 361px;
}

.place-detail-section-title {
  width: 361px;
  color: rgba(44, 40, 40, 0.7);
  font-size: 18px;
  font-weight: 500;
  line-height: 21px;
  letter-spacing: -0.01em;
}

.place-detail-review-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 8px;
}

.place-detail-review-card {
  width: 361px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px;
  border: 1px solid #eeeeee;
  border-radius: 24px;
  background: #ffffff;
}

.place-detail-review-card-compact {
  min-height: 162px;
}

.place-detail-review-card-tall {
  min-height: 186px;
}

.place-detail-review-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 345px;
}

.place-detail-reviewer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.place-detail-avatar-frame {
  position: relative;
  width: 40px;
  height: 40px;
  overflow: hidden;
  border: 1px solid #f3f3f3;
  border-radius: 1000px;
  background: #ffffff;
  flex-shrink: 0;
}

.place-detail-avatar-layer {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.place-detail-avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2c2828;
  font-size: 16px;
  font-weight: 500;
  line-height: 22px;
}

.place-detail-reviewer-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.place-detail-reviewer-name {
  color: #2c2828;
  font-size: 16px;
  font-weight: 500;
  line-height: 22px;
}

.place-detail-reviewer-time {
  color: #999999;
  font-size: 12px;
  font-weight: 400;
  line-height: 18px;
}

.place-detail-stars {
  display: inline-flex;
  align-items: center;
  gap: 2px;
}

.place-detail-stars img {
  width: 14px;
  height: 14px;
  display: block;
}

.place-detail-review-text {
  width: 345px;
  color: #1e1e1e;
  font-size: 14px;
  font-weight: 400;
  line-height: 170%;
}

.place-detail-review-text-compact {
  min-height: 48px;
}

.place-detail-review-text-tall {
  min-height: 72px;
}

.place-detail-review-actions {
  width: 124px;
  display: inline-flex;
  align-items: flex-start;
  gap: 16px;
  margin-top: auto;
  padding: 8px 16px;
  border-radius: 1000px;
  background: #fafafa;
}

.place-detail-review-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.place-detail-review-action img {
  width: 16px;
  height: 16px;
  display: block;
}

.place-detail-review-action span {
  color: #1e1e1e;
  font-size: 12px;
  font-weight: 400;
  line-height: 18px;
}

.place-detail-load-more {
  width: 361px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 16px;
  padding: 10px 12px;
  border: 0;
  border-radius: 166.667px;
  background: #fafafa;
}

.place-detail-load-more-icon {
  width: 14px;
  height: 14px;
  display: block;
}

.place-detail-load-more span {
  color: #1e1e1e;
  font-size: 14px;
  font-weight: 400;
  line-height: 24px;
}

.place-detail-home-indicator {
  position: absolute;
  top: 832px;
  left: 0;
  width: 100%;
  height: 21px;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 8px 124px;
}

.place-detail-home-indicator-bar {
  width: 144px;
  height: 5px;
  border-radius: 100px;
  background: #2c2828;
}

.place-detail-reminder-section {
  position: absolute;
  top: 1353px;
  left: 16px;
  width: 361px;
  min-height: 148px;
}

.place-detail-reminder-title {
  color: #6c6868;
  font-size: 18px;
  font-weight: 500;
  line-height: 21px;
  letter-spacing: -0.01em;
}

.place-detail-reminder-divider {
  position: absolute;
  top: 36px;
  width: 1px;
  height: 112px;
  display: block;
}

.place-detail-reminder-divider-left {
  left: 0;
}

.place-detail-reminder-divider-right {
  left: 181px;
}

.place-detail-reminder-listing {
  position: absolute;
  top: 41px;
  left: 8px;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.place-detail-reminder-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.place-detail-reminder-bullet {
  width: 4px;
  height: 4px;
  display: block;
  flex-shrink: 0;
}

.place-detail-reminder-item span {
  color: #565656;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', sans-serif;
  font-size: 13px;
  font-weight: 400;
  line-height: 15px;
}

.place-detail-reminder-note {
  position: absolute;
  top: 52px;
  left: 194px;
  width: 161px;
  color: #565656;
  font-family: 'FZLanTingHeiS-DB-GB', 'PingFang SC', sans-serif;
  font-size: 12px;
  font-weight: 400;
  line-height: 14px;
}
</style>