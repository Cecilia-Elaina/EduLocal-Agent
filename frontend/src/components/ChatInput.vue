<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  send: [content: string]
}>()

const props = defineProps<{
  disabled?: boolean
}>()

const inputText = ref('')

function handleSend() {
  if (!inputText.value.trim() || props.disabled) return
  emit('send', inputText.value)
  inputText.value = ''
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="chat-input-container">
    <div class="chat-input-wrapper">
      <textarea
        v-model="inputText"
        :disabled="disabled"
        placeholder="输入您的问题..."
        @keydown="handleKeydown"
        rows="1"
        aria-label="消息输入框"
      ></textarea>
      <button
        class="send-btn"
        :disabled="!inputText.trim() || disabled"
        @click="handleSend"
        :aria-label="disabled ? '正在处理中' : '发送消息'"
      >
        <svg v-if="!disabled" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
        <svg v-else class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
      </button>
    </div>
    <div class="input-hint">
      <span>Enter 发送</span>
      <span>Shift + Enter 换行</span>
    </div>
  </div>
</template>

<style scoped>
.chat-input-container {
  padding: var(--space-4) var(--space-5);
  background: var(--color-background);
  border-top: 1px solid var(--color-border);
}

.chat-input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-2) var(--space-2) var(--space-4);
  background: var(--color-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.chat-input-wrapper:focus-within {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(161, 98, 7, 0.1);
}

textarea {
  flex: 1;
  padding: var(--space-2) 0;
  background: transparent;
  border: none;
  resize: none;
  font-size: var(--font-size-sm);
  font-family: var(--font-family);
  line-height: 1.5;
  color: var(--color-foreground);
  min-height: 24px;
  max-height: 120px;
}

textarea:focus {
  outline: none;
}

textarea:disabled {
  opacity: 0.6;
}

textarea::placeholder {
  color: var(--color-secondary);
  opacity: 0.5;
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: var(--radius-full);
  background: var(--color-accent);
  color: var(--color-on-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: var(--color-accent-hover);
  transform: scale(1.05);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.send-btn:disabled {
  background: var(--color-border);
  cursor: not-allowed;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.input-hint {
  display: flex;
  justify-content: center;
  gap: var(--space-4);
  margin-top: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-secondary);
  opacity: 0.5;
}
</style>
