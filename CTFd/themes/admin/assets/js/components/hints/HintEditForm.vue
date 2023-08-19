<template>
  <div class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header text-center">
          <div class="container">
            <div class="row">
              <div class="col-md-12">
                <h3>{{ language("Edit Hint","编辑提示") }}</h3>
              </div>
            </div>
          </div>
          <button
            type="button"
            class="close"
            data-dismiss="modal"
            aria-label="Close"
            style="position: absolute;top: 0;right: 0;padding: 30px;"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
        <form method="POST" @submit.prevent="updateHint">
          <div class="modal-body">
            <div class="container">
              <div class="row">
                <div class="col-md-12">
                  <div class="form-group">
                    <label>
                      {{ language("Hint:","提示内容：") }}<br />
                      <small>{{ language("Markdown & HTML are supported","支持Markdown & HTML") }}</small>
                    </label>
                    <!-- Explicitly don't put the markdown class on this because we will add it later -->
                    <textarea
                      type="text"
                      class="form-control"
                      name="content"
                      rows="7"
                      :value="this.content"
                      ref="content"
                    ></textarea>
                  </div>

                  <div class="form-group">
                    <label>
                      {{ language("Cost:","解锁花费：") }}<br />
                      <small>{{ language("How many points it costs to see your hint.","需要多少积分才能看到你的提示。") }}</small>
                    </label>
                    <input
                      type="number"
                      class="form-control"
                      name="cost"
                      v-model.lazy="cost"
                    />
                  </div>

                  <div class="form-group">
                    <label>
                      {{ language("Requirements:","前置要求：") }}<br />
                      <small>
                        {{ language("Hints that must be unlocked before unlocking this hint","解锁此提示之前必须先解锁的提示") }}
                      </small>
                    </label>
                    <div
                      class="form-check"
                      v-for="hint in otherHints"
                      :key="hint.id"
                    >
                      <label class="form-check-label cursor-pointer">
                        <input
                          class="form-check-input"
                          type="checkbox"
                          :value="hint.id"
                          v-model="selectedHints"
                        />
                        ID: {{ hint.content }} - {{ language("Content:","内容：") }}{{ hint.content }} - {{ language("Cost:","花费：") }}{{ hint.cost }}
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <div class="container">
              <div class="row">
                <div class="col-md-12">
                  <button class="btn btn-primary float-right">{{ language("Submit","提交") }}</button>
                </div>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import CTFd from "core/CTFd";
import { bindMarkdownEditor } from "../../styles";

export default {
  name: "HintEditForm",
  props: {
    challenge_id: Number,
    hint_id: Number,
    hints: Array
  },
  data: function() {
    return {
      cost: 0,
      content: null,
      selectedHints: []
    };
  },
  computed: {
    // Get all hints besides the current one
    otherHints: function() {
      return this.hints.filter(hint => {
        return hint.id !== this.$props.hint_id;
      });
    }
  },
  watch: {
    hint_id: {
      immediate: true,
      handler(val, oldVal) {
        if (val !== null) {
          this.loadHint();
        }
      }
    }
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
    loadHint: function() {
      CTFd.fetch(`/api/v1/hints/${this.$props.hint_id}?preview=true`, {
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
            let hint = response.data;
            this.cost = hint.cost;
            this.content = hint.content;
            this.selectedHints = hint.requirements?.prerequisites || [];
            // Wait for Vue to update the DOM
            this.$nextTick(() => {
              // Wait a little longer because we need the modal to appear.
              // Kinda nasty but not really avoidable without polling the DOM via CodeMirror
              setTimeout(() => {
                let editor = this.$refs.content;
                bindMarkdownEditor(editor);
                editor.mde.codemirror.getDoc().setValue(editor.value);
                editor.mde.codemirror.refresh();
              }, 100);
            });
          }
        });
    },
    getCost: function() {
      return this.cost || 0;
    },
    getContent: function() {
      return this.$refs.content.value;
    },
    updateHint: function() {
      let params = {
        challenge_id: this.$props.challenge_id,
        content: this.getContent(),
        cost: this.getCost(),
        requirements: { prerequisites: this.selectedHints }
      };

      CTFd.fetch(`/api/v1/hints/${this.$props.hint_id}`, {
        method: "PATCH",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify(params)
      })
        .then(response => {
          return response.json();
        })
        .then(response => {
          if (response.success) {
            this.$emit("refreshHints", this.$options.name);
          }
        });
    }
  },
  mounted() {
    if (this.hint_id) {
      this.loadHint();
    }
  },
  created() {
    if (this.hint_id) {
      this.loadHint();
    }
  }
};
</script>

<style scoped></style>
