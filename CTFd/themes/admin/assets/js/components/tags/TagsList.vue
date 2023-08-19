<template>
  <div class="col-md-12">
    <div id="challenge-tags" class="my-3">
      <span
        class="badge badge-primary mx-1 challenge-tag"
        v-for="tag in tags"
        :key="tag.id"
      >
        <span>{{ tag.value }}</span>
        <a class="btn-fa delete-tag" @click="deleteTag(tag.id)"> &#215;</a>
      </span>
    </div>

    <div class="form-group">
      <label
        >{{ language("Tag","标签") }}
        <br />
        <small class="text-muted">{{ language("Type tag and press Enter","输入标签并按 Enter 键") }}</small>
      </label>
      <input
        id="tags-add-input"
        maxlength="80"
        type="text"
        class="form-control"
        v-model.lazy="tagValue"
        @keyup.enter="addTag()"
      />
    </div>
  </div>
</template>

<script>
import $ from "jquery";
import CTFd from "core/CTFd";

export default {
  props: {
    challenge_id: Number
  },
  data: function() {
    return {
      tags: [],
      tagValue: ""
    };
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
    loadTags: function() {
      CTFd.fetch(`/api/v1/challenges/${this.$props.challenge_id}/tags`, {
        method: "GET",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        }
      })
        .then(response => {
          return response.json();
        })
        .then(response => {
          if (response.success) {
            this.tags = response.data;
          }
        });
    },
    addTag: function() {
      const params = {
        value: this.tagValue,
        challenge: this.$props.challenge_id
      };
      CTFd.api.post_tag_list({}, params).then(response => {
        if (response.success) {
          this.tagValue = "";
          this.loadTags();
        }
      });
    },
    deleteTag: function(tag_id) {
      CTFd.api.delete_tag({ tagId: tag_id }).then(response => {
        if (response.success) {
          this.loadTags();
        }
      });
    }
  },
  created() {
    this.loadTags();
  }
};
</script>

<style scoped></style>
