import sys
import logging
import os
import tempfile
import zipfile
from datetime import datetime
from functools import wraps
from PyPDF2 import PdfReader
from io import BytesIO

from flask_restx import Namespace, Resource
from lxml import etree

import CTFd
from CTFd.plugins import (
    register_plugin_assets_directory,
    register_admin_plugin_menu_bar,
)
from CTFd.utils import config as ctf_config
from CTFd.utils import get_config, set_config
from CTFd.utils import user as current_user
from flask import request, render_template, Blueprint, send_file, redirect, url_for

from ...api import CTFd_API_v1
from ...utils.dates import ctf_started
from ...utils.decorators import admins_only, authed_only
from ...utils.logging import log_simple

logger = logging.getLogger("writeup")


def config(app):
    if not get_config("writeup:setup"):
        for key, val in {
            'enabled': 'false',
            'name': '{user.id}-{user.name}-writeup.pdf',
            'setup': 'true'
        }.items():
            set_config('writeup:' + key, val)


def load(app):
    config(app)
    plugin_name = __name__.split('.')[-1]

    # 初始化日志
    logger_writeup = logging.getLogger("writeup")
    logger_writeup.setLevel(logging.INFO)

    log_dir = app.config["LOG_FOLDER"]
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logs = {
        "writeup": os.path.join(log_dir, "writeup.log"),
    }
    try:
        for log in logs.values():
            if not os.path.exists(log):
                open(log, "a").close()
        writeup_log = logging.handlers.RotatingFileHandler(
            logs["writeup"], maxBytes=10485760, backupCount=5
        )
        logger_writeup.addHandler(writeup_log)
    except IOError:
        pass
    stdout = logging.StreamHandler(stream=sys.stdout)
    logger_writeup.addHandler(stdout)
    logger_writeup.propagate = 0

    register_plugin_assets_directory(
        app,
        base_path=f"/plugins/{plugin_name}/assets",
        endpoint='plugins.writeup.assets')
    register_admin_plugin_menu_bar(title='Writeup',
                                   route='/plugins/writeup/admin/settings')

    page_blueprint = Blueprint("writeup",
                               __name__,
                               template_folder="templates",
                               static_folder="static",
                               url_prefix="/plugins/writeup")

    def format_size(size):
        # Convert bytes to human-readable format
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                break
            size /= 1024.0
        return "{:.2f} {}".format(size, unit)

    @page_blueprint.route('/admin/settings')
    @admins_only
    def admin_list_configs():
        upload_folder = os.path.join(
            os.path.normpath(app.root_path), app.config.get("UPLOAD_FOLDER")
        )
        writeup_folder = os.path.join(upload_folder, "writeups")
        os.makedirs(writeup_folder, exist_ok=True)
        writeup_files = []
        for root, dirs, files in os.walk(writeup_folder):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                file_date = os.path.getctime(file_path)
                writeup_files.append({
                    'name': file,
                    'size': format_size(file_size),
                    'date': datetime.utcfromtimestamp(file_date)
                })
        return render_template('writeup_config.html', writeup_files=writeup_files)

    @page_blueprint.route("/admin/download")
    @admins_only
    def admin_download_writeup():
        upload_folder = os.path.join(
            os.path.normpath(app.root_path), app.config.get("UPLOAD_FOLDER")
        )
        writeup_folder = os.path.join(upload_folder, "writeups")
        os.makedirs(writeup_folder, exist_ok=True)

        writeup_name = request.args.get("name")
        # 构造备份文件的完整路径
        writeup_path = os.path.join(writeup_folder, writeup_name)

        # 检查文件是否存在
        if os.path.exists(writeup_path):
            # 使用send_file发送文件
            return send_file(
                writeup_path,
                as_attachment=True
            )
        else:
            # 文件不存在，可以返回404或其他适当的响应
            return "File not found", 404

    @page_blueprint.route("/admin/downloadAll")
    @admins_only
    def admin_download_all_writeup():
        upload_folder = os.path.join(
            os.path.normpath(app.root_path), app.config.get("UPLOAD_FOLDER")
        )
        writeup_folder = os.path.join(upload_folder, "writeups")
        os.makedirs(writeup_folder, exist_ok=True)

        wp = tempfile.NamedTemporaryFile()
        wp_zip = zipfile.ZipFile(wp, "w")
        for root, _dirs, files in os.walk(writeup_folder):
            for file in files:
                parent_dir = os.path.basename(root)
                wp_zip.write(
                    os.path.join(root, file),
                    arcname=os.path.join(parent_dir, file),
                )

        wp_zip.close()
        wp.seek(0)

        ctf_name = ctf_config.ctf_name()
        day = datetime.now().strftime("%Y-%m-%d_%T")
        full_name = u"{}.writeup.{}.zip".format(ctf_name, day)

        return send_file(
            wp, cache_timeout=-1, as_attachment=True, attachment_filename=full_name
        )

    @page_blueprint.route("/admin/delete")
    @admins_only
    def admin_delete_writeup():
        upload_folder = os.path.join(
            os.path.normpath(app.root_path), app.config.get("UPLOAD_FOLDER")
        )
        writeup_folder = os.path.join(upload_folder, "writeups")
        os.makedirs(writeup_folder, exist_ok=True)

        writeup_name = request.args.get("name")
        # 构造备份文件的完整路径
        writeup_path = os.path.join(writeup_folder, writeup_name)

        # 检查文件是否存在
        if os.path.exists(writeup_path):
            os.remove(writeup_path)
            return {
                'success': True,
                'message': '删除成功！'
            }, 200
        else:
            return {
                'success': False,
                'message': '文件不存在！'
            }, 200

    def is_pdf(file):
        try:
            original_position = file.tell()
            # 使用BytesIO将文件内容读取到内存中
            file_content = BytesIO(file.read())
            file.seek(original_position)
            pdf_reader = PdfReader(file_content)
            # 判断PDF文件是否能成功读取
            len(pdf_reader.pages)
            return True
        except Exception as e:
            return False

    @page_blueprint.route("/upload", methods=['GET', 'POST'])
    @authed_only
    def UserUpload():
        if request.method == "POST":
            # 没开始之前不许上传wp
            if ctf_started() is False:
                if current_user.is_admin() is False:
                    return redirect(url_for("challenges.listing"))

            if get_config("writeup:enabled"):
                filename_for_store = ""
                user = current_user.get_current_user()
                try:
                    filename_for_store = get_config("writeup:name").format(user=user)
                except Exception as e:
                    log_simple("writeup", "[{date}] [Writeup] 用户上传writeup时格式化名称出错，请检查后台文件名配置！：{e}",
                               e=str(e))
                    return {
                        'success': False,
                        'message': '后端处理失败，请联系管理员！'
                    }, 500
                upload_folder = os.path.join(
                    os.path.normpath(app.root_path), app.config.get("UPLOAD_FOLDER")
                )
                writeup_folder = os.path.join(upload_folder, "writeups")
                os.makedirs(writeup_folder, exist_ok=True)

                # 检查文件是否存在于请求中
                if 'writeup' not in request.files:
                    return {
                        'success': False,
                        'message': '题解文件不存在'
                    }, 400
                file = request.files['writeup']
                # 如果用户未选择文件，浏览器也可能提交一个空的 part
                if file.filename == '':
                    return {
                        'success': False,
                        'message': '题解文件为空'
                    }, 400

                if file:
                    try:
                        if not is_pdf(file):
                            log_simple("writeup", "[{date}] [Writeup] pdf校验失败，可能用户{name}上传的是恶意文件！",
                                       name=user.name)
                            return {'success': False, 'message': "文件未通过校验！"}, 400
                    except:
                        log_simple("writeup", "[{date}] [Writeup] pdf校验失败，可能用户{name}上传的是恶意文件！",
                                   name=user.name)
                        return {'success': False, 'message': "文件未通过校验！"}, 400
                    try:
                        filepath = os.path.join(writeup_folder, filename_for_store)
                        file.save(filepath)
                        log_simple("writeup", "[{date}] [Writeup] 用户{name}成功上传了writeup:[{filename}]。",
                                   name=user.name,
                                   filename=file.filename)
                    except Exception as e:
                        log_simple("writeup", "[{date}] [Writeup] 用户{name}上传writeup:[{filename}]时出错{e}",
                                   name=user.name,
                                   filename=file.filename,
                                   e=str(e))
                        return {'success': False, 'message': "上传失败"}, 500

                return {'success': True, 'message': "上传成功"}, 200
            else:
                return redirect(url_for("challenges.listing"))
        else:
            # 没开始之前不许上传wp
            if ctf_started() is False:
                if current_user.is_admin() is False:
                    return redirect(url_for("challenges.listing"))

            if get_config("writeup:enabled"):
                return render_template("writeup_upload.html")
            else:
                return redirect(url_for("challenges.listing"))

    app.register_blueprint(page_blueprint)

    def insert_tags(page):
        # 没有开启直接返回
        if not get_config('writeup:enabled'):
            return page

        # 没开始之前不显示上传wp
        if ctf_started() is False:
            if current_user.is_admin() is False:
                return page

        if isinstance(page, etree._ElementTree):
            root = page
        else:
            try:
                root = etree.fromstring(page, etree.HTMLParser())
            except:
                # 我们无法解析它（例如，它是一个 Response 对象），所以只需将它传递过去
                return page

        try:
            language = "en"
            try:
                language = request.cookies.get("Scr1wCTFdLanguage", "en")
            except:
                pass

            inserted = False
            for window in root.xpath('/html/body/main/div[@id="challenge-window"]'):
                if language == "zh":
                    link = etree.Element(
                        'button',
                        attrib={
                            'class': 'btn btn-md btn-primary btn-outlined float-right',
                            'style': 'position: sticky; top: 80px; margin-top:40px; float: right;margin-right:30px; '
                                     'z-index: 999;',
                            'onclick': 'window.open("/plugins/writeup/upload")',
                        }
                    )
                    link.text = "上传题解"
                    window.addnext(link)
                else:
                    link = etree.Element(
                        'button',
                        attrib={
                            'class': 'btn btn-md btn-primary btn-outlined float-right',
                            'style': 'position: sticky; top: 90px; margin-top:40px; float: right;margin-right:30px; '
                                     'z-index: 999;',
                            'onclick': 'window.open("/plugins/writeup/upload")',
                        }
                    )
                    div1 = etree.SubElement(link, 'div')
                    div1.text = 'Upload'
                    div2 = etree.SubElement(link, 'div')
                    div2.text = 'Writeup'
                    window.addnext(link)
                inserted = True

            if not inserted:
                log_simple("writeup", "[{date}] [Writeup] 页面插入元素失败，未找到对应元素。")

            # fix some weird padding
            if language == "zh":
                return etree.tostring(root, encoding="unicode", method='html').replace("<span class=\"d-lg-none"
                                                                                       "\">注销</span>", "注销")
            else:
                return etree.tostring(root, encoding="unicode", method='html').replace("<span class=\"d-lg-none"
                                                                                       "\">Logout</span>", "Logout")
        except Exception as e:
            log_simple("writeup", "[{date}] [Writeup] 页面插入元素失败:{e}", e=e)
            return page

    def insert_tags_decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            return insert_tags(view_func(*args, **kwargs))

        return wrapper

    app.view_functions['challenges.listing'] = insert_tags_decorator(app.view_functions['challenges.listing'])
