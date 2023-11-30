import glob
import os

static_js_dirs = [
    "CTFd/themes/pages-remastered/static/js/**/*.dev.js",
    "CTFd/themes/competition/static/js/**/*.dev.js",
    "CTFd/themes/core/static/js/**/*.dev.js",
    "CTFd/themes/admin/static/js/**/*.dev.js",
]

for js_dir in static_js_dirs:
    for path in glob.glob(js_dir, recursive=True):
        if path.endswith(".dev.js"):
            path = path.replace(".dev.js", ".min.js")
            if not os.path.isfile(path):
                with open(path, "a") as file:
                    file.write("//empty file")


static_css_dirs = [
    "CTFd/themes/pages-remastered/static/css/**/*.dev.css",
    "CTFd/themes/competition/static/css/**/*.dev.css",
    "CTFd/themes/core/static/css/**/*.dev.css",
    "CTFd/themes/admin/static/css/**/*.dev.css",
]

for js_dir in static_js_dirs:
    for path in glob.glob(js_dir, recursive=True):
        if path.endswith(".dev.css"):
            path = path.replace(".dev.css", ".min.css")
            if not os.path.isfile(path):
                with open(path, "a") as file:
                    file.write("//empty file")
