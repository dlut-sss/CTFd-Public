const $ = CTFd.lib.$;

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

function htmlentities(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function copyToClipboard(event, str) {
    // Select element
    const el = document.createElement('textarea');
    el.value = str;
    el.setAttribute('readonly', '');
    el.style.position = 'absolute';
    el.style.left = '-9999px';
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);

    $(event.target).tooltip({
        title: language("Copied!","复制完成!"),
        trigger: "manual"
    });
    $(event.target).tooltip("show");

    setTimeout(function () {
        $(event.target).tooltip("hide");
    }, 1500);
}

$(".click-copy").click(function (e) {
    copyToClipboard(e, $(this).data("copy"));
})

async function delete_container(user_id) {
    let response = await CTFd.fetch("/api/v1/plugins/ctfd-whale/admin/container?user_id=" + user_id, {
        method: "DELETE",
        credentials: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json"
        }
    });
    response = await response.json();
    return response.success;
}
async function renew_container(user_id) {
    let response = await CTFd.fetch(
        "/api/v1/plugins/ctfd-whale/admin/container?user_id=" + user_id, {
        method: "PATCH",
        credentials: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json"
        }
    });
    response = await response.json();
    return response.success;
}

$('#containers-renew-button').click(function (e) {
    let users = $("input[data-user-id]:checked").map(function () {
        return $(this).data("user-id");
    });
    CTFd.ui.ezq.ezQuery({
        title: language("Renew Container","延期容器"),
        body: language(`Are you sure to renew ${users.length} container(s)?`,`你确定要给选中的 ${users.length} 个容器延期吗?`),
        success: async function () {
            await Promise.all(users.toArray().map((user) => renew_container(user)));
            location.reload();
        }
    });
});

$('#containers-delete-button').click(function (e) {
    let users = $("input[data-user-id]:checked").map(function () {
        return $(this).data("user-id");
    });
    CTFd.ui.ezq.ezQuery({
        title: language("Destroy Container","关闭容器"),
        body: language(`Are you sure to Destroy ${users.length} container(s)?`,`你确定要删除选中的 ${users.length} 个容器吗?`),
        success: async function () {
            await Promise.all(users.toArray().map((user) => delete_container(user)));
            location.reload();
        }
    });
});

$(".delete-container").click(function (e) {
    e.preventDefault();
    let container_id = $(this).attr("container-id");
    let user_id = $(this).attr("user-id");

    CTFd.ui.ezq.ezQuery({
        title: language("Destroy Container","关闭容器"),
        body: language("<span>Are you sure to destroy <strong>container #{0}</strong>?</span>".format(htmlentities(container_id)),"<span>你确定要关闭 <strong>容器 #{0}</strong>吗?</span>".format(htmlentities(container_id))),
        success: async function () {
            await delete_container(user_id);
            location.reload();
        }
    });
});

$(".renew-container").click(function (e) {
    e.preventDefault();
    let container_id = $(this).attr("container-id");
    let user_id = $(this).attr("user-id");

    CTFd.ui.ezq.ezQuery({
        title: language("Renew Container","延期容器"),
        body: language("<span>Are you sure to Renew <strong>container #{0}</strong>?</span>".format(htmlentities(container_id)),"<span>你确定要给 <strong>容器 #{0}</strong>延期吗?</span>".format(htmlentities(container_id))),
        success: async function () {
            await renew_container(user_id);
            location.reload();
        },
    });
});
