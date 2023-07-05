import "./main";
import CTFd from "core/CTFd";
import $ from "jquery";
import { ezQuery } from "core/ezq";

function deleteSelectedUsers(_event) {
  let pageIDs = $("input[data-page-id]:checked").map(function() {
    return $(this).data("page-id");
  });
  let target = "页面";

  ezQuery({
    title: "删除页面",
    body: `你确定要删除 ${pageIDs.length} ${target}吗?`,
    success: function() {
      const reqs = [];
      for (var pageID of pageIDs) {
        reqs.push(
          CTFd.fetch(`/api/v1/pages/${pageID}`, {
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

$(() => {
  $("#pages-delete-button").click(deleteSelectedUsers);
});
