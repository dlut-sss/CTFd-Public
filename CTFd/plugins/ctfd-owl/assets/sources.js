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

$(".delete-source").click(function (e) {
    e.preventDefault();
    let foldername = $(this).attr("data-folder-name");


    CTFd.ui.ezq.ezQuery({
        title: language("Delete source","删除题目源文件"),
        body: language(`Are you sure you want to delete ${foldername}?`,`你确定要删除${foldername}的题目源文件吗？`),
        success: async function () {
            let response = await CTFd.fetch(`/plugins/ctfd-owl/admin/delete?name=${foldername}`, {
                method: "GET"
            })
            response = await response.json()
            if (response.success === true){
                window.location.reload()
            }else{
                CTFd.ui.ezq.ezToast({
                    title: language("Error!",'出现错误！'),
                    body: language("Delete Source Failed!",'题目源文件删除失败！')
                });
            }
        }
    });
});

$(".download-all").click(function (e) {
    e.preventDefault();

    window.open("/plugins/ctfd-owl/admin/downloadAll","_blank")
});