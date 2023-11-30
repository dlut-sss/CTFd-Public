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

$(".delete-backup").click(function (e) {
    e.preventDefault();
    let filename = $(this).attr("data-filename");


    CTFd.ui.ezq.ezQuery({
        title: language("Delete Backup","删除备份"),
        body: language(`Are you sure you want to delete ${filename}?`,`你确定要删除${filename}的备份吗？`),
        success: async function () {
            let response = await CTFd.fetch(`/plugins/backup/admin/delete?name=${filename}`, {
                method: "GET"
            })
            response = await response.json()
            if (response.success === true){
                window.location.reload()
            }else{
                CTFd.ui.ezq.ezToast({
                    title: language("Error!",'出现错误！'),
                    body: language("Delete Backup Failed!",'备份文件删除失败！')
                });
            }
        }
    });
});

$(".backup-now").click(async function (e) {
    e.preventDefault();
    let response = await CTFd.fetch(`/plugins/backup/admin/backupNow`, {
        method: "GET"
    })
    response = await response.json()
    if (response.success === true) {
        window.location.reload()
    } else {
        CTFd.ui.ezq.ezToast({
            title: language("Error!", '出现错误！'),
            body: language("Backup Failed!", '备份文件失败！')
        });
    }
});