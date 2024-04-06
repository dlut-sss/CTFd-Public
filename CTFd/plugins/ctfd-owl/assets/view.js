CTFd._internal.challenge.data = undefined

CTFd._internal.challenge.renderer = CTFd.lib.markdown();

CTFd._internal.challenge.preRender = function () {
}

CTFd._internal.challenge.render = function (markdown) {
    return CTFd._internal.challenge.renderer.render(markdown);
}

CTFd._internal.challenge.postRender = function () {
    loadInfo();
}

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

CTFd._internal.challenge.submit = function (preview) {
    var challenge_id = parseInt(CTFd.lib.$('#challenge-id').val())
    var submission = CTFd.lib.$('#challenge-input').val()

    var body = {
        'challenge_id': challenge_id,
        'submission': submission,
    }
    var params = {}
    if (preview) {
        params['preview'] = true
    }

    return CTFd.api.post_challenge_attempt(params, body).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response;
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response;
        }
        return response;
    });
};

function loadInfo() {
    var challenge_id = parseInt(CTFd.lib.$('#challenge-id').val());
    var target = "/plugins/ctfd-owl/container?challenge_id={challenge_id}";
    target = target.replace("{challenge_id}", challenge_id);

    var params = {};

    CTFd.fetch(target, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success === false) {
            CTFd.ui.ezq.ezAlert({
                title: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Fail" : "失败"),
                body: response.msg,
                button: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "OK" : "好的")
            });
        } else if (response.remaining_time === undefined) {
            CTFd.lib.$('#owl-panel').html(
                '<h5 class="card-title">' + (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Instance info" : "实例信息") + '</h5><hr>' +
                '<button type="button" class="btn btn-primary card-link" id="owl-button-boot" onclick="CTFd._internal.challenge.boot()">' +
                (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Launch an instance" : "启动题目实例") +
                '</button>'
            );
        } else {
            if (getCookieForLanguage("Scr1wCTFdLanguage") === "en") {
                var panel_html = '<h5 class="card-title">Instance Info</h5><hr>' +
                    '<h6 class="card-subtitle mb-2 text-muted" id="owl-challenge-count-down">Remaining Time: ' + response.remaining_time + 's</h6>';
                if (response.type === 'http') {
                    panel_html += '<p class="card-text">Domain: <br/>' + '<a href="//' + response.domain + '" target="_blank">' + response.domain + '</a></p>';
                } else {
                    panel_html += '<p class="card-text">Domain: <br/>' + '<a href="//' + response.ip + ':' + response.port + '" target="_blank">' + response.ip + ':' + response.port + '</a></p>';
                }
                panel_html += '<button type="button" class="btn btn-danger card-link" id="owl-button-destroy" onclick="CTFd._internal.challenge.destroy()">Destroy</button>' +
                    '<button type="button" class="btn btn-success card-link" id="owl-button-renew" onclick="CTFd._internal.challenge.renew()">Renew</button>';
                CTFd.lib.$('#owl-panel').html(panel_html);

                if (window.t !== undefined) {
                    clearInterval(window.t);
                    window.t = undefined;
                }

                function showAuto() {
                    const origin = CTFd.lib.$('#owl-challenge-count-down')[0].innerHTML;
                    const second = parseInt(origin.split(": ")[1].split('s')[0]) - 1;
                    CTFd.lib.$('#owl-challenge-count-down')[0].innerHTML = 'Remaining Time: ' + second + 's';
                    if (second < 0) {
                        loadInfo();
                    }
                }

                window.t = setInterval(showAuto, 1000);
            } else {
                var panel_html = '<h5 class="card-title">实例信息</h5><hr>' +
                    '<h6 class="card-subtitle mb-2 text-muted" id="owl-challenge-count-down">剩余时间: ' + response.remaining_time + '秒</h6>';
                if (response.type === 'http') {
                    panel_html += '<p class="card-text">域名: <br/>' + '<a href="//' + response.domain + '" target="_blank">' + response.domain + '</a></p>';
                } else {
                    panel_html += '<p class="card-text">域名: <br/>' + '<a href="//' + response.ip + ':' + response.port + '" target="_blank">' + response.ip + ':' + response.port + '</a></p>';
                }
                panel_html += '<button type="button" class="btn btn-danger card-link" id="owl-button-destroy" onclick="CTFd._internal.challenge.destroy()">关闭实例容器</button>' +
                    '<button type="button" class="btn btn-success card-link" id="owl-button-renew" onclick="CTFd._internal.challenge.renew()">延期实例容器</button>';
                CTFd.lib.$('#owl-panel').html(panel_html);

                if (window.t !== undefined) {
                    clearInterval(window.t);
                    window.t = undefined;
                }

                function showAuto() {
                    const origin = CTFd.lib.$('#owl-challenge-count-down')[0].innerHTML;
                    const second = parseInt(origin.split(": ")[1].split('s')[0]) - 1;
                    CTFd.lib.$('#owl-challenge-count-down')[0].innerHTML = '剩余时间: ' + second + '秒';
                    if (second < 0) {
                        loadInfo();
                    }
                }

                window.t = setInterval(showAuto, 1000);
            }
        }
    });
};

