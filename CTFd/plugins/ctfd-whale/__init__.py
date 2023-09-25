import fcntl
import logging
import os
import sys
import traceback
import warnings

import requests
from flask import Blueprint, render_template, session, current_app, request
from flask_apscheduler import APScheduler

from CTFd.api import CTFd_API_v1
from CTFd.plugins import (
    register_plugin_assets_directory,
    register_admin_plugin_menu_bar,
)
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.utils import get_config, set_config, import_in_progress, current_backend_time
from CTFd.utils.decorators import admins_only
from CTFd.utils.logging import log, log_simple

from .api import user_namespace, admin_namespace, AdminContainers
from .challenge_type import DynamicValueDockerChallenge
from .utils.checks import WhaleChecks
from .utils.control import ControlUtil
from .utils.db import DBContainer
from .utils.docker import DockerUtils
from .utils.exceptions import WhaleWarning
from .utils.setup import setup_default_configs
from .utils.routers import Router


def load(app):
    # upgrade()
    plugin_name = __name__.split('.')[-1]
    set_config('whale:plugin_name', plugin_name)
    app.db.create_all()
    if not get_config("whale:setup"):
        setup_default_configs()

    register_plugin_assets_directory(
        app,
        base_path=f"/plugins/{plugin_name}/assets",
        endpoint='plugins.ctfd-whale.assets')
    register_admin_plugin_menu_bar(title='Whale',
                                   route='/plugins/ctfd-whale/admin/settings')

    DynamicValueDockerChallenge.templates = {
        "create": f"/plugins/{plugin_name}/assets/create.html",
        "update": f"/plugins/{plugin_name}/assets/update.html",
        "view": f"/plugins/{plugin_name}/assets/view.html",
    }
    DynamicValueDockerChallenge.scripts = {
        "create": "/plugins/ctfd-whale/assets/create.js",
        "update": "/plugins/ctfd-whale/assets/update.js",
        "view": "/plugins/ctfd-whale/assets/view.js",
    }
    CHALLENGE_CLASSES["dynamic_docker"] = DynamicValueDockerChallenge

    page_blueprint = Blueprint("ctfd-whale",
                               __name__,
                               template_folder="templates",
                               static_folder="assets",
                               url_prefix="/plugins/ctfd-whale")
    CTFd_API_v1.add_namespace(admin_namespace,
                              path="/plugins/ctfd-whale/admin")
    CTFd_API_v1.add_namespace(user_namespace, path="/plugins/ctfd-whale")

    worker_config_commit = None

    init_logs(app)

    @page_blueprint.route('/admin/settings')
    @admins_only
    def admin_list_configs():
        nonlocal worker_config_commit
        errors = WhaleChecks.perform()
        if not errors and get_config("whale:refresh") != worker_config_commit:
            worker_config_commit = get_config("whale:refresh")
            DockerUtils.init()
            Router.reset()
            set_config("whale:refresh", "false")
        return render_template('whale_config.html', errors=errors)

    @page_blueprint.route("/admin/containers")
    @admins_only
    def admin_list_containers():
        result = AdminContainers.get()
        view_mode = request.args.get('mode', session.get('view_mode', 'list'))
        session['view_mode'] = view_mode
        return render_template("whale_containers.html",
                               plugin_name=plugin_name,
                               containers=result['data']['containers'],
                               pages=result['data']['pages'],
                               curr_page=abs(
                                   request.args.get("page", 1, type=int)),
                               curr_page_start=result['data']['page_start'])

    @page_blueprint.route("/admin/upload", methods=['GET', 'POST'])
    @admins_only
    def admin_upload_image():
        global filepath
        if request.method == 'POST':
            name = request.args.get("name")
            if not name:
                return {
                           'success': False,
                           'message': '缺少参数'
                       }, 400
            tag = request.args.get("tag")
            if not tag:
                return {
                           'success': False,
                           'message': '缺少参数'
                       }, 400
            # 检查文件是否存在于请求中
            if 'image' not in request.files:
                return {
                           'success': False,
                           'message': '镜像文件不存在'
                       }, 500
            file = request.files['image']
            # 如果用户未选择文件，浏览器也可能提交一个空的 part
            if file.filename == '':
                return {
                           'success': False,
                           'message': '镜像文件为空'
                       }, 500
            if file:
                try:
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                    file.save(filepath)
                    log(
                        "whale",
                        "[{date}] [CTFd Whale] {ip}上传的镜像文件({name}:{tag})保存至:{filepath}",
                        name=name,
                        tag=tag,
                        filepath=filepath,
                    )
                    try:
                        image_info = DockerUtils.client.images.get(name + ":" + tag)
                        DockerUtils.client.api.remove_image(name + ":" + tag)
                    except Exception as e:
                        pass
                    DockerUtils.client.api.import_image_from_file(filepath, repository=name, tag=tag)
                    log(
                        "whale",
                        "[{date}] [CTFd Whale] {name}:{tag}导入完成。",
                        name=name,
                        tag=tag,
                    )
                    # 删除上传的文件
                    os.remove(filepath)
                    return {
                               'success': True,
                               'message': '镜像上传完成'
                           }, 200
                except Exception as e:
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
                    traceback_str = ''.join(traceback.format_tb(e.__traceback__))
                    log(
                        "whale",
                        "[{date}] [CTFd Whale] {name}镜像加载失败。{error}\n{tb}",
                        name=(name + ":" + tag),
                        error=e,
                        tb=traceback_str,
                    )
                    return {
                               'success': False,
                               'message': '镜像加载失败<br>' + str(e)
                           }, 500

        return render_template("whale_upload.html")

    @page_blueprint.route("/admin/image-update")
    @admins_only
    def admin_image_update():
        try:
            # 获取GET请求中的name参数
            name = request.args.get('name')
            log(
                "whale",
                "[{date}] [CTFd Whale] 尝试更新镜像{name}。",
                name=name,
            )
            DockerUtils.client.api.pull(name)
            # 返回HTTP状态码200
            log(
                "whale",
                "[{date}] [CTFd Whale] {name}镜像更新成功。",
                name=name,
            )
            return {
                       'success': True,
                       'message': '镜像更新完成'
                   }, 200
        except Exception as e:
            name = request.args.get('name')
            traceback_str = ''.join(traceback.format_tb(e.__traceback__))
            log(
                "whale",
                "[{date}] [CTFd Whale] {name}镜像更新失败。{error}\n{tb}",
                name=name,
                error=e,
                tb=traceback_str
            )
            return {
                       'success': False,
                       'message': '镜像更新出错：<br>' + str(e.__cause__)
                   }, 200

    class ContainerObject:
        def __init__(self, user_id, uuid):
            self.user_id = user_id
            self.uuid = uuid

    def auto_clean_container():
        with app.app_context():
            if not import_in_progress():
                results = DBContainer.get_all_expired_container()
                for r in results:
                    ControlUtil.try_remove_container(r.user_id)

                existing_whale_services = []
                for service in DockerUtils.client.services.list():
                    service_labels = service.attrs['Spec']['Labels']
                    if 'whale_id' in service_labels:
                        existing_whale_services.append(service)

                for service in existing_whale_services:
                    whale_id = service.attrs['Spec']['Labels']['whale_id']
                    user_id = whale_id.split("-")[0]
                    uuid = ""
                    user_id_prefix = "{}-".format(user_id)
                    if whale_id.startswith(user_id_prefix):
                        uuid = whale_id[len(user_id_prefix):]
                    container = ContainerObject(user_id=user_id, uuid=uuid)
                    if DBContainer.get_current_containers(user_id) is None:
                        log_simple("whale", "[CTFd Whale] 检测到幽灵镜像：" + whale_id)
                        try:
                            DockerUtils.remove_container(container)
                            Router.reload()
                        except:
                            pass

    app.register_blueprint(page_blueprint)

    try:
        Router.check_availability()
        DockerUtils.init()
    except Exception as e:
        traceback_str = ''.join(traceback.format_tb(e.__traceback__))
        logger = logging.getLogger("whale")
        current_date = current_backend_time().strftime("%Y/%m/%d %X")
        logger.info(
            "[{}] [CTFd Whale] 初始化失败，请检查配置。\n{} \n{}\n{}".format(current_date, e, WhaleWarning, traceback_str)
        )

    try:
        lock_file = open("/tmp/ctfd_whale.lock", "w")
        lock_fd = lock_file.fileno()
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()
        scheduler.add_job(id='whale-auto-clean',
                          func=auto_clean_container,
                          trigger="interval",
                          seconds=10)

        logger = logging.getLogger("whale")
        current_date = current_backend_time().strftime("%Y/%m/%d %X")
        logger.info("[{}] [CTFd Whale] 启动初始化完成。".format(current_date))
    except IOError:
        pass


def init_logs(app):
    logger_whale = logging.getLogger("whale")
    logger_whale.setLevel(logging.INFO)

    log_dir = app.config["LOG_FOLDER"]
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logs = {
        "whale": os.path.join(log_dir, "whale.log"),
    }
    try:
        for log in logs.values():
            if not os.path.exists(log):
                open(log, "a").close()
        whale_log = logging.handlers.RotatingFileHandler(
            logs["whale"], maxBytes=10485760, backupCount=5
        )
        logger_whale.addHandler(whale_log)
    except IOError:
        pass
    stdout = logging.StreamHandler(stream=sys.stdout)
    logger_whale.addHandler(stdout)
    logger_whale.propagate = 0
