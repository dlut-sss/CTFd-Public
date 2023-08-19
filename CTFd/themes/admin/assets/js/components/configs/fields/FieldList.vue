<template>
  <div>
    <!-- You can't use index as :key here b/c Vue is crazy -->
    <!-- https://rimdev.io/the-v-for-key/ -->
    <div class="mb-5" v-for="(field, index) in fields" :key="field.id">
      <Field
        :index="index"
        :initialField.sync="fields[index]"
        @remove-field="removeField"
      />
    </div>

    <div class="row">
      <div class="col text-center">
        <button
          class="btn btn-sm btn-success btn-outlined m-auto"
          type="button"
          @click="addField()"
        >
          {{ language("Add New Field","添加新字段") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import CTFd from "core/CTFd";
import Field from "./Field.vue";

export default {
  name: "FieldList",
  components: {
    Field
  },
  props: {
    type: String
  },
  data: function() {
    return {
      fields: []
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
    loadFields: function() {
      CTFd.fetch(`/api/v1/configs/fields?type=${this.type}`, {
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
          this.fields = response.data;
        });
    },
    addField: function() {
      this.fields.push({
        id: Math.random(),
        type: this.type,
        field_type: "text",
        name: "",
        description: "",
        editable: false,
        required: false,
        public: false
      });
    },
    removeField: function(index) {
      this.fields.splice(index, 1);
      console.log(this.fields);
    }
  },
  created() {
    this.loadFields();
  }
};
</script>
