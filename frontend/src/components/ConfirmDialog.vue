<script setup lang="ts">
const props = defineProps<{
  visible: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
}>()

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="dialog-overlay" @click.self="emit('cancel')">
        <Transition name="scale">
          <div v-if="visible" class="dialog-container">
            <!-- 图标 -->
            <div :class="['dialog-icon', type || 'danger']">
              <svg v-if="type === 'danger' || !type" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              <svg v-else-if="type === 'warning'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                <line x1="12" y1="9" x2="12" y2="13"/>
                <line x1="12" y1="17" x2="12.01" y2="17"/>
              </svg>
              <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
            </div>

            <!-- 内容 -->
            <h3 class="dialog-title">{{ title }}</h3>
            <p class="dialog-message">{{ message }}</p>

            <!-- 按钮 -->
            <div class="dialog-actions">
              <button class="btn-cancel" @click="emit('cancel')">
                {{ cancelText || '取消' }}
              </button>
              <button :class="['btn-confirm', type || 'danger']" @click="emit('confirm')">
                {{ confirmText || '确定' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-container {
  background: var(--color-background, #fff);
  border-radius: 16px;
  padding: 32px;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  text-align: center;
}

.dialog-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.dialog-icon.danger {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.dialog-icon.warning {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.dialog-icon.info {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-foreground, #1a1a1a);
  margin: 0 0 12px;
}

.dialog-message {
  font-size: 14px;
  color: var(--color-secondary, #666);
  margin: 0 0 28px;
  line-height: 1.6;
}

.dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-cancel,
.btn-confirm {
  padding: 12px 28px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-cancel {
  background: var(--color-muted, #f5f5f5);
  color: var(--color-secondary, #666);
}

.btn-cancel:hover {
  background: var(--color-border, #e5e5e5);
}

.btn-confirm {
  color: white;
}

.btn-confirm.danger {
  background: #ef4444;
}

.btn-confirm.danger:hover {
  background: #dc2626;
}

.btn-confirm.warning {
  background: #f59e0b;
}

.btn-confirm.warning:hover {
  background: #d97706;
}

.btn-confirm.info {
  background: #3b82f6;
}

.btn-confirm.info:hover {
  background: #2563eb;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.scale-enter-active {
  transition: all 0.2s ease;
}

.scale-leave-active {
  transition: all 0.15s ease;
}

.scale-enter-from {
  transform: scale(0.9);
  opacity: 0;
}

.scale-leave-to {
  transform: scale(0.95);
  opacity: 0;
}
</style>
