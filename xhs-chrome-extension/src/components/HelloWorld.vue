<script setup lang="ts">
defineProps<{
  msg: string
}>()
</script>

<template>
  <div class="hello-world">
    <h2>{{ msg }}</h2>
  </div>
</template>

<style scoped>
.hello-world {
  text-align: center;
  padding: 20px;
}
</style>
