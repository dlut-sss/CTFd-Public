import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from socket import timeout

from CTFd.utils import get_app_config, get_config
from CTFd.utils.email.providers import EmailProvider
from CTFd.utils.logging import log_simple


class SMTPEmailProvider(EmailProvider):
    @staticmethod
    def sendmail(addr, text, subject):
        ctf_name = get_config("ctf_name")
        mailfrom_addr = get_config("mailfrom_addr") or get_app_config("MAILFROM_ADDR")
        mailfrom_addr = formataddr((ctf_name, mailfrom_addr))

        data = {
            "host": get_config("mail_server") or get_app_config("MAIL_SERVER"),
            "port": int(get_config("mail_port") or get_app_config("MAIL_PORT")),
        }
        username = get_config("mail_username") or get_app_config("MAIL_USERNAME")
        password = get_config("mail_password") or get_app_config("MAIL_PASSWORD")
        TLS = get_config("mail_tls") or get_app_config("MAIL_TLS")
        SSL = get_config("mail_ssl") or get_app_config("MAIL_SSL")
        auth = get_config("mail_useauth") or get_app_config("MAIL_USEAUTH")

        if username:
            data["username"] = username
        if password:
            data["password"] = password
        if TLS:
            data["TLS"] = TLS
        if SSL:
            data["SSL"] = SSL
        if auth:
            data["auth"] = auth

        try:
            smtp = get_smtp(**data)

            msg = EmailMessage()
            msg.set_content(text)

            msg["Subject"] = subject
            msg["From"] = mailfrom_addr
            msg["To"] = addr

            # 检查我们是否使用管理员定义的 SMTP 服务器
            custom_smtp = bool(get_config("mail_server"))

            # 我们应该只考虑配置中定义的服务器上的 MAILSENDER_ADDR 值
            if custom_smtp:
                smtp.send_message(msg)
            else:
                mailsender_addr = get_app_config("MAILSENDER_ADDR")
                smtp.send_message(msg, from_addr=mailsender_addr)

            smtp.quit()
            log_simple("email", "[{date}] [CTFd] 发往{addr}的邮件已成功发送。",addr=addr)
            return True, f"发往{addr}的邮件已成功发送。"
        except smtplib.SMTPException as e:
            log_simple("email", "[{date}] [CTFd] 邮件发送失败，出现了SMTPException异常{e}", e=str(e))
            return False, f"邮件发送失败，出现了SMTPException异常{str(e)}"
        except timeout:
            log_simple("email", "[{date}] [CTFd] 邮件发送失败，SMTP 服务器连接超时")
            return False, "SMTP 服务器连接超时"
        except Exception as e:
            if "WRONG_VERSION_NUMBER" in str(e):
                log_simple("email", "[{date}] [CTFd] 邮件发送失败，出现了异常{e}", e=str(e))
                log_simple("email",
                           "[{date}] [CTFd] WRONG_VERSION_NUMBER代表你可能开启了tls，但是服务器端口仍然为25，应设置为465")
                return False, f"邮件发送失败，出现了异常{str(e)}，代表你可能开启了tls，但是服务器端口仍然为25，应设置为465"
            else:
                log_simple("email", "[{date}] [CTFd] 邮件发送失败，出现了异常{e}", e=str(e))
                return False, f"邮件发送失败，出现了异常{str(e)}"


def get_smtp(host, port, username=None, password=None, TLS=None, SSL=None, auth=None):
    if SSL is None:
        smtp = smtplib.SMTP(host, port, timeout=3)
    else:
        smtp = smtplib.SMTP_SSL(host, port, timeout=3)

    if TLS:
        smtp.starttls()

    if auth:
        smtp.login(username, password)
    return smtp