function stopShowAuto() {
    // 窗口关闭时停止循环
    CTFd.lib.$("#challenge-window").on("hide.bs.modal", function (event) {
        clearInterval(window.t);
        window.t = undefined;
    });
}

CTFd._internal.challenge.destroy = function () {
    var challenge_id = parseInt(CTFd.lib.$('#challenge-id').val());
    var target = "/plugins/ctfd-owl/container?challenge_id={challenge_id}";
    target = target.replace("{challenge_id}", challenge_id);
    var body = {};
    var params = {};

    CTFd.lib.$('#owl-button-destroy')[0].innerHTML = (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Waiting...." : "正在关闭容器，请等待。。。");
    CTFd.lib.$('#owl-button-destroy')[0].disabled = true;

    CTFd.fetch(target, {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success) {
            loadInfo();
            CTFd.ui.ezq.ezAlert({
                title: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Success" : "操作成功"),
                body: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Your instance has been destroyed!" : "你的容器实例已被关闭!"),
                button: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "OK" : "好的")
            });
            stopShowAuto();
        } else {
            CTFd.lib.$('#owl-button-destroy')[0].innerHTML = (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Destroy Container" : "关闭实例容器");
            CTFd.lib.$('#owl-button-destroy')[0].disabled = false;
            CTFd.ui.ezq.ezAlert({
                title: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Fail" : "操作失败"),
                body: response.msg,
                button: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "OK" : "好的")
            });
        }
    });
};

CTFd._internal.challenge.renew = function () {
    var challenge_id = parseInt(CTFd.lib.$('#challenge-id').val())
    var target = "/plugins/ctfd-owl/container?challenge_id={challenge_id}";
    target = target.replace("{challenge_id}", challenge_id);
    var body = {};
    var params = {};

    CTFd.lib.$('#owl-button-renew')[0].innerHTML = (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Waiting..." : "正在请求延期容器，请等待。。。");
    CTFd.lib.$('#owl-button-renew')[0].disabled = true;

    CTFd.fetch(target, {
        method: 'PATCH',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success) {
            loadInfo();
            CTFd.ui.ezq.ezAlert({
                title: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Success" : "延期成功"),
                body: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Your instance has been renewed!" : "你的实例容器已延期!"),
                button: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "OK" : "好的")
            });
        } else {
            CTFd.lib.$('#owl-button-renew')[0].innerHTML = "Renew";
            CTFd.lib.$('#owl-button-renew')[0].disabled = false;
            CTFd.ui.ezq.ezAlert({
                title: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Fail" : "延期失败"),
                body: response.msg,
                button: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "OK" : "好的")
            });
        }
    });
};

CTFd._internal.challenge.boot = function () {
    var challenge_id = parseInt(CTFd.lib.$('#challenge-id').val())
    var target = "/plugins/ctfd-owl/container?challenge_id={challenge_id}";
    target = target.replace("{challenge_id}", challenge_id);

    var params = {};

    CTFd.lib.$('#owl-button-boot')[0].innerHTML = (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Waiting..." : "正在启动容器，请等待。。。");
    CTFd.lib.$('#owl-button-boot')[0].disabled = true;

    CTFd.fetch(target, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success) {
            loadInfo();
            CTFd.ui.ezq.ezAlert({
                title: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Success" : "启动成功"),
                body: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Your instance has been deployed!" : "你的实例容器已成功部署!"),
                button: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "OK" : "好的")
            });
        } else {
            CTFd.lib.$('#owl-button-boot')[0].innerHTML = (getCookieForLanguage("Scr1wCTFdLanguage") === "Fail" ? "Launch an instance" : "启动题目实例");
            CTFd.lib.$('#owl-button-boot')[0].disabled = false;
            CTFd.ui.ezq.ezAlert({
                title: (getCookieForLanguage("Scr1wCTFdLanguage") === "Fail" ? "Success" : "启动失败"),
                body: response.msg,
                button: (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "OK" : "好的")
            });
        }
    });
};