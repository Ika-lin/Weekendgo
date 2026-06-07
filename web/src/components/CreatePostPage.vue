<script setup lang="ts">
import { nextTick, onUnmounted, ref } from 'vue'

type Screen = 'discover'

type UploadedImage = {
  id: number
  name: string
  url: string
}

defineEmits<{
  navigate: [screen: Screen]
}>()

const caption = ref('')
const isKeyboardVisible = ref(false)
const isPostSuccessVisible = ref(false)
const captionField = ref<HTMLTextAreaElement | null>(null)
const imagePicker = ref<HTMLInputElement | null>(null)
const uploadedImages = ref<UploadedImage[]>([])
let postSuccessTimer: number | undefined

const keyboardFirstRow = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']
const keyboardSecondRow = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l']
const keyboardThirdRow = ['z', 'x', 'c', 'v', 'b', 'n', 'm']

function focusCaption() {
  captionField.value?.focus()
}

function setCursor(position: number) {
  nextTick(() => {
    const field = captionField.value
    if (!field) return

    field.focus()
    field.setSelectionRange(position, position)
  })
}

function openImagePicker() {
  imagePicker.value?.click()
}

function handleImageSelection(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? []).filter((file) => file.type.startsWith('image/'))

  if (!files.length) {
    input.value = ''
    return
  }

  const nextImages: UploadedImage[] = files.map((file, index) => ({
    id: Date.now() + index,
    name: file.name,
    url: URL.createObjectURL(file),
  }))

  uploadedImages.value.push(...nextImages)
  input.value = ''
}

function removeImage(imageId: number) {
  const index = uploadedImages.value.findIndex((image) => image.id === imageId)
  if (index === -1) return

  const [removedImage] = uploadedImages.value.splice(index, 1)
  URL.revokeObjectURL(removedImage.url)
}

function insertText(text: string) {
  const field = captionField.value
  if (!field) {
    caption.value += text
    return
  }

  const start = field.selectionStart ?? caption.value.length
  const end = field.selectionEnd ?? caption.value.length

  caption.value = `${caption.value.slice(0, start)}${text}${caption.value.slice(end)}`
  setCursor(start + text.length)
}

function deleteBackward() {
  const field = captionField.value
  if (!field) {
    caption.value = caption.value.slice(0, -1)
    return
  }

  const start = field.selectionStart ?? caption.value.length
  const end = field.selectionEnd ?? caption.value.length

  if (start !== end) {
    caption.value = `${caption.value.slice(0, start)}${caption.value.slice(end)}`
    setCursor(start)
    return
  }

  if (start === 0) return

  caption.value = `${caption.value.slice(0, start - 1)}${caption.value.slice(end)}`
  setCursor(start - 1)
}

function handleCaptionFocus() {
  isKeyboardVisible.value = true
}

function handleCaptionBlur() {
  window.setTimeout(() => {
    if (document.activeElement !== captionField.value) {
      isKeyboardVisible.value = false
    }
  }, 0)
}

function hideKeyboard() {
  isKeyboardVisible.value = false
  captionField.value?.blur()
}

function showPostSuccess() {
  if (postSuccessTimer) {
    window.clearTimeout(postSuccessTimer)
  }

  hideKeyboard()
  isPostSuccessVisible.value = true

  postSuccessTimer = window.setTimeout(() => {
    isPostSuccessVisible.value = false
    postSuccessTimer = undefined
  }, 1600)
}

onUnmounted(() => {
  if (postSuccessTimer) {
    window.clearTimeout(postSuccessTimer)
  }

  uploadedImages.value.forEach((image) => URL.revokeObjectURL(image.url))
})

const levelsAsset = '/Levels.svg'
const backAsset = '/icon-park-outline_left.svg'
const plusAsset = '/Plus Icon.svg'
const locationAsset = '/Icon-4.svg'
const trashAsset = '/Trash Icon.svg'
</script>

