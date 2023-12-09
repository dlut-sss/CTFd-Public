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

$(".delete-writeup").click(function (e) {
    e.preventDefault();
    let filename = $(this).attr("data-filename");


    CTFd.ui.ezq.ezQuery({
        title: language("Delete writeup","删除题解"),
        body: language(`Are you sure you want to delete ${filename}?`,`你确定要删除${filename}的题解吗？`),
        success: async function () {
            let response = await CTFd.fetch(`/plugins/writeup/admin/delete?name=${filename}`, {
                method: "GET"
            })
            response = await response.json()
            if (response.success === true){
                window.location.reload()
            }else{
                CTFd.ui.ezq.ezToast({
                    title: language("Error!",'出现错误！'),
                    body: language("Delete writeup Failed!",'题解文件删除失败！')
                });
            }
        }
    });
});

$(".download-all").click(function (e) {
    e.preventDefault();

    window.open("/plugins/writeup/admin/downloadAll","_blank")
});