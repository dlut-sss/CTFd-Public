<template>
  <div id="flag-create-modal" class="modal fade" tabindex="-1">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header text-center">
          <div class="container">
            <div class="row">
              <div class="col-md-12">
                <h3>
                  {{ language("Create Flag","创建Flag") }}
                </h3>
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
        <div class="modal-body">
          <div class="create-keys-select-div">
            <label for="create-keys-select" class="control-label">
              {{ language("Choose Flag Type","选择Flag类型") }}
            </label>
            <select
              class="form-control custom-select"
              @change="selectType($event)"
            >
              <option> -- </option>
              <option
                v-for="type in Object.keys(types)"
                :value="type"
                :key="type"
                >{{ type }}</option
              >
            </select>
          </div>
          <br />
          <form @submit.prevent="submitFlag">
            <div id="create-flag-form" v-html="createForm"></div>
            <button
              class="btn btn-success float-right"
              type="submit"
              v-if="createForm"
            >
              {{ language("Create Flag","创建Flag") }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import $ from "jquery";
import CTFd from "core/CTFd";
import nunjucks from "nunjucks";

export default {
  name: "FlagCreationForm",
  props: {
    challenge_id: Number
  },
  data: function() {
    return {
      types: {},
      selectedType: null,
      createForm: ""
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
    selectType: function(event) {
      let flagType = event.target.value;
      if (this.types[flagType] === undefined) {
        this.selectedType = null;
        this.createForm = "";
        return;
      }
      let createFormURL = this.types[flagType]["templates"]["create"];

      $.get(CTFd.config.urlRoot + createFormURL, template_data => {
        const template = nunjucks.compile(template_data);
        this.selectedType = flagType;
        this.createForm = template.render();

        // TODO: See https://github.com/CTFd/CTFd/issues/1779
        if (this.createForm.includes("<script")) {
          setTimeout(() => {
            $(`<div>` + this.createForm + `</div>`)
              .find("script")
              .each(function() {
                eval($(this).html());
              });
          }, 100);
        }
      });
    },
    loadTypes: function() {
      CTFd.fetch("/api/v1/flags/types", {
        method: "GET"
      })
        .then(response => {
          return response.json();
        })
        .then(response => {
          this.types = response.data;
        });
    },
    submitFlag: function(event) {
      let form = $(event.target);
      let params = form.serializeJSON(true);
      params["challenge"] = this.$props.challenge_id;

      CTFd.fetch("/api/v1/flags", {
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
        .then(_response => {
          this.$emit("refreshFlags", this.$options.name);
        });
    }
  },
  created() {
    this.loadTypes();
  }
};
</script>

<style scoped></style>