<template>
  <div class="create-post-page" data-node-id="181:320">
    <header class="create-post-status-bar">
      <div class="create-post-time">9:41</div>
      <div class="create-post-island"></div>
      <img :src="levelsAsset" alt="" class="create-post-levels" />
    </header>

    <div class="create-post-glow create-post-glow-pink"></div>
    <div class="create-post-glow create-post-glow-yellow"></div>

    <div class="create-post-header" data-node-id="181:350">
      <button type="button" class="create-post-circle-btn" aria-label="返回" @click="$emit('navigate', 'discover')">
        <img :src="backAsset" alt="" />
      </button>

      <h1 class="create-post-title">创建帖子</h1>

      <button type="button" class="create-post-circle-btn create-post-info-btn" aria-label="页面说明">
        <span>i</span>
      </button>
    </div>

    <main class="create-post-content" :class="{ 'create-post-content-keyboard': isKeyboardVisible }" data-node-id="181:357">
      <div class="create-post-image-strip" data-node-id="181:497">
        <input
          ref="imagePicker"
          class="create-post-file-input"
          type="file"
          accept="image/*"
          multiple
          @change="handleImageSelection"
        />

        <article
          v-for="image in uploadedImages"
          :key="image.id"
          class="create-post-image-card"
          :aria-label="`已选择图片 ${image.name}`"
        >
          <img :src="image.url" :alt="image.name" class="create-post-image-preview" />

          <button
            type="button"
            class="create-post-image-remove"
            aria-label="删除图片"
            @click="removeImage(image.id)"
          >
            <img :src="trashAsset" alt="" />
          </button>
        </article>

        <button type="button" class="create-post-upload" aria-label="添加本地图片" @click="openImagePicker">
          <img :src="plusAsset" alt="" />
        </button>
      </div>

      <div class="create-post-fields">
        <label class="create-post-caption-box">
          <span class="sr-only">帖子内容</span>
          <textarea
            ref="captionField"
            v-model="caption"
            class="create-post-caption"
            rows="6"
            placeholder="写点什么。。"
            @focus="handleCaptionFocus"
            @blur="handleCaptionBlur"
          ></textarea>
        </label>

        <button type="button" class="create-post-option create-post-option-location" aria-label="添加地点">
          <span class="create-post-option-main">
            <img :src="locationAsset" alt="" class="create-post-location-icon" />
            <span>添加地点</span>
          </span>

          <img :src="backAsset" alt="" class="create-post-option-arrow" />
        </button>

        <button type="button" class="create-post-option" aria-label="增加话题">
          <span class="create-post-option-main">
            <span class="create-post-topic-icon">#</span>
            <span>增加话题</span>
          </span>
        </button>
      </div>
    </main>

    <footer v-if="!isKeyboardVisible" class="create-post-footer" data-node-id="181:373">
      <div class="create-post-sheet-handle"></div>

      <div class="create-post-actions">
        <button type="button" class="create-post-draft-btn">保存草稿</button>
        <button type="button" class="create-post-submit-btn" @click="showPostSuccess">发帖</button>
      </div>

      <div class="create-post-home-indicator-wrap">
        <div class="create-post-home-indicator"></div>
      </div>
    </footer>

    <div v-else class="create-post-page-home-indicator-wrap" aria-hidden="true">
      <div class="create-post-home-indicator"></div>
    </div>

    <div
      v-if="isPostSuccessVisible"
      class="create-post-success-overlay"
      role="status"
      aria-live="polite"
      aria-label="发帖成功"
    >
      <div class="create-post-success-card">
        <div class="create-post-success-icon">
          <span class="create-post-success-tick"></span>
        </div>

        <p class="create-post-success-text">已发帖</p>
      </div>
    </div>


    <section
      v-if="isKeyboardVisible"
      class="create-post-keyboard"
      data-node-id="218:1592"
      aria-label="设计态键盘"
    >
      <div class="create-post-keyboard-toolbar">
        <button type="button" class="create-post-keyboard-toolbar-back" aria-label="收起键盘" @mousedown.prevent="hideKeyboard">
          <img :src="backAsset" alt="" />
        </button>

        <button type="button" class="create-post-keyboard-toolbar-text" @mousedown.prevent>GIF</button>
        <button type="button" class="create-post-keyboard-toolbar-icon" aria-label="设置" @mousedown.prevent>
          <span>⚙</span>
        </button>
        <button type="button" class="create-post-keyboard-toolbar-translate" aria-label="翻译输入" @mousedown.prevent>
          <span>Gx</span>
        </button>
        <button type="button" class="create-post-keyboard-toolbar-icon" aria-label="表情贴纸" @mousedown.prevent>
          <span>☺</span>
        </button>
        <span class="create-post-keyboard-toolbar-divider" aria-hidden="true"></span>
        <button type="button" class="create-post-keyboard-toolbar-icon" aria-label="更多" @mousedown.prevent>
          <span>⋯</span>
        </button>
        <button type="button" class="create-post-keyboard-toolbar-icon" aria-label="语音输入" @mousedown.prevent>
          <span>🎤</span>
        </button>
      </div>

      <div class="create-post-keyboard-rows">
        <div class="create-post-keyboard-row">
          <button
            v-for="key in keyboardFirstRow"
            :key="key"
            type="button"
            class="create-post-keyboard-key"
            @mousedown.prevent
            @click="insertText(key)"
          >
            {{ key }}
          </button>
        </div>

        <div class="create-post-keyboard-row create-post-keyboard-row-middle">
          <button
            v-for="key in keyboardSecondRow"
            :key="key"
            type="button"
            class="create-post-keyboard-key"
            @mousedown.prevent
            @click="insertText(key)"
          >
            {{ key }}
          </button>
        </div>

        <div class="create-post-keyboard-row">
          <button type="button" class="create-post-keyboard-key create-post-keyboard-key-side" aria-label="大写" @mousedown.prevent="focusCaption">
            ⇧
          </button>

          <button
            v-for="key in keyboardThirdRow"
            :key="key"
            type="button"
            class="create-post-keyboard-key"
            @mousedown.prevent
            @click="insertText(key)"
          >
            {{ key }}
          </button>

          <button type="button" class="create-post-keyboard-key create-post-keyboard-key-side" aria-label="删除" @mousedown.prevent @click="deleteBackward">
            ⌫
          </button>
        </div>

        <div class="create-post-keyboard-row create-post-keyboard-row-bottom">
          <button type="button" class="create-post-keyboard-key create-post-keyboard-key-mode" @mousedown.prevent="focusCaption">?123</button>
          <button type="button" class="create-post-keyboard-key create-post-keyboard-key-icon" @mousedown.prevent="focusCaption">☺</button>
          <button type="button" class="create-post-keyboard-key create-post-keyboard-key-icon" @mousedown.prevent="focusCaption">◎</button>
          <button type="button" class="create-post-keyboard-key create-post-keyboard-key-space" @mousedown.prevent @click="insertText(' ')"></button>
          <button type="button" class="create-post-keyboard-key create-post-keyboard-key-dot" @mousedown.prevent @click="insertText('.')">.</button>
          <button type="button" class="create-post-keyboard-key create-post-keyboard-key-enter" @mousedown.prevent @click="insertText('\n')">
            ↵
          </button>
        </div>
      </div>

      <div class="create-post-keyboard-bottom-nav">
        <button type="button" class="create-post-keyboard-bottom-btn" aria-label="收起键盘" @mousedown.prevent="hideKeyboard">⌄</button>
        <button type="button" class="create-post-keyboard-bottom-btn" aria-label="键盘设置" @mousedown.prevent="focusCaption">⌨</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.create-post-page {
  position: relative;
  height: 100%;
  overflow: hidden;
  background: linear-gradient(180deg, #fafafa 0%, #f8f3f4 62%, #f6f1eb 100%);
  font-family: 'SF Pro Rounded', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.create-post-glow {
  position: absolute;
  border-radius: 999px;
  filter: blur(44px);
  pointer-events: none;
}

.create-post-glow-pink {
  left: -66px;
  bottom: 154px;
  width: 248px;
  height: 248px;
  background: rgba(245, 189, 205, 0.64);
}

.create-post-glow-yellow {
  right: -44px;
  bottom: 122px;
  width: 228px;
  height: 246px;
  background: rgba(255, 241, 153, 0.72);
}

.create-post-status-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 54px;
}

.create-post-time {
  width: 138px;
  font-size: 17px;
  font-weight: 600;
  line-height: 22px;
  text-align: center;
  color: #000;
}

.create-post-island {
  width: 104px;
  height: 28px;
  border-radius: 999px;
  background: #2a2a2a;
}

.create-post-levels {
  width: 143px;
  height: 54px;
  object-fit: cover;
}

.create-post-header {
  position: absolute;
  top: 58px;
  left: 16px;
  right: 16px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.create-post-circle-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  border: 1px solid #f3f3f3;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 10px 18px rgba(255, 255, 255, 0.28);
}

.create-post-circle-btn img {
  width: 16px;
  height: 16px;
}

.create-post-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  line-height: 24px;
  color: #1e1e1e;
}

