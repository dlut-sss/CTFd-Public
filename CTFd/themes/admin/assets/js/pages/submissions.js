import "./main";
import CTFd from "core/CTFd";
import $ from "jquery";
import { htmlEntities } from "core/utils";
import { ezQuery } from "core/ezq";

function deleteCorrectSubmission(_event) {
  const key_id = $(this).data("submission-id");
  const $elem = $(this)
    .parent()
    .parent();
  const chal_name = $elem
    .find(".chal")
    .text()
    .trim();
  const team_name = $elem
    .find(".team")
    .text()
    .trim();

  const row = $(this)
    .parent()
    .parent();

  ezQuery({
    title: "删除提交",
    body: "您确定要删除 {0} 对于题目 {1} 的正确提交吗".format(
      "<strong>" + htmlEntities(team_name) + "</strong>",
      "<strong>" + htmlEntities(chal_name) + "</strong>"
    ),
    success: function() {
      CTFd.api
        .delete_submission({ submissionId: key_id })
        .then(function(response) {
          if (response.success) {
            row.remove();
          }
        });
    }
  });
}

function deleteSelectedSubmissions(_event) {
  let submissionIDs = $("input[data-submission-id]:checked").map(function() {
    return $(this).data("submission-id");
  });
  let target = submissionIDs.length === 1 ? "个提交" : "个提交";

  ezQuery({
    title: "删除提交",
    body: `你确定要删除${submissionIDs.length} ${target}?`,
    success: function() {
      const reqs = [];
      for (var subId of submissionIDs) {
        reqs.push(CTFd.api.delete_submission({ submissionId: subId }));
      }
      Promise.all(reqs).then(_responses => {
        window.location.reload();
      });
    }
  });
}

$(() => {
  $(".delete-correct-submission").click(deleteCorrectSubmission);
  $("#submission-delete-button").click(deleteSelectedSubmissions);
});
