<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getSettings, updateLLMSettings, getDocuments, getSystemStatus, deleteDocument, uploadDocument, getModels } from '../api'
import ConfirmDialog from './ConfirmDialog.vue'

const props = defineProps<{
  sessions: any[]
  currentSessionId: string | null
}>()

const emit = defineEmits<{
  selectSession: [id: string]
  newChat: []
}>()

const activeTab = ref<'chat' | 'knowledge' | 'settings'>('chat')

// 按时间分组的会话
const groupedSessions = computed(() => {
  const groups: Record<string, any[]> = {}
  for (const session of props.sessions) {
    const group = session.time_group || '其他'
    if (!groups[group]) groups[group] = []
    groups[group].push(session)
  }
  return groups
})

const groupOrder = ['今天', '昨天', '7天内']

const sortedGroups = computed(() => {
  const result: { label: string; sessions: any[] }[] = []
  const groups = groupedSessions.value

  // 按优先级排序
  for (const label of groupOrder) {
    if (groups[label]) {
      result.push({ label, sessions: groups[label] })
    }
  }

  // 其他分组
  for (const [label, sessions] of Object.entries(groups)) {
    if (!groupOrder.includes(label)) {
      result.push({ label, sessions })
    }
  }

  return result
})

// 设置相关
const llmProvider = ref('deepseek')
const llmModel = ref('deepseek-chat')
const apiKey = ref('')
const temperature = ref(0.7)
const isSaving = ref(false)
const saveMessage = ref('')
const availableModels = ref<string[]>([])
const isLoadingModels = ref(false)
const hasApiKey = ref(false)

// 知识库相关
const documents = ref<any[]>([])
const isUploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle')
const uploadMessage = ref('')

// 系统状态
const systemStatus = ref<any>(null)

function setActiveTab(tab: 'chat' | 'knowledge' | 'settings') {
  activeTab.value = tab

  if (tab === 'settings') {
    loadSettings()
  } else if (tab === 'knowledge') {
    loadDocuments()
  }
}

// 监听提供商变化，加载模型列表
watch(llmProvider, async (newProvider) => {
  await loadModels(newProvider)
})

async function loadModels(provider: string) {
  isLoadingModels.value = true
  try {
    const result = await getModels(provider)
    availableModels.value = result.models || []
    if (result.error) {
      console.warn('加载模型列表:', result.error)
    }
  } catch (error) {
    console.error('加载模型列表失败:', error)
    availableModels.value = []
  } finally {
    isLoadingModels.value = false
  }
}

async function loadSettings() {
  try {
    const [settings, status] = await Promise.all([getSettings(), getSystemStatus()])
    llmProvider.value = settings.llm_provider
    llmModel.value = settings.llm_model
    hasApiKey.value = settings.has_api_key
    systemStatus.value = status

    // 加载模型列表
    await loadModels(settings.llm_provider)
  } catch (error) {
    console.error('加载设置失败:', error)
  }
}

async function loadDocuments() {
  try {
    const result = await getDocuments()
    documents.value = result.documents
  } catch (error) {
    console.error('加载文档失败:', error)
  }
}

async function saveSettings() {
  isSaving.value = true
  saveMessage.value = ''

  try {
    await updateLLMSettings({
      provider: llmProvider.value,
      api_key: apiKey.value || undefined,
      model_name: llmModel.value,
      temperature: temperature.value,
    })
    saveMessage.value = '设置已保存'
    setTimeout(() => saveMessage.value = '', 3000)
  } catch (error) {
    saveMessage.value = '保存失败'
    console.error('保存设置失败:', error)
  } finally {
    isSaving.value = false
  }
}

async function handleUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  // 重置状态
  uploadStatus.value = 'uploading'
  uploadProgress.value = 0
  uploadMessage.value = `正在上传 ${file.name}...`

  try {
    // 上传文件（带进度）
    await uploadDocument(file, (percent) => {
      uploadProgress.value = percent
      if (percent >= 100) {
        uploadStatus.value = 'processing'
        uploadMessage.value = '正在处理文档...'
      }
    })

    // 上传成功
    uploadStatus.value = 'success'
    uploadMessage.value = `${file.name} 上传成功！`

    // 刷新文档列表
    await loadDocuments()

    // 3秒后清除成功提示
    setTimeout(() => {
      uploadStatus.value = 'idle'
      uploadMessage.value = ''
    }, 3000)

  } catch (error: any) {
    // 上传失败
    uploadStatus.value = 'error'
    uploadMessage.value = error?.response?.data?.detail || '上传失败，请重试'
    console.error('上传失败:', error)

    // 5秒后清除错误提示
    setTimeout(() => {
      uploadStatus.value = 'idle'
      uploadMessage.value = ''
    }, 5000)
  } finally {
    isUploading.value = false
    input.value = ''
  }
}

