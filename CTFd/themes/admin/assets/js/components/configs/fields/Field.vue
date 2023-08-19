<template>
  <div class="border-bottom">
    <div>
      <button
        type="button"
        class="close float-right"
        aria-label="Close"
        @click="deleteField()"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>

    <div class="row">
      <div class="col-md-3">
        <div class="form-group">
          <label>{{ language("Field Type","字段类型") }}</label>
          <select
            class="form-control custom-select"
            v-model.lazy="field.field_type"
          >
            <option value="text">{{ language("Text Field","文本域") }}</option>
            <option value="boolean">{{ language("Checkbox","复选框") }}</option>
          </select>
          <small class="form-text text-muted"
            >{{ language("Type of field shown to the user","显示给用户的字段类型") }}</small
          >
        </div>
      </div>
      <div class="col-md-9">
        <div class="form-group">
          <label>{{ language("Field Name","字段名称") }}</label>
          <input type="text" class="form-control" v-model.lazy="field.name" />
          <small class="form-text text-muted">{{ language("Field name","字段名称") }}</small>
        </div>
      </div>

      <div class="col-md-12">
        <div class="form-group">
          <label>{{ language("Field Description","字段说明") }}</label>
          <input
            type="text"
            class="form-control"
            v-model.lazy="field.description"
          />
          <small id="emailHelp" class="form-text text-muted"
            >
            {{ language("Field Description","字段说明") }}</small
          >
        </div>
      </div>

      <div class="col-md-12">
        <div class="form-check">
          <label class="form-check-label">
            <input
              class="form-check-input"
              type="checkbox"
              v-model.lazy="field.editable"
            />
            {{ language("Editable by user in profile","用户可在个人资料中编辑") }}
          </label>
        </div>
        <div class="form-check">
          <label class="form-check-label">
            <input
              class="form-check-input"
              type="checkbox"
              v-model.lazy="field.required"
            />
            {{ language("Required on registration","注册时需要填写") }}
          </label>
        </div>
        <div class="form-check">
          <label class="form-check-label">
            <input
              class="form-check-input"
              type="checkbox"
              v-model.lazy="field.public"
            />
            {{ language("Shown on public profile","显示在公开资料上") }}
          </label>
        </div>
      </div>
    </div>

    <div class="row pb-3">
      <div class="col-md-12">
        <div class="d-block">
          <button
            class="btn btn-sm btn-success btn-outlined float-right"
            type="button"
            @click="saveField()"
          >
            {{ language("Save","保存") }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import CTFd from "core/CTFd";
import { ezToast } from "core/ezq";

export default {
  props: {
    index: Number,
    initialField: Object
  },
  data: function() {
    return {
      field: this.initialField
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
    persistedField: function() {
      // We're using Math.random() for unique IDs so new items have IDs < 1
      // Real items will have an ID > 1
      return this.field.id >= 1;
    },
    saveField: function() {
      let body = this.field;
      if (this.persistedField()) {
        CTFd.fetch(`/api/v1/configs/fields/${this.field.id}`, {
          method: "PATCH",
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json"
          },
          body: JSON.stringify(body)
        })
          .then(response => {
            return response.json();
          })
          .then(response => {
            if (response.success === true) {
              this.field = response.data;
              ezToast({
                title: this.language("Success","成功"),
                body: this.language("Field has been updated!","字段更新完成！"),
                delay: 1000
              });
            }
          });
      } else {
        CTFd.fetch(`/api/v1/configs/fields`, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json"
          },
          body: JSON.stringify(body)
        })
          .then(response => {
            return response.json();
          })
          .then(response => {
            if (response.success === true) {
              this.field = response.data;
              ezToast({
                title: this.language("Success","成功"),
                body: this.language("Field has been created!","字段创建成功！"),
                delay: 1000
              });
            }
          });
      }
    },
    deleteField: function() {
      if (confirm(this.language("Are you sure you'd like to delete this field?","你确定你要删除这个字段吗？"))) {
        if (this.persistedField()) {
          CTFd.fetch(`/api/v1/configs/fields/${this.field.id}`, {
            method: "DELETE",
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
              if (response.success === true) {
                this.$emit("remove-field", this.index);
              }
            });
        } else {
          this.$emit("remove-field", this.index);
        }
      }
    }
  }
};
</script>

<style scoped></style>
