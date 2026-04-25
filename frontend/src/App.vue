<template>
  <n-config-provider>
    <n-message-provider>
      <!-- 根组件只负责承载路由页面，具体布局放在 AppLayout 中。 -->
      <router-view />
    </n-message-provider>
  </n-config-provider>
</template>
