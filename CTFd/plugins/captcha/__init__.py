import sys
import logging
import os

from flask_restx import Namespace

from CTFd.plugins import (
    register_plugin_assets_directory,
    register_admin_plugin_menu_bar,
)
from CTFd.utils import get_config, set_config

from .providers import VerificationError, CaptchaProvider
from flask import request, render_template, Blueprint
from functools import wraps
from lxml import etree

from ...api import CTFd_API_v1
from ...utils.decorators import admins_only

logger = logging.getLogger('captcha')


def config(app):
    if not get_config("captcha:setup"):
        for key, val in {
            'ENABLED': 'false',
            'VERIFY_REMOTE_IP': 'false',
            'PROVIDER': 'reCaptcha',
            'SECRET': '',
            'SITE_KEY': '',
            'setup': 'true'
        }.items():
            set_config('captcha:' + key, val)


def load(app):
    config(app)
    plugin_name = __name__.split('.')[-1]

    register_plugin_assets_directory(
        app,
        base_path=f"/plugins/{plugin_name}/assets",
        endpoint='plugins.captcha.assets')
    register_admin_plugin_menu_bar(title='Captcha',
                                   route='/plugins/captcha/admin/settings')

    page_blueprint = Blueprint("captcha",
                               __name__,
                               template_folder="templates",
                               static_folder="static",
                               url_prefix="/plugins/captcha")
    CTFd_API_v1.add_namespace(Namespace("captcha-admin"),
                              path="/plugins/captcha/admin")

    @page_blueprint.route('/admin/settings')
    @admins_only
    def admin_list_configs():
        return render_template('captcha_config.html')

    app.register_blueprint(page_blueprint)

    # 初始化日志
    log_dir = app.config.get('LOG_FOLDER', os.path.join(os.path.dirname(__file__), 'logs'))
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, 'captcha.log')

    if not os.path.exists(log_file):
        open(log_file, 'a').close()
    logger.addHandler(logging.handlers.RotatingFileHandler(log_file, maxBytes=10000))
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))
    logger.propagate = 0

    def insert_tags(page):
        # 没有开启直接返回
        if not get_config('captcha:ENABLED'):
            return page

        # 定义服务提供商
        provider = CaptchaProvider.parse(get_config('captcha:PROVIDER'))(get_config('captcha:SITE_KEY'),
                                                                         get_config('captcha:SECRET'),
                                                                         get_config('captcha:VERIFY_REMOTE_IP'))

        if isinstance(page, etree._ElementTree):
            root = page
        else:
            try:
                root = etree.fromstring(page, etree.HTMLParser())
            except:
                # 我们无法解析它（例如，它是一个 Response 对象），所以只需将它传递过去
                return page

        # 在提交按钮左侧插入复选框
        # 遍历所有表单和按钮，但实际上只有一个
        # 除非开发人员正在做一个不平凡的自定义主题
        # 在这种情况下他们将关闭自动插入功能
        inserted_div, inserted_script = False, False
        for form in root.iter('form'):
            for button in form.xpath('.//button[@type="submit"] | .//input[@type="submit"]'):
                button.addprevious(provider.challenge_tag())
                logger.debug("将验证码复选框元素插入页面")
                inserted_div = True

        for head in root.iter('head'):
            head.append(provider.script_tag())
            logger.debug("将验证码脚本标签插入页面头部")
            inserted_script = True

        if not inserted_div and inserted_script:
            logger.error('无法将 capctha 元素插入页面：inserted_div={!s}、inserted_script={!s}'.format(inserted_div,
                                                                                                     inserted_script))

        return etree.tostring(root, method='html')

    def insert_tags_decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            return insert_tags(view_func(*args, **kwargs))

        return wrapper

    def register_decorator(register_func):
        @wraps(register_func)
        def wrapper(*args, **kwargs):
            provider = CaptchaProvider.parse(get_config('captcha:PROVIDER'))(get_config('captcha:SITE_KEY'),
                                                                             get_config('captcha:SECRET'),
                                                                             get_config('captcha:VERIFY_REMOTE_IP'))
            if request.method == 'POST':
                if get_config('captcha:ENABLED'):
                    errors = []
                    verified = None
                    try:
                        verified = provider.verify(request.form, request.remote_addr)
                    except VerificationError as e:
                        errors.append("验证码服务目前不可用。 请稍后再试")

                    if verified is False:
                        errors.append("请检查验证码框以验证您是人类")

                    if not verified:
                        return render_template(
                            'register.html',
                            errors=errors,
                            name=request.form['name'],
                            email=request.form['email'],
                        )
            return register_func(*args, **kwargs)

        return wrapper

    app.view_functions['auth.register'] = register_decorator(app.view_functions['auth.register'])
    app.view_functions['auth.register'] = insert_tags_decorator(app.view_functions['auth.register'])