// 删除确认弹窗
const showDeleteDialog = ref(false)
const deleteTargetId = ref('')
const deleteTargetName = ref('')

function confirmDeleteDocument(docId: string, filename: string) {
  deleteTargetId.value = docId
  deleteTargetName.value = filename
  showDeleteDialog.value = true
}

async function handleConfirmDelete() {
  try {
    await deleteDocument(deleteTargetId.value)
    await loadDocuments()
  } catch (error) {
    console.error('删除失败:', error)
  } finally {
    showDeleteDialog.value = false
    deleteTargetId.value = ''
    deleteTargetName.value = ''
  }
}

function handleCancelDelete() {
  showDeleteDialog.value = false
  deleteTargetId.value = ''
  deleteTargetName.value = ''
}
</script>

<template>
  <aside class="sidebar" role="navigation" aria-label="主导航">
    <!-- Logo -->
    <div class="sidebar-header">
      <div class="logo">
        <svg class="logo-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
          <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
        </svg>
        <span class="logo-text">EduLocal</span>
      </div>
    </div>

    <!-- New Chat Button -->
    <div class="new-chat-wrapper">
      <button class="new-chat-btn" @click="emit('newChat')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        新对话
      </button>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <button
        :class="['nav-item', { active: activeTab === 'chat' }]"
        @click="setActiveTab('chat')"
      >
        <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span>对话</span>
      </button>

      <button
        :class="['nav-item', { active: activeTab === 'knowledge' }]"
        @click="setActiveTab('knowledge')"
      >
        <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
          <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
        </svg>
        <span>知识库</span>
      </button>

      <button
        :class="['nav-item', { active: activeTab === 'settings' }]"
        @click="setActiveTab('settings')"
      >
        <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
        </svg>
        <span>设置</span>
      </button>
    </nav>

    <!-- Content Area -->
    <div class="sidebar-content">
      <!-- Chat History -->
      <div v-if="activeTab === 'chat'" class="tab-content">
        <div v-if="sessions.length > 0" class="session-groups">
          <div v-for="group in sortedGroups" :key="group.label" class="session-group">
            <div class="group-label">{{ group.label }}</div>
            <div class="group-items">
              <button
                v-for="session in group.sessions"
                :key="session.id"
                :class="['session-item', { active: currentSessionId === session.id }]"
                @click="emit('selectSession', session.id)"
              >
                <svg class="session-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                <span class="session-title">{{ session.title || '新对话' }}</span>
              </button>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <svg class="empty-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <p>开始新对话</p>
        </div>
      </div>

      <!-- Knowledge Base -->
      <div v-if="activeTab === 'knowledge'" class="tab-content">
        <div class="section-header">
          <h3>知识库</h3>
        </div>

        <label class="upload-btn" :class="{ disabled: isUploading }">
          <input type="file" accept=".pdf,.txt,.md,.docx,.html" @change="handleUpload" hidden :disabled="isUploading" />
          <svg v-if="!isUploading" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <svg v-else class="upload-spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
          <span>{{ isUploading ? '上传中...' : '上传文档' }}</span>
        </label>

        <!-- 上传进度 -->
        <div v-if="uploadStatus !== 'idle'" class="upload-status" :class="uploadStatus">
          <!-- 上传中 -->
          <template v-if="uploadStatus === 'uploading'">
            <div class="progress-info">
              <span class="progress-text">{{ uploadMessage }}</span>
              <span class="progress-percent">{{ uploadProgress }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
            </div>
          </template>

          <!-- 处理中 -->
          <template v-else-if="uploadStatus === 'processing'">
            <div class="processing-info">
              <svg class="processing-spinner" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              <span>{{ uploadMessage }}</span>
            </div>
          </template>

          <!-- 成功 -->
          <template v-else-if="uploadStatus === 'success'">
            <div class="success-info">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              <span>{{ uploadMessage }}</span>
            </div>
          </template>

          <!-- 错误 -->
          <template v-else-if="uploadStatus === 'error'">
            <div class="error-info">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              <span>{{ uploadMessage }}</span>
            </div>
          </template>
        </div>

        <div v-if="documents.length > 0" class="doc-list">
          <div v-for="doc in documents" :key="doc.id" class="doc-item">
            <div class="doc-info">
              <span class="doc-name">{{ doc.filename }}</span>
              <span class="doc-meta">{{ doc.chunk_count }} 个分块</span>
            </div>
            <button class="doc-delete" @click="confirmDeleteDocument(doc.id, doc.filename)" title="删除">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>
        <div v-else-if="uploadStatus === 'idle'" class="empty-state">
          <svg class="empty-icon" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <p>上传教材开始使用</p>
          <span class="empty-hint">支持 PDF、Word、TXT、Markdown</span>
        </div>
      </div>

      <!-- Settings -->
      <div v-if="activeTab === 'settings'" class="tab-content">
        <div class="section-header">
          <h3>设置</h3>
        </div>

        <div class="settings-form">
          <div class="form-group">
            <label for="llm-provider">LLM 提供商</label>
            <select id="llm-provider" v-model="llmProvider">
              <option value="deepseek">DeepSeek</option>
              <option value="openai">OpenAI</option>
              <option value="ollama">Ollama (本地)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="llm-model">
              模型名称
              <span v-if="isLoadingModels" class="loading-hint">(加载中...)</span>
            </label>
            <select v-if="availableModels.length > 0" id="llm-model" v-model="llmModel">
              <option v-for="model in availableModels" :key="model" :value="model">
                {{ model }}
              </option>
            </select>
            <input v-else id="llm-model" v-model="llmModel" placeholder="deepseek-chat" />
          </div>

          <div class="form-group">
            <label for="api-key">
              API Key
              <span v-if="hasApiKey" class="key-saved">已保存</span>
            </label>
            <input id="api-key" v-model="apiKey" type="password" :placeholder="hasApiKey ? '已保存，留空保持不变' : '输入 API Key'" />
          </div>

          <div class="form-group">
            <label for="temperature">Temperature: {{ temperature }}</label>
            <input id="temperature" v-model.number="temperature" type="range" min="0" max="2" step="0.1" />
          </div>

          <button class="save-btn" @click="saveSettings" :disabled="isSaving">
            {{ isSaving ? '保存中...' : '保存设置' }}
          </button>

          <div v-if="saveMessage" :class="['save-message', saveMessage.includes('失败') ? 'error' : 'success']">
            {{ saveMessage }}
          </div>

          <!-- System Status -->
          <div v-if="systemStatus" class="status-section">
            <h4>系统状态</h4>
            <div class="status-item">
              <span>当前模型</span>
              <span>{{ systemStatus.llm_provider }} / {{ systemStatus.llm_model }}</span>
            </div>
            <div class="status-item">
              <span>API Key</span>
              <span :class="systemStatus.has_api_key ? 'available' : 'unavailable'">
                {{ systemStatus.has_api_key ? '已配置' : '未配置' }}
              </span>
            </div>
            <div class="status-item">
              <span>Ollama</span>
              <span :class="systemStatus.ollama_available ? 'available' : 'unavailable'">
                {{ systemStatus.ollama_available ? '可用' : '未检测到' }}
              </span>
            </div>
            <div class="status-item">
              <span>数据库</span>
              <span>{{ systemStatus.stats?.messages || 0 }} 条消息</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </aside>

  <!-- 删除确认弹窗 -->
  <ConfirmDialog
    :visible="showDeleteDialog"
    title="删除文档"
    :message="`确定要删除文档「${deleteTargetName}」吗？删除后将无法恢复。`"
    confirm-text="删除"
    cancel-text="取消"
    type="danger"
    @confirm="handleConfirmDelete"
    @cancel="handleCancelDelete"
  />
</template>

<style scoped>
.sidebar {
  width: 280px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-header {
  padding: var(--space-5) var(--space-5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.logo-icon {
  color: var(--color-accent);
}

.logo-text {
  font-size: var(--font-size-lg);
  font-weight: 600;
  letter-spacing: -0.02em;
}

.new-chat-wrapper {
  padding: var(--space-3) var(--space-3);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-3);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-md);
  color: var(--color-on-primary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.new-chat-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
}

.sidebar-nav {
  padding: var(--space-3) var(--space-3);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: rgba(255, 255, 255, 0.6);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.9);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.12);
  color: var(--color-on-primary);
}

.nav-icon {
  opacity: 0.8;
}

.nav-item.active .nav-icon {
  opacity: 1;
  color: var(--color-accent);
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4);
}

