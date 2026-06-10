<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import Sidebar from '../components/Sidebar.vue'
import ChatMessage from '../components/ChatMessage.vue'
import ChatInput from '../components/ChatInput.vue'
import type { ChatMessage as ChatMessageType } from '../types'
import { sendMessageStream, getSessions, getChatHistory } from '../api'

const messages = ref<ChatMessageType[]>([])
const isLoading = ref(false)
const sessionId = ref<string | null>(null)
const sessions = ref<any[]>([])
const currentStreamingMessage = ref('')

onMounted(() => {
  loadSessions()
})

async function loadSessions() {
  try {
    const result = await getSessions()
    sessions.value = result.sessions || []
  } catch (error) {
    console.error('加载会话失败:', error)
  }
}

async function selectSession(id: string) {
  sessionId.value = id
  try {
    const result = await getChatHistory(id)
    messages.value = (result.messages || []).map((msg: any) => ({
      role: msg.role,
      content: msg.content,
      sources: msg.sources || [],
    }))
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('加载历史失败:', error)
  }
}

function startNewChat() {
  sessionId.value = null
  messages.value = []
}

async function handleSend(content: string) {
  if (!content.trim() || isLoading.value) return

  // Add user message
  messages.value.push({ role: 'user', content })
  isLoading.value = true
  currentStreamingMessage.value = ''

  // 添加空的助手消息用于流式更新
  const assistantIndex = messages.value.length
  messages.value.push({ role: 'assistant', content: '', sources: [] })

  try {
    let finalReply = ''

    await sendMessageStream(
      {
        message: content,
        session_id: sessionId.value || undefined,
      },
      {
        onAgent: (agent) => {
          console.log('Agent:', agent)
        },
        onRetrieval: (count) => {
          console.log('检索到', count, '个文档')
        },
        onContent: (chunk) => {
          finalReply += chunk
          messages.value[assistantIndex].content = finalReply
          scrollToBottom()
        },
        onDone: (sources) => {
          messages.value[assistantIndex].sources = sources
          // 从最终回复中提取 session_id（如果有）
          if (!sessionId.value) {
            // 生成一个临时 session_id
            sessionId.value = crypto.randomUUID()
          }
          loadSessions()
        },
        onError: (error) => {
          messages.value[assistantIndex].content = `抱歉，处理您的请求时出现错误：${error}`
        },
      }
    )
  } catch (error) {
    console.error('Failed to send message:', error)
    messages.value[assistantIndex].content = '抱歉，处理您的请求时出现错误，请稍后重试。'
  } finally {
    isLoading.value = false
    currentStreamingMessage.value = ''
    await nextTick()
    scrollToBottom()
  }
}

function scrollToBottom() {
  const chatContainer = document.querySelector('.chat-messages')
  if (chatContainer) {
    chatContainer.scrollTo({
      top: chatContainer.scrollHeight,
      behavior: 'smooth'
    })
  }
}
</script>

<template>
  <div class="chat-view">
    <!-- Sidebar -->
    <Sidebar
      :sessions="sessions"
      :current-session-id="sessionId"
      @select-session="selectSession"
      @new-chat="startNewChat"
    />

    <!-- Main Chat Area -->
    <main class="chat-main">
      <!-- Session Header -->
      <div class="session-header" v-if="sessionId">
        <button class="back-btn" @click="startNewChat">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12"/>
            <polyline points="12 19 5 12 12 5"/>
          </svg>
          新对话
        </button>
        <span class="session-id">会话 {{ sessionId?.slice(0, 8) }}...</span>
      </div>

      <!-- Messages -->
      <div class="chat-messages">
        <!-- Welcome State -->
        <div v-if="messages.length === 0" class="welcome">
          <div class="welcome-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
          </div>
          <h1>EduLocal</h1>
          <p class="welcome-subtitle">智能教学助理</p>

          <div class="features">
            <div class="feature-card">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <span>知识答疑</span>
            </div>
            <div class="feature-card">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
              <span>习题生成</span>
            </div>
            <div class="feature-card">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 20h9"/>
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
              </svg>
              <span>学习规划</span>
            </div>
            <div class="feature-card">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"/>
                <line x1="12" y1="20" x2="12" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="14"/>
              </svg>
              <span>学情分析</span>
            </div>
          </div>

          <div class="quick-actions">
            <p class="hint">试试这些：</p>
            <div class="action-chips">
              <button @click="handleSend('什么是勾股定理？')">什么是勾股定理？</button>
              <button @click="handleSend('帮我出5道二次函数的练习题')">出5道二次函数练习题</button>
              <button @click="handleSend('制定一个学习英语的计划')">制定英语学习计划</button>
            </div>
          </div>
        </div>

        <!-- Message List -->
        <ChatMessage
          v-for="(msg, index) in messages"
          :key="index"
          :message="msg"
        />

        <!-- Loading Indicator -->
        <div v-if="isLoading && !currentStreamingMessage" class="loading-indicator">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>

      <!-- Input -->
      <ChatInput @send="handleSend" :disabled="isLoading" />
    </main>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  height: 100vh;
  width: 100%;
  background: var(--color-background);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.session-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-5);
  background: var(--color-background);
  border-bottom: 1px solid var(--color-border);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-muted);
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  background: var(--color-border);
  color: var(--color-foreground);
}

.session-id {
  font-size: var(--font-size-xs);
  color: var(--color-secondary);
  opacity: 0.6;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
  scroll-behavior: smooth;
}

/* Welcome State */
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: var(--space-8);
  animation: fadeIn 400ms ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.welcome-icon {
  width: 80px;
  height: 80px;
  background: var(--color-muted);
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-6);
  color: var(--color-accent);
}

.welcome h1 {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--color-foreground);
  letter-spacing: -0.03em;
  margin-bottom: var(--space-2);
}

.welcome-subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-secondary);
  margin-bottom: var(--space-8);
}

.features {
  display: flex;
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.feature-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  background: var(--color-muted);
  border-radius: var(--radius-lg);
  color: var(--color-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  transition: all var(--transition-fast);
}

.feature-card:hover {
  background: var(--color-border);
  color: var(--color-foreground);
  transform: translateY(-2px);
}

.quick-actions {
  margin-top: var(--space-4);
}

.quick-actions .hint {
  font-size: var(--font-size-sm);
  color: var(--color-secondary);
  margin-bottom: var(--space-3);
}

.action-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: center;
}

.action-chips button {
  padding: var(--space-2) var(--space-4);
  background: var(--color-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-chips button:hover {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-on-primary);
}

/* Loading Indicator */
.loading-indicator {
  display: flex;
  justify-content: flex-start;
  padding-left: 48px;
  margin-bottom: var(--space-5);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: var(--space-3) var(--space-4);
  background: var(--color-muted);
  border-radius: var(--radius-lg);
  border-bottom-left-radius: var(--radius-sm);
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: var(--color-secondary);
  border-radius: var(--radius-full);
  opacity: 0.4;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: 0ms; }
.typing-indicator span:nth-child(2) { animation-delay: 200ms; }
.typing-indicator span:nth-child(3) { animation-delay: 400ms; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* Responsive */
@media (max-width: 768px) {
  .features {
    flex-direction: column;
    width: 100%;
    max-width: 280px;
  }

  .feature-card {
    flex-direction: row;
    justify-content: center;
  }

  .action-chips {
    flex-direction: column;
  }
}
</style>
