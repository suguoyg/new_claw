<template>
  <div class="confirm-overlay">
    <div class="confirm-dialog card">
      <div class="confirm-icon">⚠️</div>
      <h3>确认请求</h3>
      <div class="confirm-content">
        <p><strong>操作:</strong> {{ action }}</p>
        <p><strong>目标:</strong> {{ target }}</p>
        <p class="warning">{{ warning }}</p>
      </div>
      <div class="confirm-actions">
        <button @click="$emit('cancel')" class="btn btn-secondary">取消</button>
        <button @click="$emit('confirm')" class="btn btn-danger">确认执行</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  tool: string
  action: string
  target: string
  warning: string
}>()

defineEmits<{
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.confirm-dialog {
  max-width: 400px;
  text-align: center;
}

.confirm-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.confirm-content {
  margin: 1.5rem 0;
  text-align: left;
}

.confirm-content p {
  margin-bottom: 0.5rem;
}

.warning {
  color: var(--error-color);
  font-weight: 500;
}

.confirm-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
</style>
