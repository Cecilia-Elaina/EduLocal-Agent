<script setup lang="ts">
import { computed } from 'vue'
import type { ChatMessage } from '../types'

const props = defineProps<{
  message: ChatMessage
}>()

function formatContent(content: string): string {
  // 先处理引用标记，避免被其他规则影响
  let formatted = content

  // 处理标题 (### 标题)
  formatted = formatted.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  formatted = formatted.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  formatted = formatted.replace(/^# (.+)$/gm, '<h1>$1</h1>')

  // 处理粗体
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  // 处理斜体
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>')

  // 处理代码
  formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>')

  // 处理列表项
  formatted = formatted.replace(/^- (.+)$/gm, '<li>$1</li>')
  formatted = formatted.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')

  // 处理引用标记 [1], [2] 等
  formatted = formatted.replace(/\[(\d+)\]/g, '<sup class="citation">[$1]</sup>')

  // 处理换行
  formatted = formatted.replace(/\n\n/g, '</p><p>')
  formatted = formatted.replace(/\n/g, '<br>')

  // 包装列表
  formatted = formatted.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')

  // 清理连续的ul标签
  formatted = formatted.replace(/<\/ul>\s*<ul>/g, '')

  // 包装在p标签中
  if (!formatted.startsWith('<')) {
    formatted = '<p>' + formatted + '</p>'
  }

  return formatted
}

// 提取引用来源名称（不显示完整路径）
function getSourceName(source: string): string {
  if (!source) return ''
  // 获取文件名
  const parts = source.split(/[/\\]/)
  const filename = parts[parts.length - 1]
  // 移除扩展名
  return filename.replace(/\.[^.]+$/, '')
}

const sourceNames = computed(() => {
  return (props.message.sources || []).map(getSourceName).filter(Boolean)
})
</script>

<template>
  <div :class="['message', message.role]">
    <div class="avatar" :aria-label="message.role === 'user' ? '用户' : 'AI 助手'">
      <!-- User avatar -->
      <svg v-if="message.role === 'user'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
      <!-- AI avatar -->
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a4 4 0 0 1 4 4c0 1.95-1.4 3.58-3.25 3.93"/>
        <path d="M8.56 9.8A4.002 4.002 0 0 1 12 2"/>
        <path d="M12 18a4 4 0 0 1-3.44-2"/>
        <path d="M9 22h6"/>
        <path d="M12 18v4"/>
        <circle cx="12" cy="10" r="2"/>
      </svg>
    </div>

    <div class="message-body">
      <div class="message-content" v-html="formatContent(message.content)"></div>

      <div v-if="sourceNames.length > 0" class="sources">
        <div class="sources-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
          <span>参考来源</span>
        </div>
        <div class="source-list">
          <span v-for="(name, index) in sourceNames" :key="index" class="source-tag">
            {{ name }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
  max-width: 85%;
  animation: messageIn 300ms ease;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message.assistant {
  margin-right: auto;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform var(--transition-fast);
}

.message.user .avatar {
  background: var(--color-accent);
  color: var(--color-on-primary);
}

.message.assistant .avatar {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.message-body {
  min-width: 0;
}

.message.assistant .message-body {
  flex: 1;
}

.message.user .message-body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-content {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  line-height: 1.7;
  font-size: var(--font-size-sm);
}

.message.user .message-content {
  background: var(--color-accent);
  color: var(--color-on-primary);
  border-bottom-right-radius: var(--radius-sm);
  display: inline-block;
  max-width: fit-content;
  word-break: break-word;
}

.message.assistant .message-content {
  background: var(--color-muted);
  color: var(--color-foreground);
  border-bottom-left-radius: var(--radius-sm);
}

/* Markdown 样式 */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin: var(--space-4) 0 var(--space-2);
  font-weight: 600;
  color: var(--color-foreground);
}

.message-content :deep(h1) {
  font-size: var(--font-size-xl);
}

.message-content :deep(h2) {
  font-size: var(--font-size-lg);
}

.message-content :deep(h3) {
  font-size: var(--font-size-base);
}

.message-content :deep(p) {
  margin: var(--space-2) 0;
}

.message-content :deep(strong) {
  font-weight: 600;
  color: var(--color-foreground);
}

.message-content :deep(em) {
  font-style: italic;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  font-family: 'SF Mono', Monaco, monospace;
  font-size: var(--font-size-xs);
}

.message.user .message-content :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message-content :deep(ul) {
  margin: var(--space-2) 0;
  padding-left: var(--space-5);
}

.message-content :deep(li) {
  margin: var(--space-1) 0;
  list-style-type: disc;
}

.message-content :deep(.citation) {
  color: var(--color-accent);
  font-weight: 600;
  cursor: help;
}

/* Sources */
.sources {
  margin-top: var(--space-3);
  padding: var(--space-3);
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.sources-header {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--color-secondary);
  margin-bottom: var(--space-2);
}

.source-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.source-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  background: var(--color-muted);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  color: var(--color-secondary);
}

.source-tag::before {
  content: "📄";
  font-size: 12px;
}
</style>
