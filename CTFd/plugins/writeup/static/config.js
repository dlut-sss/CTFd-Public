const $ = CTFd.lib.$;

$(".config-section > form:not(.form-upload)").submit(async function (event) {
    event.preventDefault();
    const obj = $(this).serializeJSON();
    const params = {};
    for (let x in obj) {
        if (obj[x] === "true") {
            params[x] = true;
        } else if (obj[x] === "false") {
            params[x] = false;
        } else {
            params[x] = obj[x];
        }
    }

    await CTFd.api.patch_config_list({}, params);
    location.reload();
});

$('a[data-toggle="tab"]').on("shown.bs.tab", function(e) {
    sessionStorage.setItem("activeTab", $(e.target).attr("href"));
});

$('a[data-toggle="pill"]').on("shown.bs.tab", function(e) {
    sessionStorage.setItem("activeTab", $(e.target).attr("href"));
});

let activeTab = sessionStorage.getItem("activeTab");
if (activeTab) {
    let target = $(
        `.nav-tabs a[href="${activeTab}"], .nav-pills a[href="${activeTab}"]`
    );
    if (target.length) {
        target.tab("show");
    } else {
        sessionStorage.removeItem("activeTab");
    }
}