.tab-content {
  animation: fadeIn 200ms ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-header {
  margin-bottom: var(--space-4);
}

.section-header h3 {
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Session Groups - DeepSeek Style */
.session-groups {
  display: flex;
  flex-direction: column;
}

.session-group {
  margin-bottom: var(--space-4);
}

.group-label {
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: rgba(255, 255, 255, 0.35);
  padding: var(--space-1) var(--space-2);
  margin-bottom: var(--space-1);
}

.group-items {
  display: flex;
  flex-direction: column;
}

.session-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: rgba(255, 255, 255, 0.75);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
}

.session-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.95);
}

.session-item.active {
  background: rgba(255, 255, 255, 0.12);
  color: var(--color-on-primary);
}

.session-icon {
  opacity: 0.4;
  flex-shrink: 0;
}

.session-item:hover .session-icon {
  opacity: 0.6;
}

.session-item.active .session-icon {
  opacity: 1;
  color: var(--color-accent);
}

.session-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-8) var(--space-4);
  text-align: center;
}

.empty-icon {
  color: rgba(255, 255, 255, 0.15);
  margin-bottom: var(--space-3);
}

.empty-state p {
  color: rgba(255, 255, 255, 0.4);
  font-size: var(--font-size-sm);
}

.empty-hint {
  color: rgba(255, 255, 255, 0.3);
  font-size: var(--font-size-xs);
  margin-top: var(--space-1);
}