.create-post-info-btn span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: 1.5px solid #1e1e1e;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  color: #1e1e1e;
}

.create-post-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 122px 16px 240px;
}

.create-post-content-keyboard {
  padding-bottom: 346px;
}

.create-post-image-strip {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 2px;
  scrollbar-width: none;
}

.create-post-image-strip::-webkit-scrollbar {
  display: none;
}

.create-post-file-input {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  border: 0;
  clip: rect(0, 0, 0, 0);
}

.create-post-image-card,
.create-post-upload {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 96px;
  width: 96px;
  height: 96px;
  padding: 0;
  border: 1px dashed #b0b0b0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
  overflow: hidden;
}

.create-post-image-card {
  border-style: solid;
}

.create-post-upload img {
  width: 32px;
  height: 32px;
}

.create-post-image-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.create-post-image-remove {
  position: absolute;
  top: 7px;
  right: 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: 1px solid #f0f0f0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.04);
}

.create-post-image-remove img {
  width: 16px;
  height: 16px;
}

.create-post-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.create-post-caption-box {
  display: block;
  height: 150px;
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.97);
}

.create-post-caption {
  width: 100%;
  height: 100%;
  padding: 0;
  border: 0;
  background: transparent;
  resize: none;
  font: inherit;
  font-size: 14px;
  line-height: 1.7;
  color: #1e1e1e;
}

