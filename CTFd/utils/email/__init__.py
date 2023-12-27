from flask import url_for

from CTFd.utils import get_config
from CTFd.utils.config import get_mail_provider
from CTFd.utils.email.providers.mailgun import MailgunEmailProvider
from CTFd.utils.email.providers.smtp import SMTPEmailProvider
from CTFd.utils.formatters import safe_format
from CTFd.utils.security.signing import serialize

PROVIDERS = {"smtp": SMTPEmailProvider, "mailgun": MailgunEmailProvider}

DEFAULT_VERIFICATION_EMAIL_SUBJECT = "确认您的 {ctf_name} 帐户"
DEFAULT_VERIFICATION_EMAIL_BODY = (
    "欢迎来到 {ctf_name}！\n\n"
    "点击以下链接确认并激活您的帐户：\n"
    "{url}"
    "\n\n"
    "如果该链接不可点击，请尝试将其复制并粘贴到您的浏览器中。"
)
DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_SUBJECT = "已成功注册 {ctf_name}"
DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_BODY = (
    "您已成功注册 {ctf_name}！"
)
DEFAULT_USER_CREATION_EMAIL_SUBJECT = "来自 {ctf_name} 的消息"
DEFAULT_USER_CREATION_EMAIL_BODY = (
    "已为您在 {url} 上为 {ctf_name} 创建了一个新帐户。 \n\n"
    "用户名：{name}\n"
    "密码：{password}"
)
DEFAULT_PASSWORD_RESET_SUBJECT = "来自 {ctf_name} 的密码重置请求"
DEFAULT_PASSWORD_RESET_BODY = (
    "您是否在 {ctf_name} 上进行了密码重置？"
    "如果您没有发起此请求，您可以忽略此电子邮件。 \n\n"
    "单击以下链接重置您的密码：\n{url}\n\n"
    "如果该链接不可点击，请尝试将其复制并粘贴到您的浏览器中。"
)
DEFAULT_PASSWORD_CHANGE_ALERT_SUBJECT = "{ctf_name} 的密码更改确认"
DEFAULT_PASSWORD_CHANGE_ALERT_BODY = (
    "您的 {ctf_name} 密码已更改。\n\n"
    "如果您没有请求更改密码，您可以在此处重置密码：\n{url}\n\n"
    "如果该链接不可点击，请尝试将其复制并粘贴到您的浏览器中。"
)


def sendmail(addr, text, subject="来自 {ctf_name} 的消息"):
    subject = safe_format(subject, ctf_name=get_config("ctf_name"))
    provider = get_mail_provider()
    EmailProvider = PROVIDERS.get(provider)
    if EmailProvider is None:
        return False, "未配置邮件设置"
    return EmailProvider.sendmail(addr, text, subject)


def password_change_alert(email):
    text = safe_format(
        get_config("password_change_alert_body") or DEFAULT_PASSWORD_CHANGE_ALERT_BODY,
        ctf_name=get_config("ctf_name"),
        ctf_description=get_config("ctf_description"),
        url=url_for("auth.reset_password", _external=True),
    )

    subject = safe_format(
        get_config("password_change_alert_subject")
        or DEFAULT_PASSWORD_CHANGE_ALERT_SUBJECT,
        ctf_name=get_config("ctf_name"),
    )
    return sendmail(addr=email, text=text, subject=subject)


def forgot_password(email):
    text = safe_format(
        get_config("password_reset_body") or DEFAULT_PASSWORD_RESET_BODY,
        ctf_name=get_config("ctf_name"),
        ctf_description=get_config("ctf_description"),
        url=url_for("auth.reset_password", data=serialize(email), _external=True),
    )

    subject = safe_format(
        get_config("password_reset_subject") or DEFAULT_PASSWORD_RESET_SUBJECT,
        ctf_name=get_config("ctf_name"),
    )
    return sendmail(addr=email, text=text, subject=subject)


def verify_email_address(addr):
    text = safe_format(
        get_config("verification_email_body") or DEFAULT_VERIFICATION_EMAIL_BODY,
        ctf_name=get_config("ctf_name"),
        ctf_description=get_config("ctf_description"),
        url=url_for(
            "auth.confirm", data=serialize(addr), _external=True, _method="GET"
        ),
    )

    subject = safe_format(
        get_config("verification_email_subject") or DEFAULT_VERIFICATION_EMAIL_SUBJECT,
        ctf_name=get_config("ctf_name"),
    )
    return sendmail(addr=addr, text=text, subject=subject)


def successful_registration_notification(addr):
    text = safe_format(
        get_config("successful_registration_email_body")
        or DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_BODY,
        ctf_name=get_config("ctf_name"),
        ctf_description=get_config("ctf_description"),
        url=url_for("views.static_html", _external=True),
    )

    subject = safe_format(
        get_config("successful_registration_email_subject")
        or DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_SUBJECT,
        ctf_name=get_config("ctf_name"),
    )
    return sendmail(addr=addr, text=text, subject=subject)


def user_created_notification(addr, name, password):
    text = safe_format(
        get_config("user_creation_email_body") or DEFAULT_USER_CREATION_EMAIL_BODY,
        ctf_name=get_config("ctf_name"),
        ctf_description=get_config("ctf_description"),
        url=url_for("views.static_html", _external=True),
        name=name,
        password=password,
    )

    subject = safe_format(
        get_config("user_creation_email_subject")
        or DEFAULT_USER_CREATION_EMAIL_SUBJECT,
        ctf_name=get_config("ctf_name"),
    )
    return sendmail(addr=addr, text=text, subject=subject)


def check_email_is_whitelisted(email_address):
    local_id, _, domain = email_address.partition("@")
    domain_whitelist = get_config("domain_whitelist")
    if domain_whitelist:
        domain_whitelist = [d.strip() for d in domain_whitelist.split(",")]
        for allowed_domain in domain_whitelist:
            if allowed_domain.startswith("*."):
                # 域名永远不应该包含“*”字符
                if "*" in domain:
                    return False

                # 处理通配符域名情况
                suffix = allowed_domain[1:]  # Remove the "*" prefix
                if domain.endswith(suffix):
                    return True

            elif domain == allowed_domain:
                return True

        # 指定了白名单，但电子邮件与任何域名都不匹配
        return False
    return True
