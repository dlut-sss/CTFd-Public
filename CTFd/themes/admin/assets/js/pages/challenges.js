import "./main";
import CTFd from "core/CTFd";
import $ from "jquery";
import { ezAlert, ezQuery } from "core/ezq";

function language(en,zh) {
  const cookies = document.cookie.split('; ');
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.split('=');
    if (cookieName === "Scr1wCTFdLanguage") {
      return (decodeURIComponent(cookieValue) === "en" ? en : zh);
    }
  }
  return zh;
}

function deleteSelectedChallenges(_event) {
  let challengeIDs = $("input[data-challenge-id]:checked").map(function() {
    return $(this).data("challenge-id");
  });
  let target = challengeIDs.length === 1 ? "challenge" : "challenges";

  ezQuery({
    title: language("Delete Challenges","删除题目"),
    body: language(`Are you sure you want to delete ${challengeIDs.length} ${target}?`,`你确定要删除${challengeIDs.length}个题目吗`),
    success: function() {
      const reqs = [];
      for (var chalID of challengeIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/challenges/${chalID}`, {
            method: "DELETE"
          })
        );
      }
      Promise.all(reqs).then(_responses => {
        window.location.reload();
      });
    }
  });
}

function bulkEditChallenges(_event) {
  let challengeIDs = $("input[data-challenge-id]:checked").map(function() {
    return $(this).data("challenge-id");
  });

  ezAlert({
    title: language("Edit Challenges","编辑题目"),
    body: $(language(`
    <form id="challenges-bulk-edit">
      <div class="form-group">
        <label>Category</label>
        <input type="text" name="category" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>Subcategory</label>
        <input type="text" name="subcategory" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>Value</label>
        <input type="number" name="value" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>State</label>
        <select name="state" data-initial="">
          <option value="">--</option>
          <option value="visible">Visible</option>
          <option value="hidden">Hidden</option>
        </select>
      </div>
    </form>
    `,`
    <form id="challenges-bulk-edit">
      <div class="form-group">
        <label>类别</label>
        <input type="text" name="category" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>子类别</label>
        <input type="text" name="subcategory" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>分值</label>
        <input type="number" name="value" data-initial="" value="">
      </div>
      <div class="form-group">
        <label>状态</label>
        <select name="state" data-initial="">
          <option value="">--</option>
          <option value="visible">可见</option>
          <option value="hidden">隐藏</option>
        </select>
      </div>
    </form>`)),
    button: language("Submit","提交"),
    success: function() {
      let data = $("#challenges-bulk-edit").serializeJSON(true);
      const reqs = [];
      for (var chalID of challengeIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/challenges/${chalID}`, {
            method: "PATCH",
            body: JSON.stringify(data)
          })
        );
      }
      Promise.all(reqs).then(_responses => {
        window.location.reload();
      });
    }
  });
}

$(() => {
  $("#challenges-delete-button").click(deleteSelectedChallenges);
  $("#challenges-edit-button").click(bulkEditChallenges);
});
