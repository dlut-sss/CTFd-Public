from __future__ import division  # Use floating point for math calculations

import shutil
import subprocess
from datetime import datetime
import fcntl
import logging
import os
import sys
import tempfile
import traceback
import zipfile

from flask import render_template, request, jsonify, Blueprint, send_file
from flask_apscheduler import APScheduler

from CTFd.plugins import register_plugin_assets_directory, register_admin_plugin_menu_bar
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.utils import set_config, get_config, current_backend_time, import_in_progress
from CTFd.utils.decorators import admins_only, authed_only
from .challenge_type import DynamicCheckValueChallenge
from .models import DynamicCheckChallenge
from .utils.control import ControlUtil
from .utils.db import DBUtils
from .utils.extensions import get_mode
from .utils.frp import FrpUtils
from .utils.setup import setup_default_configs
from .utils.extensions import log as custom_log


def load(app):
    # upgrade()
    plugin_name = __name__.split('.')[-1]
    set_config('owl:plugin_name', plugin_name)
    app.db.create_all()
    if not get_config("owl:setup"):
        setup_default_configs()
    register_plugin_assets_directory(
        app, base_path=f"/plugins/{plugin_name}/assets",
        endpoint=f'plugins.{plugin_name}.assets'
    )
    register_admin_plugin_menu_bar(title='Owl',
                                   route=f'/plugins/ctfd-owl/admin/settings')

    DynamicCheckValueChallenge.templates = {
        "create": f"/plugins/{plugin_name}/assets/create.html",
        "update": f"/plugins/{plugin_name}/assets/update.html",
        "view": f"/plugins/{plugin_name}/assets/view.html",
    }
    DynamicCheckValueChallenge.scripts = {
        "create": f"/plugins/{plugin_name}/assets/create.js",
        "update": f"/plugins/{plugin_name}/assets/update.js",
        "view": f"/plugins/{plugin_name}/assets/view.js",
    }
    CHALLENGE_CLASSES["dynamic_docker_compose"] = DynamicCheckValueChallenge

    owl_blueprint = Blueprint(
        "ctfd-owl",
        __name__,
        template_folder="templates",
        static_folder="assets",
        url_prefix="/plugins/ctfd-owl"
    )

    log_dir = app.config["LOG_FOLDER"]
    logger_owl = logging.getLogger("owl")
    logger_owl.setLevel(logging.INFO)
    logs = {
        "owl": os.path.join(log_dir, "owl.log"),
    }
    try:
        for log in logs.values():
            if not os.path.exists(log):
                open(log, "a").close()
        container_log = logging.handlers.RotatingFileHandler(
            logs["owl"], maxBytes=10485760, backupCount=5
        )
        logger_owl.addHandler(container_log)
    except IOError:
        pass

    stdout = logging.StreamHandler(stream=sys.stdout)
    logger_owl.addHandler(stdout)
    logger_owl.propagate = 0

    @owl_blueprint.route('/admin/settings')
    @admins_only
    def admin_list_configs():
        return render_template('configs.html')

    @owl_blueprint.route("/admin/containers", methods=['GET'])
    @admins_only
    # list alive containers
    def admin_list_containers():
        mode = get_config("user_mode")
        page = abs(request.args.get("page", 1, type=int))
        results_per_page = 50
        page_start = results_per_page * (page - 1)
        page_end = results_per_page * (page - 1) + results_per_page

        count = DBUtils.get_all_alive_container_count()
        containers = DBUtils.get_all_alive_container_page(page_start, page_end)

        pages = int(count / results_per_page) + (count % results_per_page > 0)
        return render_template("containers.html", containers=containers, pages=pages, curr_page=page,
                               curr_page_start=page_start, mode=mode)

    @owl_blueprint.route("/admin/containers", methods=['PATCH'])
    @admins_only
    def admin_expired_container():
        user_id = request.args.get('user_id')
        result = ControlUtil.expired_container(user_id=user_id)
        return jsonify({'success': result})

    @owl_blueprint.route("/admin/containers", methods=['DELETE'])
    @admins_only
    def admin_delete_container():
        user_id = request.args.get('user_id')
        result = ControlUtil.destroy_container(user_id)
        return jsonify({'success': result})

    @owl_blueprint.route("/admin/upload", methods=['GET', 'POST'])
    @admins_only
    def admin_upload_file():
        global filepath
        if request.method == 'POST':
            name = request.args.get("name")
            if not name:
                return {
                    'success': False,
                    'message': '缺少参数'
                }, 400
            # 检查文件是否存在于请求中
            if 'file' not in request.files:
                return {
                    'success': False,
                    'message': '文件不存在'
                }, 500
            file = request.files['file']
            # 如果用户未选择文件，浏览器也可能提交一个空的 part
            if file.filename == '':
                return {
                    'success': False,
                    'message': '文件为空'
                }, 500
            if file:
                try:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filepath)
                    try:
                        extract_to_path = os.path.join(os.path.dirname(__file__), "source", name)
                        with zipfile.ZipFile(filepath, 'r') as zip_ref:
                            zip_ref.extractall(extract_to_path)
                    except Exception as e:
                        custom_log("owl",
                                   '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                                   e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)),
                                   flush=True
                                   )
                        return {
                            'success': False,
                            'message': '文件处理失败<br>' + str(e)
                        }, 500
                    # 删除上传的文件
                    os.remove(filepath)
                    custom_log("owl",
                               '[CTFd-owl] [{date}] 上传了源文件{name}',
                               name=name
                               )
                    return {
                        'success': True,
                        'message': '文件上传完成'
                    }, 200
                except Exception as e:
                    custom_log("owl",
                               '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                               e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                               )
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
                    return {
                        'success': False,
                        'message': '文件处理失败<br>' + str(e)
                    }, 500

        return render_template("upload.html")

    def format_size(size):
        # Convert bytes to human-readable format
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                break
            size /= 1024.0
        return "{:.2f} {}".format(size, unit)

    def get_dir_size(dir):
        size = 0
        for root, dirs, files in os.walk(dir):
            size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        return size

    @owl_blueprint.route("/admin/sources")
    @admins_only
    def admin_list_source():
        source_folder = os.path.join(os.path.dirname(__file__), "source")
        source_folders = []
        first_entries = os.listdir(source_folder)
        for entry in first_entries:
            first_path = os.path.join(source_folder, entry)
            if os.path.isdir(first_path):
                second_entries = os.listdir(first_path)
                for child_entry in second_entries:
                    second_path = os.path.join(first_path, child_entry)
                    if os.path.isdir(second_path):
                        file_size = get_dir_size(second_path)
                        file_date = os.path.getctime(second_path)
                        source_folders.append({
                            'name': (entry + "/" + child_entry),
                            'size': format_size(file_size),
                            'date': datetime.utcfromtimestamp(file_date)
                        })
        return render_template("sources.html", source_folders=source_folders)

    @owl_blueprint.route("/admin/delete")
    @admins_only
    def admin_delete_source():
        source_folder = os.path.join(os.path.dirname(__file__), "source")
        folder_name = request.args.get("name")
        source_path = os.path.join(source_folder, folder_name)

        if os.path.exists(source_path):
            shutil.rmtree(source_path)
            custom_log("owl",
                       '[CTFd-owl] [{date}] 删除了源文件{name}',
                       name=folder_name
                       )
            return {
                'success': True,
                'message': '删除成功！'
            }, 200
        else:
            return {
                'success': False,
                'message': '文件夹不存在！'
            }, 200

    @owl_blueprint.route("/admin/download")
    @admins_only
    def admin_download_sources():
        source_folder = os.path.join(os.path.dirname(__file__), "source")
        folder_name = request.args.get("name")
        source_path = os.path.join(source_folder, folder_name)

        # 检查文件是否存在
        if os.path.exists(source_path):
            source = tempfile.NamedTemporaryFile()
            with zipfile.ZipFile(source, 'w') as zipf:
                # 遍历文件夹中的所有文件和子文件夹，并将其添加到zip文件中
                for root, dirs, files in os.walk(source_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, source_path))
                zipf.close()
            source.seek(0)

            return send_file(
                source, cache_timeout=-1, as_attachment=True, attachment_filename="source.zip"
            )
        else:
            # 文件不存在，可以返回404或其他适当的响应
            return "File not found", 404

    @owl_blueprint.route("/admin/downloadAll")
    @admins_only
    def admin_download_all_sources():
        source_folder = os.path.join(os.path.dirname(__file__), "source")
        source = tempfile.NamedTemporaryFile()
        with zipfile.ZipFile(source, 'w') as zipf:
            # 遍历文件夹中的所有文件和子文件夹，并将其添加到zip文件中
            for root, dirs, files in os.walk(source_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, source_folder))
            zipf.close()
        source.seek(0)

        day = datetime.now().strftime("%Y-%m-%d_%T")
        full_name = u"owl.sources.{}.zip".format(day)

        return send_file(
            source, cache_timeout=-1, as_attachment=True, attachment_filename=full_name
        )

    # instances
    @owl_blueprint.route('/container', methods=['GET'])
    @authed_only
    def list_container():
        try:
            user_id = get_mode()
            challenge_id = request.args.get('challenge_id')
            ControlUtil.check_challenge(challenge_id, user_id)
            data = ControlUtil.get_container(user_id=user_id)
            domain = get_config('owl:frp_http_domain_suffix', "")
            timeout = int(get_config("owl:docker_timeout", "3600"))

            if data is not None:
                if int(data.challenge_id) != int(challenge_id):
                    return jsonify({})
                dynamic_docker_challenge = DynamicCheckChallenge.query \
                    .filter(DynamicCheckChallenge.id == data.challenge_id) \
                    .first_or_404()
                lan_domain = str(user_id) + "-" + data.docker_id

                if dynamic_docker_challenge.deployment == "single":
                    return jsonify(
                        {'success': True, 'type': 'redirect', 'ip': get_config('owl:frp_direct_ip_address', ""),
                         'port': data.port,
                         'remaining_time': timeout - (datetime.utcnow() - data.start_time).seconds,
                         'lan_domain': lan_domain})
                else:
                    if dynamic_docker_challenge.redirect_type == "http":
                        if int(get_config('owl:frp_http_port', "80")) == 80:
                            return jsonify({'success': True, 'type': 'http', 'domain': data.docker_id + "." + domain,
                                            'remaining_time': timeout - (
                                                    datetime.utcnow() - data.start_time).seconds,
                                            'lan_domain': lan_domain})
                        else:
                            return jsonify({'success': True, 'type': 'http',
                                            'domain': data.docker_id + "." + domain + ":" + get_config(
                                                'owl:frp_http_port', "80"),
                                            'remaining_time': timeout - (
                                                    datetime.utcnow() - data.start_time).seconds,
                                            'lan_domain': lan_domain})
                    else:
                        return jsonify(
                            {'success': True, 'type': 'redirect', 'ip': get_config('owl:frp_direct_ip_address', ""),
                             'port': data.port,
                             'remaining_time': timeout - (datetime.utcnow() - data.start_time).seconds,
                             'lan_domain': lan_domain})
            else:
                return jsonify({'success': True})
        except Exception as e:
            custom_log("owl",
                       '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                       e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                       )
            return jsonify({'success': False, 'msg': str(e)})

    @owl_blueprint.route('/container', methods=['POST'])
    @authed_only
    def new_container():
        try:
            user_id = get_mode()

            if ControlUtil.frequency_limit():
                return jsonify({'success': False, 'msg': '超出频率限制，请至少等待一分钟！'})
            existContainer = ControlUtil.get_container(user_id)
            if existContainer:
                return jsonify(
                    {'success': False, 'msg': '你已经开启了 {} 的实例.'.format(existContainer.challenge.name)})
            else:
                challenge_id = request.args.get('challenge_id')
                ControlUtil.check_challenge(challenge_id, user_id)
                current_count = DBUtils.get_all_alive_container_count()
                if get_config("owl:docker_max_container_count") != "None":
                    if int(get_config("owl:docker_max_container_count")) <= int(current_count):
                        return jsonify({'success': False, 'msg': '达到服务器最大实例上线！'})

                try:
                    result = ControlUtil.new_container(user_id=user_id, challenge_id=challenge_id)
                    if isinstance(result, bool):
                        return jsonify({'success': True})
                    else:
                        return jsonify({'success': False, 'msg': str(result)})
                except subprocess.CalledProcessError as e:
                    custom_log("owl",
                               '[CTFd-owl] [{date}] Error: {e}\n{stdout}\n{stderr}\n{trace}',
                               e=e, stdout=e.stdout, stderr=e.stderr,
                               trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                               )
                    return jsonify(
                        {'success': False,
                         'msg': '实例启动失败，请联系管理员解决！<br>{} {}'.format(str(e), str(e.stderr))})
                except Exception as e:
                    custom_log("owl",
                               '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                               e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                               )
                    return jsonify({'success': False, 'msg': '实例启动失败，请联系管理员解决！<br>{}'.format(str(e))})
        except Exception as e:
            custom_log("owl",
                       '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                       e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                       )
            return jsonify({'success': False, 'msg': str(e)})

    @owl_blueprint.route('/container', methods=['DELETE'])
    @authed_only
    def destroy_container():
        user_id = get_mode()

        if ControlUtil.frequency_limit():
            return jsonify({'success': False, 'msg': '超出频率限制，请至少等待一分钟！'})

        if ControlUtil.destroy_container(user_id):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'msg': '销毁实例失败，请联系管理员！'})

    @owl_blueprint.route('/container', methods=['PATCH'])
    @authed_only
    def renew_container():
        user_id = get_mode()
        if ControlUtil.frequency_limit():
            return jsonify({'success': False, 'msg': '超出频率限制，请至少等待一分钟！'})

        challenge_id = request.args.get('challenge_id')
        ControlUtil.check_challenge(challenge_id, user_id)
        docker_max_renew_count = int(get_config("owl:docker_max_renew_count"))
        container = ControlUtil.get_container(user_id)
        if container is None:
            return jsonify({'success': False, 'msg': '找不到请求的实例！'})
        if container.renew_count >= docker_max_renew_count:
            return jsonify({'success': False, 'msg': '超出最大延期次数！'})

        ControlUtil.expired_container(user_id=user_id)

        return jsonify({'success': True})

    def auto_clean_container():
        with app.app_context():
            if not import_in_progress():
                results = DBUtils.get_all_expired_container()
                for r in results:
                    ControlUtil.destroy_container(r.user_id)
                FrpUtils.update_frp_redirect()

    app.register_blueprint(owl_blueprint)

    try:
        lock_file = open("/tmp/ctfd_owl.lock", "w")
        lock_fd = lock_file.fileno()
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()
        scheduler.add_job(id='owl-auto-clean', func=auto_clean_container, trigger="interval", seconds=10)

        logger = logging.getLogger("owl")
        current_date = current_backend_time().strftime("%Y/%m/%d %X")
        logger.info("[CTFd-owl] 启动初始化完成。".format(current_date))
    except IOError:
        pass
