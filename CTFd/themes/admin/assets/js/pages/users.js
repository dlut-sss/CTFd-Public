import "./main";
import CTFd from "core/CTFd";
import $ from "jquery";
import { ezAlert, ezQuery } from "core/ezq";

function deleteSelectedUsers(_event) {
  let userIDs = $("input[data-user-id]:checked").map(function() {
    return $(this).data("user-id");
  });
  let target = userIDs.length === 1 ? "个用户" : "个用户";

  ezQuery({
    title: "删除用户",
    body: `你确定要删除${userIDs.length} ${target}?`,
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
    title: "编辑用户",
    body: $(`
    <form id="users-bulk-edit">
      <div class="form-group">
        <label>认证状态</label>
        <select name="verified" data-initial="">
          <option value="">--</option>
          <option value="true">已认证</option>
          <option value="false">未认证</option>
        </select>
      </div>
      <div class="form-group">
        <label>封禁状态</label>
        <select name="banned" data-initial="">
          <option value="">--</option>
          <option value="true">已封禁</option>
          <option value="false">未封禁</option>
        </select>
      </div>
      <div class="form-group">
        <label>是否隐藏</label>
        <select name="hidden" data-initial="">
          <option value="">--</option>
          <option value="true">隐藏</option>
          <option value="false">显示</option>
        </select>
      </div>
    </form>
    `),
    button: "提交",
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
