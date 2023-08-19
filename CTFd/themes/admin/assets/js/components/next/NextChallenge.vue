<template>
  <div>
    <form @submit.prevent="updateNext">
      <div class="form-group">
        <label>
          {{ language("Next Challenge","下一题") }}
          <br />
          <small class="text-muted"
            >{{ language("Challenge to recommend after solving this challenge","解决此题目后推荐的题目") }}</small
          >
        </label>
        <select class="form-control custom-select" v-model="selected_id">
          <option value="null"> -- </option>
          <option
            v-for="challenge in otherChallenges"
            :value="challenge.id"
            :key="challenge.id"
            >{{ challenge.name }}</option
          >
        </select>
      </div>
      <div class="form-group">
        <button
          class="btn btn-success float-right"
          :disabled="!updateAvailable"
        >
          {{ language("Save","保存") }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import CTFd from "core/CTFd";

export default {
  props: {
    challenge_id: Number
  },
  data: function() {
    return {
      challenge: null,
      challenges: [],
      selected_id: null
    };
  },
  computed: {
    updateAvailable: function() {
      if (this.challenge) {
        return this.selected_id != this.challenge.next_id;
      } else {
        return false;
      }
    },
    // Get all challenges besides the current one and current next
    otherChallenges: function() {
      return this.challenges.filter(challenge => {
        return challenge.id !== this.$props.challenge_id;
      });
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
    loadData: function() {
      CTFd.fetch(`/api/v1/challenges/${this.$props.challenge_id}`, {
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
            this.challenge = response.data;
            this.selected_id = response.data.next_id;
          }
        });
    },
    loadChallenges: function() {
      CTFd.fetch("/api/v1/challenges?view=admin", {
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
            this.challenges = response.data;
          }
        });
    },
    updateNext: function() {
      CTFd.fetch(`/api/v1/challenges/${this.$props.challenge_id}`, {
        method: "PATCH",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          next_id: this.selected_id != "null" ? this.selected_id : null
        })
      })
        .then(response => {
          return response.json();
        })
        .then(data => {
          if (data.success) {
            this.loadData();
            this.loadChallenges();
          }
        });
    }
  },
  created() {
    this.loadData();
    this.loadChallenges();
  }
};
</script>

<style scoped></style>
