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