.create-post-caption::placeholder {
  color: #b0b0b0;
}

.create-post-caption:focus {
  outline: none;
}

.create-post-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 50px;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.97);
  color: #6e6e6e;
}

.create-post-option-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  line-height: 18px;
}

.create-post-location-icon {
  width: 10px;
  height: 12px;
}

.create-post-option-arrow {
  width: 16px;
  height: 16px;
  transform: rotate(180deg);
}

.create-post-topic-icon {
  font-size: 18px;
  line-height: 1;
  color: #6e6e6e;
}

.create-post-footer {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 8px 16px 0;
  border-radius: 24px 24px 0 0;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 1px 10px rgba(0, 0, 0, 0.05);
}

.create-post-page-home-indicator-wrap {
  position: absolute;
  right: 0;
  bottom: 8px;
  left: 0;
  z-index: 5;
  display: flex;
  justify-content: center;
}

.create-post-success-overlay {
  position: absolute;
  inset: 0;
  z-index: 6;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
}

.create-post-success-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  width: 200px;
  padding: 24px;
  border: 1px solid #f0f0f0;
  border-radius: 24px;
  background: #fff;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.04);
}

.create-post-success-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 999px;
  background: #461c3a;
}

.create-post-success-tick {
  width: 24px;
  height: 14px;
  border-bottom: 5px solid #fff;
  border-left: 5px solid #fff;
  transform: rotate(-45deg) translateY(-2px);
}

