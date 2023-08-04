import fcntl
import os
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
from CTFd.utils import get_config, set_config, import_in_progress
from CTFd.utils.decorators import admins_only

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
                    print("[CTFd Whale] 上传的镜像文件 " + name + ":" + tag + " 保存至：" + filepath)
                    try:
                        image_info = DockerUtils.client.images.get(name + ":" + tag)
                        DockerUtils.client.api.remove_image(name + ":" + tag)
                    except Exception as e:
                        pass
                    DockerUtils.client.api.import_image_from_file(filepath, repository=name, tag=tag)
                    print("[CTFd Whale] " + name + ":" + tag + "导入完成")
                    # 删除上传的文件
                    os.remove(filepath)
                    return {
                               'success': True,
                               'message': '镜像上传完成'
                           }, 200
                except Exception as e:
                    print(e)
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
            DockerUtils.client.api.pull(name)
            # 返回HTTP状态码200
            print("[CTFd Whale] " + name + "镜像更新成功")
            return {
                       'success': True,
                       'message': '镜像更新完成'
                   }, 200
        except Exception as e:
            print("[CTFd Whale] " + name + "镜像更新失败")
            print(e)
            return {
                       'success': False,
                       'message': '镜像更新出错：\n' + str(e.__cause__)
                   }, 200

    def auto_clean_container():
        with app.app_context():
            if not import_in_progress():
                results = DBContainer.get_all_expired_container()
                for r in results:
                    ControlUtil.try_remove_container(r.user_id)

    app.register_blueprint(page_blueprint)

    try:
        Router.check_availability()
        DockerUtils.init()
    except Exception as e:
        warnings.warn("[CTFd Whale] 初始化失败，请检查配置。\n" + e,
                      WhaleWarning)

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

        print("[CTFd Whale] 启动成功！")
    except IOError:
        pass
