import glob
import os

static_js_dirs = [
    "CTFd/themes/pages-remastered/static/js/**/*.min.js.LICENSE.txt",
    "CTFd/themes/competition/static/js/**/*.min.js.LICENSE.txt",
    "CTFd/themes/core/static/js/**/*.min.js.LICENSE.txt",
    "CTFd/themes/admin/static/js/**/*.min.js.LICENSE.txt",
]

for js_dir in static_js_dirs:
    for path in glob.glob(js_dir, recursive=True):
        if os.path.isfile(path):
            os.remove(path)