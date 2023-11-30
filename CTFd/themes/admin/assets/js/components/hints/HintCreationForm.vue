<template>
  <div class="modal fade" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header text-center">
          <div class="container">
            <div class="row">
              <div class="col-md-12">
                <h3>{{ language("Create Hint","创建提示") }}</h3>
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
        <form method="POST" @submit.prevent="submitHint">
          <div class="modal-body">
            <div class="container">
              <div class="row">
                <div class="col-md-12">
                  <div class="form-group">
                    <label>
                      {{ language("Hint:","提示内容：") }}<br />
                      <small>{{ language("Markdown & HTML are supported","支持Markdown & HTML") }}</small>
                    </label>
                    <textarea
                      type="text"
                      class="form-control markdown"
                      name="content"
                      rows="7"
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
                    <label style="word-break: break-all;">
                      {{ language("Requirements:","前置要求：") }}<br />
                      <small>
                        {{ language("Hints that must be unlocked before unlocking this hint","解锁此提示之前必须先解锁的提示") }}
                      </small>
                    </label>
                    <div
                        class="form-check"
                        v-for="hint in hints"
                        :key="hint.id"
                    >
                      <label class="form-check-label cursor-pointer" style="word-break: break-all;">
                        <input
                            class="form-check-input"
                            type="checkbox"
                            :value="hint.id"
                            v-model="selectedHints"
                        />
                        ID: {{ hint.id }} - {{ language("Content:","内容：") }}{{ hint.content }} - {{ language("Cost:","花费：") }}{{ hint.cost }}
                      </label>
                    </div>
                  </div>

                  <input type="hidden" id="hint-id-for-hint" name="id" />
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
export default {
  name: "HintCreationForm",
  props: {
    challenge_id: Number,
    hints: Array
  },
  data: function() {
    return {
      cost: 0,
      selectedHints: []
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
    getCost: function() {
      return this.cost || 0;
    },
    getContent: function() {
      return this.$refs.content.value;
    },
    submitHint: function() {
      let params = {
        challenge_id: this.$props.challenge_id,
        content: this.getContent(),
        cost: this.getCost(),
        requirements: { prerequisites: this.selectedHints }
      };
      CTFd.fetch("/api/v1/hints", {
        method: "POST",
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
  }
};
</script>

<style scoped></style>
