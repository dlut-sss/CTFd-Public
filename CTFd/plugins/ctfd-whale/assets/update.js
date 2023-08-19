if ($ === undefined) $ = CTFd.lib.$
$('#submit-key').click(function(e) {
    submitkey($('#chalid').val(), $('#answer').val())
});

$('#submit-keys').click(function(e) {
    e.preventDefault();
    $('#update-keys').modal('hide');
});

$('#limit_max_attempts').change(function() {
    if (this.checked) {
        $('#chal-attempts-group').show();
    } else {
        $('#chal-attempts-group').hide();
        $('#chal-attempts-input').val('');
    }
});

// Markdown Preview
$('#desc-edit').on('shown.bs.tab', function(event) {
    if (event.target.hash == '#desc-preview') {
        var editor_value = $('#desc-editor').val();
        $(event.target.hash).html(
            window.challenge.render(editor_value)
        );
    }
});
$('#new-desc-edit').on('shown.bs.tab', function(event) {
    if (event.target.hash == '#new-desc-preview') {
        var editor_value = $('#new-desc-editor').val();
        $(event.target.hash).html(
            window.challenge.render(editor_value)
        );
    }
});

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

function loadchal(id, update) {
    $.get(script_root + '/admin/chal/' + id, function(obj) {
        $('#desc-write-link').click(); // Switch to Write tab
        if (typeof update === 'undefined')
            $('#update-challenge').modal();
    });
}

function openchal(id) {
    loadchal(id);
}

$(document).ready(function() {
    $('[data-toggle="tooltip"]').tooltip();
});


function UpdateDockerImage(){
    var name = document.getElementById("docker_name_input").value;
    var url = "/plugins/ctfd-whale/admin/image-update?name=" + name;

    CTFd.fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
        }
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
            var e = new Object;
            e.title = (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Success" : "更新成功！");
            e.body = (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Image update command sent!" : "镜像更新命令已发送！");
            CTFd.ui.ezq.ezToast(e)
        } else {
            var e = new Object;
            e.title = (getCookieForLanguage("Scr1wCTFdLanguage") === "en" ? "Fail" : "更新失败！");
            e.body = response.message;
            CTFd.ui.ezq.ezToast(e)
        }
    });
}
