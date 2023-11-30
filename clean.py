import glob
import os

static_js_dirs = [
    "CTFd/themes/pages-remastered/static/js/**/*.dev.js",
    "CTFd/themes/pages-remastered/static/js/**/*.min.js",
    "CTFd/themes/pages-remastered/static/js/**/*.min.js.LICENSE.txt",
    "CTFd/themes/competition/static/js/**/*.dev.js",
    "CTFd/themes/competition/static/js/**/*.min.js",
    "CTFd/themes/competition/static/js/**/*.min.js.LICENSE.txt",
    "CTFd/themes/core/static/js/**/*.dev.js",
    "CTFd/themes/core/static/js/**/*.min.js",
    "CTFd/themes/core/static/js/**/*.min.js.LICENSE.txt",
    "CTFd/themes/admin/static/js/**/*.dev.js",
    "CTFd/themes/admin/static/js/**/*.min.js",
    "CTFd/themes/admin/static/js/**/*.min.js.LICENSE.txt",
]

for js_dir in static_js_dirs:
    for path in glob.glob(js_dir, recursive=True):
        if os.path.isfile(path):
            os.remove(path)

static_css_dirs = [
    "CTFd/themes/pages-remastered/static/css/**/*.dev.css",
    "CTFd/themes/pages-remastered/static/css/**/*.min.css",
    "CTFd/themes/competition/static/css/**/*.dev.css",
    "CTFd/themes/competition/static/css/**/*.min.css",
    "CTFd/themes/core/static/css/**/*.dev.css",
    "CTFd/themes/core/static/css/**/*.min.css",
    "CTFd/themes/admin/static/css/**/*.dev.css",
    "CTFd/themes/admin/static/css/**/*.min.css",
]

for css_dir in static_css_dirs:
    for path in glob.glob(css_dir, recursive=True):
        if os.path.isfile(path):
            os.remove(path)
