<template>
  <div class="card bg-light mb-4">
    <button
      type="button"
      :data-notif-id="this.id"
      class="delete-notification close position-absolute p-3"
      style="right:0;"
      data-dismiss="alert"
      aria-label="Close"
      @click="deleteNotification()"
    >
      <span aria-hidden="true">&times;</span>
    </button>
    <div class="card-body">
      <h3 class="card-title">{{ title }}</h3>
      <blockquote class="blockquote mb-0">
        <p v-html="this.html"></p>
        <small class="text-muted">
          <span :data-time="this.date">{{ this.localDate() }}</span>
        </small>
      </blockquote>
    </div>
  </div>
</template>

<script>
import CTFd from "core/CTFd";
import dayjs from "dayjs";
import hljs from "highlight.js";
export default {
  props: {
    id: Number,
    title: String,
    content: String,
    html: String,
    date: String
  },
  methods: {
    language: function (en, zh) {
      const cookies = document.cookie.split('; ');
      for (const cookie of cookies) {
        const [cookieName, cookieValue] = cookie.split('=');
        if (cookieName === "Scr1wCTFdLanguage") {
          return (decodeURIComponent(cookieValue) === "en" ? en : zh);
        }
      }
      return zh;
    },
    localDate: function() {
      return dayjs(this.date).format("MMMM Do, HH:mm:ss ");
    },
    deleteNotification: function() {
      if (confirm(this.language("Are you sure you want to delete this notification?","您确定要删除此通知吗？"))) {
        CTFd.api
          .delete_notification({ notificationId: this.id })
          .then(response => {
            if (response.success) {
              // Delete the current component
              // https://stackoverflow.com/a/55384005
              this.$destroy();
              this.$el.parentNode.removeChild(this.$el);
            }
          });
      }
    }
  },
  mounted() {
    this.$el.querySelectorAll("pre code").forEach(block => {
      hljs.highlightBlock(block);
    });
  }
};
</script>
