import logging
import os
import sys
import json
from email.utils import formataddr
from functools import wraps

import requests
from flask import render_template, Blueprint

from CTFd.plugins import (
    register_plugin_assets_directory,
    register_admin_plugin_menu_bar,
)
from CTFd.utils import get_app_config
from CTFd.utils import get_config, set_config
from CTFd.utils.email import SMTPEmailProvider
from ...utils.decorators import admins_only
from ...utils.logging import log_simple

logger = logging.getLogger("SMTPViaHTTP")


def config(app):
    if not get_config("SMTPViaHTTP:setup"):
        for key, val in {
            'enabled': 'false',
            'ServerName': 'https://example.com/sendEmail',
            'setup': 'true'
        }.items():
            set_config('SMTPViaHTTP:' + key, val)


def load(app):
    config(app)
    plugin_name = __name__.split('.')[-1]

    # 初始化日志
    logger_SMTPViaHTTP = logging.getLogger("SMTPViaHTTP")
    logger_SMTPViaHTTP.setLevel(logging.INFO)

    log_dir = app.config["LOG_FOLDER"]
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logs = {
        "SMTPViaHTTP": os.path.join(log_dir, "SMTPViaHTTP.log"),
    }
    try:
        for log in logs.values():
            if not os.path.exists(log):
                open(log, "a").close()
        SMTPViaHTTP_log = logging.handlers.RotatingFileHandler(
            logs["SMTPViaHTTP"], maxBytes=10485760, backupCount=2
        )
        logger_SMTPViaHTTP.addHandler(SMTPViaHTTP_log)
    except IOError:
        pass
    stdout = logging.StreamHandler(stream=sys.stdout)
    logger_SMTPViaHTTP.addHandler(stdout)
    logger_SMTPViaHTTP.propagate = 0

    register_plugin_assets_directory(
        app,
        base_path=f"/plugins/{plugin_name}/assets",
        endpoint='plugins.SMTPViaHTTP.assets')
    register_admin_plugin_menu_bar(title='SMTPViaHTTP',
                                   route='/plugins/SMTPViaHTTP/admin/settings')

    page_blueprint = Blueprint("SMTPViaHTTP",
                               __name__,
                               template_folder="templates",
                               static_folder="static",
                               url_prefix="/plugins/SMTPViaHTTP")

    @page_blueprint.route('/admin/settings')
    @admins_only
    def admin_list_configs():
        return render_template('SMTPViaHTTP_config.html')

    app.register_blueprint(page_blueprint)

    def smtp_via_http(addr, text, subject):
        mailfrom_addr = formataddr(
            (get_config("ctf_name"), (get_config("mailfrom_addr") or get_app_config("MAILFROM_ADDR"))))
        host = get_config("mail_server") or get_app_config("MAIL_SERVER")
        port = int(get_config("mail_port") or get_app_config("MAIL_PORT"))
        username = get_config("mail_username") or get_app_config("MAIL_USERNAME")
        password = get_config("mail_password") or get_app_config("MAIL_PASSWORD")
        SSL = get_config("mail_ssl") or get_app_config("MAIL_SSL") or get_config("mail_tls") or get_app_config(
            "MAIL_TLS")
        if SSL:
            SSL = True
        else:
            SSL = False
        # auth = get_config("mail_useauth") or get_app_config("MAIL_USEAUTH")

        payload = {
            "from": mailfrom_addr,
            "to": addr,
            "subject": subject,
            "body": text,
            "smtp_server": host,
            "smtp_port": port,
            "username": username,
            "password": password,
            "use_ssl": SSL
        }
        payload_json = json.dumps(payload)
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        try:
            response = requests.post(get_config("SMTPViaHTTP:ServerName"), data=payload_json,
                                     headers=headers)
            if response.status_code == 200:
                response_json = response.json()
                if response_json['success']:
                    log_simple("email", "[{date}] [CTFd] 发往{addr}的邮件已通过SMTPViaHTTP成功发送。", addr=addr)
                    return True, f"发往{addr}的邮件已通过SMTPViaHTTP成功发送。"
                else:
                    log_simple("email", "[{date}] [CTFd] 发往{addr}的邮件通过SMTPViaHTTP发送失败！\n{exception}", addr=addr,
                               exception=response_json['exception'])
                    return False, f"发往{addr}的邮件通过SMTPViaHTTP发送失败。"
            else:
                code = response.status_code
                log_simple("email", "[{date}] [CTFd] 发往{addr}的邮件通过SMTPViaHTTP发送失败！状态码{code}", addr=addr,
                           code=code)
                return False, f"发往{addr}的邮件通过SMTPViaHTTP发送失败。状态码{code}"
        except Exception as e:
            err = str(e)
            log_simple("email", "[{date}] [CTFd] 发往{addr}的邮件通过SMTPViaHTTP发送失败！错误{err}", addr=addr,
                       err=err)
            return False, f"发往{addr}的邮件通过SMTPViaHTTP发送失败。错误{err}"


    def set_smtp_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if get_config("SMTPViaHTTP:enabled"):
                return smtp_via_http(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    SMTPEmailProvider.sendmail = set_smtp_decorator(SMTPEmailProvider.sendmail)