/* Upload Button */
.upload-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: rgba(255, 255, 255, 0.06);
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-md);
  color: rgba(255, 255, 255, 0.7);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.upload-btn:hover:not(.disabled) {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  color: var(--color-on-primary);
}

.upload-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.upload-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Upload Status */
.upload-status {
  margin-top: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--font-size-xs);
}

.upload-status.uploading {
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.upload-status.processing {
  background: rgba(161, 98, 7, 0.15);
  border: 1px solid rgba(161, 98, 7, 0.3);
}

.upload-status.success {
  background: rgba(22, 163, 74, 0.15);
  border: 1px solid rgba(22, 163, 74, 0.3);
}

.upload-status.error {
  background: rgba(220, 38, 38, 0.15);
  border: 1px solid rgba(220, 38, 38, 0.3);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-2);
  color: rgba(255, 255, 255, 0.9);
}

.progress-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-percent {
  font-weight: 600;
  color: var(--color-accent);
}

.progress-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-accent);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.processing-info,
.success-info,
.error-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: rgba(255, 255, 255, 0.9);
}

.processing-spinner {
  animation: spin 1s linear infinite;
}

.success-info svg {
  color: #4ade80;
}

.error-info svg {
  color: #f87171;
}

/* Document List */
.doc-list {
  margin-top: var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3);
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-sm);
}

.doc-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.doc-name {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-meta {
  font-size: var(--font-size-xs);
  color: rgba(255, 255, 255, 0.4);
}

.doc-delete {
  padding: var(--space-1);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.doc-delete:hover {
  background: rgba(220, 38, 38, 0.2);
  color: #f87171;
}

/* Settings Form */
.settings-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-group label {
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.loading-hint {
  font-weight: 400;
  opacity: 0.6;
}

.key-saved {
  font-size: 10px;
  padding: 2px 6px;
  background: rgba(22, 163, 74, 0.2);
  color: #4ade80;
  border-radius: var(--radius-sm);
}

.form-group select,
.form-group input {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-sm);
  color: var(--color-on-primary);
  font-size: var(--font-size-sm);
  transition: border-color var(--transition-fast);
}

.form-group select:focus,
.form-group input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.form-group select option {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.form-group input::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.form-group input[type="range"] {
  padding: 0;
  background: transparent;
  border: none;
  cursor: pointer;
  margin: 0;
}

.form-group input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  background: var(--color-accent);
  border-radius: 50%;
  cursor: pointer;
  margin-top: -6px;
}

.form-group input[type="range"]::-webkit-slider-runnable-track {
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

.save-btn {
  width: 100%;
  padding: var(--space-3);
  background: var(--color-accent);
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-on-primary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.save-btn:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.save-message {
  font-size: var(--font-size-xs);
  text-align: center;
  padding: var(--space-2);
  border-radius: var(--radius-sm);
}

.save-message.success {
  background: rgba(22, 163, 74, 0.2);
  color: #4ade80;
}

.save-message.error {
  background: rgba(220, 38, 38, 0.2);
  color: #f87171;
}

.status-section {
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.status-section h4 {
  font-size: var(--font-size-xs);
  font-weight: 600;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: var(--space-3);
}

.status-item {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-xs);
  padding: var(--space-2) 0;
  color: rgba(255, 255, 255, 0.6);
}

.status-item .available {
  color: #4ade80;
}

.status-item .unavailable {
  color: #f87171;
}
</style>