.create-post-success-text {
  margin: 0;
  font-size: 16px;
  line-height: 1.7;
  color: #000;
}

.create-post-sheet-handle {
  width: 40px;
  height: 5px;
  border-radius: 999px;
  background: #dedede;
}

.create-post-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.create-post-draft-btn,
.create-post-submit-btn {
  width: 100%;
  min-height: 48px;
  border-radius: 999px;
  font-family: inherit;
}

.create-post-draft-btn {
  border: 1px solid #f0f0f0;
  background: #fff;
  font-size: 14px;
  font-weight: 500;
  color: #0b0b0b;
}

.create-post-submit-btn {
  border: 0;
  background: #461c3a;
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.create-post-home-indicator-wrap {
  display: flex;
  justify-content: center;
  width: 100%;
  padding: 8px 0;
}

.create-post-home-indicator {
  width: 144px;
  height: 5px;
  border-radius: 999px;
  background: #2c2828;
}

.create-post-keyboard {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 4;
  display: flex;
  flex-direction: column;
  height: 322px;
  padding: 10px 7px 34px;
  border-top: 1px solid #eee;
  background: #fef7ff;
}

.create-post-keyboard-toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 10px 10px 6px;
  color: #1d1b20;
}

.create-post-keyboard-toolbar button {
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
}

.create-post-keyboard-toolbar-back {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  background: #e8def8 !important;
}

.create-post-keyboard-toolbar-back img {
  width: 16px;
  height: 16px;
}

.create-post-keyboard-toolbar-text {
  font-size: 17px;
  font-weight: 700;
  line-height: 1;
}

.create-post-keyboard-toolbar-icon,
.create-post-keyboard-toolbar-translate {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  font-size: 19px;
  line-height: 1;
}

.create-post-keyboard-toolbar-translate {
  font-size: 15px;
  font-weight: 700;
}

.create-post-keyboard-toolbar-divider {
  width: 1px;
  height: 24px;
  margin-left: 2px;
  background: #cac4d0;
}

.create-post-keyboard-rows {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 11px;
}

.create-post-keyboard-row {
  display: flex;
  gap: 6px;
}

.create-post-keyboard-row-middle {
  padding: 0 19px;
}

.create-post-keyboard-row-bottom {
  align-items: stretch;
}

.create-post-keyboard-key {
  display: inline-flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  height: 44px;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: #f7f2fa;
  box-shadow: inset 0 -1px 0 rgba(0, 0, 0, 0.08);
  font-size: 20px;
  font-weight: 400;
  line-height: 1;
  color: #1d1b20;
  text-transform: lowercase;
}

.create-post-keyboard-key-side,
.create-post-keyboard-key-mode,
.create-post-keyboard-key-icon {
  flex: 0 0 auto;
  background: #e6e0e9;
}

.create-post-keyboard-key-side {
  width: 52px;
  font-size: 22px;
}

.create-post-keyboard-key-mode {
  width: 70px;
  font-size: 17px;
}

.create-post-keyboard-key-icon,
.create-post-keyboard-key-dot {
  width: 44px;
  font-size: 18px;
}

.create-post-keyboard-key-space {
  background: #f7f2fa;
}

.create-post-keyboard-key-enter {
  flex: 0 0 auto;
  width: 70px;
  background: #d0bcff;
  font-size: 24px;
  color: #4f378a;
}

.create-post-keyboard-bottom-nav {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 18px 9px;
}

.create-post-keyboard-bottom-btn {
  padding: 0;
  border: 0;
  background: transparent;
  font-size: 22px;
  line-height: 1;
  color: #49454f;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>