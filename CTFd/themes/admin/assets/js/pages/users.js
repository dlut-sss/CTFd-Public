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

function deleteSelectedUsers(_event) {
  let userIDs = $("input[data-user-id]:checked").map(function() {
    return $(this).data("user-id");
  });
  let target = userIDs.length === 1 ? language(" user","个用户") : language(" users","个用户");

  ezQuery({
    title: language("Delete Users","删除用户"),
    body: language("Are you sure you want to delete ","你确定要删除")+`${userIDs.length}${target}?`,
    success: function() {
      const reqs = [];
      for (var userID of userIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/users/${userID}`, {
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

function bulkEditUsers(_event) {
  let userIDs = $("input[data-user-id]:checked").map(function() {
    return $(this).data("user-id");
  });

  ezAlert({
    title: language("Edit Users","编辑用户"),
    body: $(`
    <form id="users-bulk-edit">
      <div class="form-group">
        <label>`+language("verified","已验证")+`</label>
        <select name="verified" data-initial="">
          <option value="">--</option>
          <option value="true">`+language("True","是")+`</option>
          <option value="false">`+language("False","否")+`</option>
        </select>
      </div>
      <div class="form-group">
        <label>`+language("Banned","已封禁")+`</label>
        <select name="banned" data-initial="">
          <option value="">--</option>
          <option value="true">`+language("True","是")+`</option>
          <option value="false">`+language("False","否")+`</option>
        </select>
      </div>
      <div class="form-group">
        <label>`+language("Hidden","已隐藏")+`</label>
        <select name="hidden" data-initial="">
          <option value="">--</option>
          <option value="true">`+language("True","是")+`</option>
          <option value="false">`+language("False","否")+`</option>
        </select>
      </div>
    </form>
    `),
    button: language("Submit","提交"),
    success: function() {
      let data = $("#users-bulk-edit").serializeJSON(true);
      const reqs = [];
      for (var userID of userIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/users/${userID}`, {
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
  $("#users-delete-button").click(deleteSelectedUsers);
  $("#users-edit-button").click(bulkEditUsers);
});
