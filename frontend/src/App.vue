<template>
  <div id="app">
    <AppHeader />
    <router-view />
    <ChatbotWidget />
  </div>
</template>

<script>
import AppHeader from "@/components/AppHeader.vue";
import ChatbotWidget from '@/components/ChatbotWidget.vue'

export default {
  components: {
    AppHeader,
    ChatbotWidget
  },

};
</script>

<style>
/* Đảm bảo root có vị trí tương đối nếu cần */
#app {
  position: relative;
}
</style>