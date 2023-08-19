import "./main";
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

function reset(event) {
  event.preventDefault();
  ezQuery({
    title: language("Reset CTF?","重置平台？"),
    body: language("Are you sure you want to reset your CTFd instance?","您确定要重置您的 CTFd 实例吗？"),
    success: function() {
      $("#reset-ctf-form")
        .off("submit")
        .submit();
    }
  });
}

$(() => {
  $("#reset-ctf-form").submit(reset);
});
