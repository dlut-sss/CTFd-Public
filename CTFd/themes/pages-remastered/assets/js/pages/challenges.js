import "./main";
import "bootstrap/js/dist/tab";
import {ezAlert, ezQuery} from "../ezq";
import {htmlEntities} from "../utils";
import dayjs from "dayjs";
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import relativeTime from "dayjs/plugin/relativeTime";
import $ from "jquery";
import CTFd from "../CTFd";
import config from "../config";
import hljs from "highlight.js";
import {ezToast} from "core/ezq";

dayjs.extend(relativeTime);

CTFd._internal.challenge = {};
let challenges = [];
let solves = [];
let pages = [];

function getCookieForLanguage(name) {
  const cookies = document.cookie.split('; ');
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.split('=');
    if (cookieName === name) {
      return decodeURIComponent(cookieValue);
    }
  }
  return null;
}

// 判断元素是否在视窗内
function isElementInViewport(el) {
  var rect = el.getBoundingClientRect();
  return (
      rect.top >= 0 &&
      rect.bottom <= (window.innerHeight || document.documentElement.clientHeight)
  );
}

function scrollToElementIfNeeded(el) {
  if (!isElementInViewport(el)) {
    var windowHeight = window.innerHeight || document.documentElement.clientHeight;
    var scrollToPosition = el.getBoundingClientRect().top + window.scrollY - (windowHeight / 3);
    window.scrollTo({
      top: scrollToPosition,
      behavior: 'smooth' // 可以设置为 'auto' 或 'smooth'，以控制滚动效果
    });
  }
}

function switchToCategory(chal) {
  //切换到所在页面
  const page = chal.category;
  const pageid = page.replace(/ /g, "-").hashCode();
  const pagebarid= "#{0}-page-row".format(pageid);
  $("#pages-board").find(".active").removeClass("active");
  $("#pages-board").find(pagebarid).addClass("active").trigger("shown.bs.tab")

  const id = chal.name.replace(/ /g, "-").hashCode()
  scrollToElementIfNeeded($.find("#"+id)[0])
}

const loadChal = id => {
  const chal = $.grep(challenges, chal => chal.id == id)[0];

  switchToCategory(chal)

  if (chal.type === "hidden") {
    ezAlert({
      title: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Challenge Hidden!" : "题目已隐藏！"),
      body: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "You haven't unlocked this challenge yet!" : "你尚未解锁这个题目！"),
      button: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Got it!" : "好的！")
    });
    return;
  }

  displayChal(chal);
};

const loadChalByName = name => {
  if (name.includes("-page-row")){
    const pagebar_id= "#{0}".format(name);
    if ($("#pages-board").find(pagebar_id).length!==0){
      $("#pages-board").find(".active").removeClass("active");
      $("#pages-board").find(pagebar_id).addClass("active").trigger("shown.bs.tab");
      const catid = name.split("-page-row")[0];
      var element = $('#{0}-row'.format(catid))[0];
      var paddingTop = 28; // 你想要的上边距值
      window.scrollTo({
        top: $(element).offset().top - paddingTop,
        behavior: 'smooth'
      });
      return;
    }
  }

  let idx = name.lastIndexOf("-");
  let pieces = [name.slice(0, idx), name.slice(idx + 1)];
  let id = pieces[1];
  const chal = $.grep(challenges, chal => chal.id == id)[0];

  switchToCategory(chal)

  displayChal(chal);
};

