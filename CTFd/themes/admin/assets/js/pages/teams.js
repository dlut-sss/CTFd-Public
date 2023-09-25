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

function deleteSelectedTeams(_event) {
  let teamIDs = $("input[data-team-id]:checked").map(function() {
    return $(this).data("team-id");
  });
  let target = teamIDs.length === 1 ? "team" : "teams";

  ezQuery({
    title: language("Delete Teams","删除队伍"),
    body: language(`Are you sure you want to delete ${teamIDs.length} ${target}?`,`你确定要删除${teamIDs.length}个队伍吗？`),
    success: function() {
      const reqs = [];
      for (var teamID of teamIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/teams/${teamID}`, {
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

function bulkEditTeams(_event) {
  let teamIDs = $("input[data-team-id]:checked").map(function() {
    return $(this).data("team-id");
  });

  ezAlert({
    title: language("Edit Teams","编辑队伍"),
    body: language($(`
    <form id="teams-bulk-edit">
      <div class="form-group">
        <label>Banned</label>
        <select name="banned" data-initial="">
          <option value="">--</option>
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      </div>
      <div class="form-group">
        <label>Hidden</label>
        <select name="hidden" data-initial="">
          <option value="">--</option>
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      </div>
    </form>
    `),$(`
    <form id="teams-bulk-edit">
      <div class="form-group">
        <label>封禁状态</label>
        <select name="banned" data-initial="">
          <option value="">--</option>
          <option value="true">已封禁</option>
          <option value="false">未封禁</option>
        </select>
      </div>
      <div class="form-group">
        <label>显示状态</label>
        <select name="hidden" data-initial="">
          <option value="">--</option>
          <option value="true">已隐藏</option>
          <option value="false">未隐藏</option>
        </select>
      </div>
    </form>
    `)),
    button: language("Submit","确定"),
    success: function() {
      let data = $("#teams-bulk-edit").serializeJSON(true);
      const reqs = [];
      for (var teamID of teamIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/teams/${teamID}`, {
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
  $("#teams-delete-button").click(deleteSelectedTeams);
  $("#teams-edit-button").click(bulkEditTeams);
});
