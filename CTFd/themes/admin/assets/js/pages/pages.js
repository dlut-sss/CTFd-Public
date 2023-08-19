import "./main";
import CTFd from "core/CTFd";
import $ from "jquery";
import { ezQuery } from "core/ezq";

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
  let pageIDs = $("input[data-page-id]:checked").map(function() {
    return $(this).data("page-id");
  });
  let target = pageIDs.length === 1 ? "page" : "pages";

  ezQuery({
    title: language("Delete Pages","删除页面"),
    body: language(`Are you sure you want to delete ${pageIDs.length} ${target}?`,`你确定要删除${pageIDs.length}个页面吗？`),
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