const displayChal = chal => {
  return Promise.all([
    CTFd.api.get_challenge({ challengeId: chal.id }),
    $.getScript(config.urlRoot + chal.script),
    $.get(config.urlRoot + chal.template)
  ]).then(responses => {
    const challenge = CTFd._internal.challenge;

    $("#challenge-window").empty();

    // Inject challenge data into the plugin
    challenge.data = responses[0].data;

    // Call preRender function in plugin
    challenge.preRender();

    // Build HTML from the Jinja response in API
    $("#challenge-window").append(responses[0].data.view);

    $("#challenge-window #challenge-input").addClass("form-control");
    $("#challenge-window #challenge-submit").addClass(
      "btn btn-md btn-outline-secondary float-right"
    );

    let modal = $("#challenge-window").find(".modal-dialog");
    if (
      window.init.theme_settings &&
      window.init.theme_settings.challenge_window_size
    ) {
      switch (window.init.theme_settings.challenge_window_size) {
        case "sm":
          modal.addClass("modal-sm");
          break;
        case "lg":
          modal.addClass("modal-lg");
          break;
        case "xl":
          modal.addClass("modal-xl");
          break;
        default:
          break;
      }
    }

    $(".challenge-solves").click(function(_event) {
      getSolves($("#challenge-id").val());
    });
    $(".nav-tabs a").click(function(event) {
      event.preventDefault();
      $(this).tab("show");
    });

    // Handle modal toggling
    $("#challenge-window").on("hide.bs.modal", function(_event) {
      $("#challenge-input").removeClass("wrong");
      $("#challenge-input").removeClass("correct");
      $("#incorrect-key").slideUp();
      $("#correct-key").slideUp();
      $("#already-solved").slideUp();
      $("#too-fast").slideUp();
    });

    $(".load-hint").on("click", function(_event) {
      loadHint($(this).data("hint-id"));
    });

    $("#challenge-submit").click(function(event) {
      event.preventDefault();
      $("#challenge-submit").addClass("disabled-button");
      $("#challenge-submit").prop("disabled", true);
      CTFd._internal.challenge
        .submit()
        .then(renderSubmissionResponse)
        .then(loadChals)
        .then(markSolves);
    });

    $("#challenge-input").keyup(event => {
      if (event.keyCode == 13) {
        $("#challenge-submit").click();
      }
    });

    challenge.postRender();

    $("#challenge-window")
      .find("pre code")
      .each(function(_idx) {
        hljs.highlightBlock(this);
      });

    window.location.replace(
      window.location.href.split("#")[0] + `#${chal.name}-${chal.id}`
    );
    $("#challenge-window").modal();
  });
};

function renderSubmissionResponse(response) {
  const result = response.data;

  const result_message = $("#result-message");
  const result_notification = $("#result-notification");
  const answer_input = $("#challenge-input");
  result_notification.removeClass();
  result_message.text(result.message);

  const next_btn = $(
    `<div class='col-md-12 pb-3'><button class='btn btn-info w-100'>`+(getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Next Challenge" : "下一题")+`</button></div>`
  ).click(function() {
    $("#challenge-window").modal("toggle");
    setTimeout(function() {
      loadChal(CTFd._internal.challenge.data.next_id);
    }, 500);
  });

  if (result.status === "authentication_required") {
    window.location =
      CTFd.config.urlRoot +
      "/login?next=" +
      CTFd.config.urlRoot +
      window.location.pathname +
      window.location.hash;
    return;
  } else if (result.status === "incorrect") {
    // Incorrect key
    result_notification.addClass(
      "alert alert-danger alert-dismissable text-center"
    );
    result_notification.slideDown();

    answer_input.removeClass("correct");
    answer_input.addClass("wrong");
    setTimeout(function() {
      answer_input.removeClass("wrong");
    }, 3000);
  } else if (result.status === "correct") {
    // Challenge Solved
    result_notification.addClass(
      "alert alert-success alert-dismissable text-center"
    );
    result_notification.slideDown();

    if (
      $(".challenge-solves")
        .text()
        .trim()
    ) {
      // Only try to increment solves if the text isn't hidden
      $(".challenge-solves").text(
        parseInt(
          $(".challenge-solves")
            .text()
            .split(" ")[0]
        ) +
          1 +
          (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? " Solves" : "人解出")
      );
    }

    answer_input.val("");
    answer_input.removeClass("wrong");
    answer_input.addClass("correct");

    if (CTFd._internal.challenge.data.next_id) {
      $(".submit-row").html(next_btn);
    }
  } else if (result.status === "already_solved") {
    // Challenge already solved
    result_notification.addClass(
      "alert alert-info alert-dismissable text-center"
    );
    result_notification.slideDown();

    answer_input.addClass("correct");

    if (CTFd._internal.challenge.data.next_id) {
      $(".submit-row").html(next_btn);
    }
  } else if (result.status === "paused") {
    // CTF is paused
    result_notification.addClass(
      "alert alert-warning alert-dismissable text-center"
    );
    result_notification.slideDown();
  } else if (result.status === "ratelimited") {
    // Keys per minute too high
    result_notification.addClass(
      "alert alert-warning alert-dismissable text-center"
    );
    result_notification.slideDown();

    answer_input.addClass("too-fast");
    setTimeout(function() {
      answer_input.removeClass("too-fast");
    }, 3000);
  }
  setTimeout(function() {
    $(".alert").slideUp();
    $("#challenge-submit").removeClass("disabled-button");
    $("#challenge-submit").prop("disabled", false);
  }, 3000);
}

function markSolves() {
  challenges.map(challenge => {
    if (challenge.solved_by_me) {
      const btn = $(`button[value="${challenge.id}"]`);
      if (!btn.find('i.fas.fa-check').length) { // Check if the i element with classes 'fas' and 'fa-check' does not exist
        btn.addClass("solved-challenge");
        btn.append("<i class='fas fa-check'></i>");
      }
    }
  });
}

function getSolves(id) {
  return CTFd.api.get_challenge_solves({ challengeId: id }).then(response => {
    const data = response.data;
    $(".challenge-solves").text(parseInt(data.length) + (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? " Solves" : "人解出"));
    const box = $("#challenge-solves-names");
    box.empty();
    for (let i = 0; i < data.length; i++) {
      const id = data[i].account_id;
      const name = data[i].name;
      const date = dayjs(data[i].date).fromNow();
      const account_url = data[i].account_url;
      box.append(
        '<tr><td><a href="{0}">{2}</td><td>{3}</td></tr>'.format(
          account_url,
          id,
          htmlEntities(name),
          date
        )
      );
    }
  });
}

function sort_challenges(challenges) {
  const priorityCategories = ['PWN', 'REVERSE', 'WEB', 'CRYPTO', 'MISC', 'OSINT', 'IOT'];

  // 提取并排序优先列表中的对象
  const priorityObjects = challenges.filter(obj => priorityCategories.includes(obj.category))
      .sort((a, b) => priorityCategories.indexOf(a.category.toUpperCase()) - priorityCategories.indexOf(b.category.toUpperCase()));

  // 提取剩余的对象并按照 category 属性排序
  const remainingObjects = challenges.filter(obj => !priorityCategories.includes(obj.category))
      .sort((a, b) => {
        const categoryA = a.category.toUpperCase();
        const categoryB = b.category.toUpperCase();
        if (categoryA < categoryB) {
          return -1;
        }
        if (categoryA > categoryB) {
          return 1;
        }
        return 0;
      });

  // 合并两个排好序的数组
  return [...priorityObjects, ...remainingObjects];
}

function loadChals() {
  return CTFd.api.get_challenge_list().then(function(response) {
    const $challenges_board = $("#challenges-board");
    const $pages_board = $("#pages-board");
    challenges = response.data;

    try {
      challenges = sort_challenges(challenges)
    } catch (error) {
      console.warn(error)
    }

    if (challenges.length === 0)
    {
      getCookieForLanguage("Scr1wCTFdLanguage") === "en" ?
          ezToast({
            title: 'Auto refresh failed',
            body: 'Challenge data is empty!'
          }) : ezToast({
            title: '自动刷新失败',
            body: '题目数据为空！'
          });
      return;
    }

    $challenges_board.empty();
    $challenges_board.addClass("tab-content");

    //循环获取所有类别，并设置导航栏
    for (let i = 0; i <= challenges.length - 1; i++) {
      const chalinfo = challenges[i];
      if ($.inArray(chalinfo.category, pages) == -1) {
        const page = chalinfo.category;
        pages.push(page);
        const pageid = page.replace(/ /g, "-").hashCode();
        const pagerow = $(
            '<a ' +
            'id="{0}-page-row" class="nav-link challenge-nav-link" '.format(pageid) +
            'data-toggle="tab" role="tab" href="#{0}-page-row"'.format(pageid) +
            '>' + page.slice(0, 15) + "</a>"
        );
        if (pages.length === 1) pagerow.addClass('active');
        //第一个默认显示

        pagerow.on('shown.bs.tab', function () {
          $challenges_board
              .find(".active")
              .removeClass("active");
          //隐藏当前显示的panel
          $challenges_board
              .find("#{0}-row".format(pageid))
              .addClass('active');
          //显示目标panel
        });

        $pages_board.append(pagerow);
      }
    }

    //不重新遍历数据，用所有pages生成tab
    for (let i = 0; i <= pages.length - 1; i++) {
        const category = pages[i];
        const categoryid = category.replace(/ /g, "-").hashCode();
        const categoryrow = $(
          "" +
            '<div id="{0}-row" class="pt-5 tab-pane" role="tabpanel">'.format(categoryid) +
            '<div class="category-header col-md-12 mb-3">' +
            "</div>" +
            '<div class="category-challenges col-md-12" id="{0}-base">'.format(categoryid) +
            '<div class="challenges-row col-md-12" id="{0}-base-row" style="display:none">'.format(categoryid) +"<div><h4>"+(getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Uncategorized" : "未分类")+"</h4></div></div>"+
            '</div>' +
            "</div>"
        );
        categoryrow
          .find(".category-header")
          .append($("<h3>" + category + "</h3>"));

        $challenges_board.append(categoryrow);
    }

    for (let i = 0; i <= challenges.length - 1; i++) {
      const chalinfo = challenges[i];
      const chalid = chalinfo.name.replace(/ /g, "-").hashCode();
      const catid = chalinfo.category.replace(/ /g, "-").hashCode();
      const chalwrap = $(
        "<div id='{0}' class='col-md-3 d-inline-block challenge-button-container' ></div>".format(chalid)
      );
      let chalbutton;

      if (solves.indexOf(chalinfo.id) == -1) {
        chalbutton = $(
          "<button class='btn btn-dark challenge-button w-100 text-truncate pt-3 pb-3 mb-2 challenge-button-content' value='{0}'></button>".format(
            chalinfo.id
          )
        );
      } else {
        chalbutton = $(
          "<button class='btn btn-dark challenge-button solved-challenge w-100 text-truncate pt-3 pb-3 mb-2 challenge-button-content' value='{0}'><i class='fas fa-check'></i></button>".format(
            chalinfo.id
          )
        );
      }

      const chalheader = $("<p>{0}</p>".format(chalinfo.name));
      const chalscore = $("<span>{0}</span>".format(chalinfo.value));
      for (let j = 0; j < chalinfo.tags.length; j++) {
        const tag = "tag-" + chalinfo.tags[j].value.replace(/ /g, "-");
        chalwrap.addClass(tag);
      }

      chalbutton.append(chalheader);
      chalbutton.append(chalscore);
      chalwrap.append(chalbutton);

      //处理子类别
      const subcategory = chalinfo.subcategory;
      if (subcategory === undefined || subcategory === null || subcategory === ""){
          $("#" + catid + "-row")
              .find(".category-challenges")
              .find("#"+catid+"-base-row")
              .removeAttr("style");

          $("#" + catid + "-row")
              .find(".category-challenges")
              .find("#"+catid+"-base-row")
              .append(chalwrap);
      }
      else {
        const subcatid = subcategory.replace(/ /g, "-").hashCode();
        const tarid = catid+"-"+subcatid+"-row"
        if(document.getElementById(tarid)==null)
        {
          $("#" + catid + "-row")
              .find(".category-challenges")
              .append("<div class=\"challenges-row col-md-12\" id=\"{0}\"><div><h4>{1}</h4></div></div>".format(tarid,subcategory))

          $("#"+tarid).append(chalwrap);
        }
        else
        {
          $("#"+tarid).append(chalwrap);
        }
      }
    }

    $(".challenge-button").click(function(_event) {
      loadChal(this.value);
    });
    //维持刷新数据时页面状态
    $pages_board.find(".active").trigger("shown.bs.tab")
  });
}

function update() {
  return loadChals().then(markSolves);
}

$(() => {
  update().then(() => {
    if (window.location.hash.length > 0) {
      loadChalByName(decodeURIComponent(window.location.hash.substring(1)));
    }
  });

  $("#challenge-input").keyup(function(event) {
    if (event.keyCode == 13) {
      $("#challenge-submit").click();
    }
  });

  $(".nav-tabs a").click(function(event) {
    event.preventDefault();
    $(this).tab("show");
  });

  $("#challenge-window").on("hidden.bs.modal", function(_event) {
    $(".nav-tabs a:first").tab("show");
    history.replaceState("", window.document.title, window.location.pathname);
  });

  $(".challenge-solves").click(function(_event) {
    getSolves($("#challenge-id").val());
  });

  $("#challenge-window").on("hide.bs.modal", function(_event) {
    $("#challenge-input").removeClass("wrong");
    $("#challenge-input").removeClass("correct");
    $("#incorrect-key").slideUp();
    $("#correct-key").slideUp();
    $("#already-solved").slideUp();
    $("#too-fast").slideUp();
  });
});
setInterval(update, 300000); // Update every 5 minutes.

const displayHint = data => {
  ezAlert({
    title: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Hint" : "提示"),
    body: data.html,
    button: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Got it!" : "好的！")
  });
};

const displayUnlock = id => {
  ezQuery({
    title: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Unlock Hint?" : "解锁提示？"),
    body: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Are you sure you want to open this hint?" : "您确定要解锁此提示吗？"),
    success: () => {
      const params = {
        target: id,
        type: "hints"
      };
      CTFd.api.post_unlock_list({}, params).then(response => {
        if (response.success) {
          CTFd.api.get_hint({ hintId: id }).then(response => {
            displayHint(response.data);
          });

          return;
        }

        ezAlert({
          title: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Error" : "错误"),
          body: response.errors.score,
          button: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Got it!" : "好的！")
        });
      });
    }
  });
};

const loadHint = id => {
  CTFd.api.get_hint({ hintId: id }).then(response => {
    if (!response.success) {
      let msg = Object.values(response.errors).join("\n");
      alert(msg);
      return;
    }
    if (response.data.content) {
      displayHint(response.data);
      return;
    }

    displayUnlock(id);
  });
};

window.updateChallengeBoard = update;
