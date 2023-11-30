import base64  # noqa: I001
import json
from urllib.parse import quote

import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from flask import Blueprint, abort
from flask import current_app as app
from flask import redirect, render_template, request, session, url_for
from itsdangerous.exc import BadSignature, BadTimeSignature, SignatureExpired

from CTFd.cache import clear_team_session, clear_user_session
from CTFd.models import Teams, UserFieldEntries, UserFields, Users, db
from CTFd.utils import config, email, get_app_config, get_config
from CTFd.utils import user as current_user
from CTFd.utils import validators
from CTFd.utils.config import is_teams_mode
from CTFd.utils.config.integrations import mlc_registration
from CTFd.utils.config.visibility import registration_visible
from CTFd.utils.crypto import verify_password
from CTFd.utils.decorators import ratelimit
from CTFd.utils.decorators.visibility import check_registration_visibility
from CTFd.utils.helpers import error_for, get_errors, markup
from CTFd.utils.logging import log
from CTFd.utils.modes import TEAMS_MODE
from CTFd.utils.security.auth import login_user, logout_user
from CTFd.utils.security.signing import unserialize
from CTFd.utils.validators import ValidationError

auth = Blueprint("auth", __name__)


@auth.route("/confirm", methods=["POST", "GET"])
@auth.route("/confirm/<data>", methods=["POST", "GET"])
@ratelimit(method="POST", limit=10, interval=60)
def confirm(data=None):
    language = request.cookies.get("Scr1wCTFdLanguage", "zh")
    if not get_config("verify_emails"):
        # If the CTF doesn't care about confirming email addresses then redierct to challenges
        return redirect(url_for("challenges.listing"))

    # User is confirming email account
    if data and request.method == "GET":
        try:
            user_email = unserialize(data, max_age=1800)
        except (BadTimeSignature, SignatureExpired):
            if language == "zh":
                return render_template(
                    "confirm.html", errors=["您的确认链接已过期"]
                )
            else:
                return render_template(
                    "confirm.html", errors=["Your confirmation link has expired"]
                )
        except (BadSignature, TypeError, base64.binascii.Error):
            if language == "zh":
                return render_template(
                    "confirm.html", errors=["您的确认令牌无效"]
                )
            else:
                return render_template(
                    "confirm.html", errors=["Your confirmation token is invalid"]
                )

        user = Users.query.filter_by(email=user_email).first_or_404()
        if user.verified:
            return redirect(url_for("views.settings"))

        user.verified = True
        log(
            "registrations",
            format="[{date}] {name} 在 {ip} 成功验证了账号邮箱信息 ",
            name=user.name,
        )
        db.session.commit()
        clear_user_session(user_id=user.id)
        email.successful_registration_notification(user.email)
        db.session.close()
        if current_user.authed():
            return redirect(url_for("challenges.listing"))
        return redirect(url_for("auth.login"))

    # User is trying to start or restart the confirmation flow
    if current_user.authed() is False:
        return redirect(url_for("auth.login"))

    user = Users.query.filter_by(id=session["id"]).first_or_404()
    if user.verified:
        return redirect(url_for("views.settings"))

    if data is None:
        if request.method == "POST":
            # User wants to resend their confirmation email
            result, text = email.verify_email_address(user.email)
            if result:
                log(
                    "registrations",
                    format="[{date}] {name} 在 {ip} 请求重新发送确认邮件",
                    name=user.name,
                )
                if language == "zh":
                    return render_template(
                        "confirm.html", infos=[f"验证邮件已发送至{user.email}!"]
                    )
                else:
                    return render_template(
                        "confirm.html", infos=[f"Confirmation email sent to {user.email}!"]
                    )
            else:
                log(
                    "registrations",
                    format="[{date}] {name} 在 {ip} 请求重新发送确认邮件失败，错误原因{text}",
                    name=user.name,
                    text=text,
                )
                if language == "zh":
                    return render_template(
                        "confirm.html", errors=[f"验证邮件发送失败，请联系管理员!"]
                    )
                else:
                    return render_template(
                        "confirm.html", errors=[f"Confirmation email sent failed,please contact admin!"]
                    )
        elif request.method == "GET":
            # User has been directed to the confirm page
            return render_template("confirm.html")


@auth.route("/reset_password", methods=["POST", "GET"])
@auth.route("/reset_password/<data>", methods=["POST", "GET"])
@ratelimit(method="POST", limit=10, interval=60)
def reset_password(data=None):
    language = request.cookies.get("Scr1wCTFdLanguage", "zh")
    if config.can_send_mail() is False:
        if language == "zh":
            return render_template(
                "reset_password.html",
                errors=[
                    markup(
                        "此 CTF 未配置为发送电子邮件。<br>请联系组织者重置您的密码。"
                    )
                ],
            )
        else:
            return render_template(
                "reset_password.html",
                errors=[
                    markup(
                        "This CTF is not configured to send email.<br> Please contact an organizer to have your password reset."
                    )
                ],
            )

    if data is not None:
        try:
            email_address = unserialize(data, max_age=1800)
        except (BadTimeSignature, SignatureExpired):
            if language == "zh":
                return render_template(
                    "reset_password.html", errors=["您的链接已过期"]
                )
            else:
                return render_template(
                    "reset_password.html", errors=["Your link has expired"]
                )
        except (BadSignature, TypeError, base64.binascii.Error):
            if language == "zh":
                return render_template(
                    "reset_password.html", errors=["您的重置令牌无效"]
                )
            else:
                return render_template(
                    "reset_password.html", errors=["Your reset token is invalid"]
                )

        if request.method == "GET":
            return render_template("reset_password.html", mode="set")
        if request.method == "POST":
            password = request.form.get("password", "").strip()
            user = Users.query.filter_by(email=email_address).first_or_404()
            if user.oauth_id:
                if language == "zh":
                    return render_template(
                        "reset_password.html",
                        infos=[
                            "您的帐户是通过身份验证提供商注册的，没有关联的密码。 请通过您的身份验证提供商登录。"
                        ],
                    )
                else:
                    return render_template(
                        "reset_password.html",
                        infos=[
                            "Your account was registered via an authentication provider and does not have an associated password. Please login via your authentication provider."
                        ],
                    )

            pass_short = len(password) == 0
            if pass_short:
                if language == "zh":
                    return render_template(
                        "reset_password.html", errors=["请选择更长的密码"]
                    )
                else:
                    return render_template(
                        "reset_password.html", errors=["Please pick a longer password"]
                    )

            user.password = password
            db.session.commit()
            clear_user_session(user_id=user.id)
            log(
                "logins",
                format="[{date}] {ip} - 成功重置了 {name} 的密码",
                name=user.name,
            )
            db.session.close()
            email.password_change_alert(user.email)
            return redirect(url_for("auth.login"))

    if request.method == "POST":
        email_address = request.form["email"].strip()
        user = Users.query.filter_by(email=email_address).first()

        get_errors()

        if not user:
            if language == "zh":
                return render_template(
                    "reset_password.html",
                    infos=[
                        "如果该帐户存在，您将收到一封电子邮件，请检查您的收件箱"
                    ],
                )
            else:
                return render_template(
                    "reset_password.html",
                    infos=[
                        "If that account exists you will receive an email, please check your inbox"
                    ],
                )

        if user.oauth_id:
            if language == "zh":
                return render_template(
                    "reset_password.html",
                    infos=[
                        "与此帐户关联的电子邮件地址是通过身份验证提供商注册的，没有关联的密码。 请通过您的身份验证提供商登录。"
                    ],
                )
            else:
                return render_template(
                    "reset_password.html",
                    infos=[
                        "The email address associated with this account was registered via an authentication provider and does not have an associated password. Please login via your authentication provider."
                    ],
                )

        result, text = email.forgot_password(email_address)
        if result:
            if language == "zh":
                return render_template(
                    "reset_password.html",
                    infos=[
                        "如果该帐户存在，您将收到一封电子邮件，请检查您的收件箱"
                    ],
                )
            else:
                return render_template(
                    "reset_password.html",
                    infos=[
                        "If that account exists you will receive an email, please check your inbox"
                    ],
                )
        else:
            if language == "zh":
                return render_template(
                    "reset_password.html", errors=["邮件发送失败，请联系管理员重置密码！"]
                )
            else:
                return render_template(
                    "reset_password.html", errors=["Email send failed, please contact admin for password reset"]
                )
    return render_template("reset_password.html")


@auth.route("/register", methods=["POST", "GET"])
@check_registration_visibility
@ratelimit(method="POST", limit=10, interval=5)
def register():
    language = request.cookies.get("Scr1wCTFdLanguage", "zh")
    errors = get_errors()
    if current_user.authed():
        return redirect(url_for("challenges.listing"))

    sso_enabled = get_config("sso_enabled")
    if sso_enabled == 1:
        # 启用sso统一认证
        ticket = request.args.get("ticket")

        session_ticket = session.get("ticket")

        if ticket:
            session["ticket"] = ticket
            return redirect("/register")
        else:
            if not session_ticket:
                if "?" in request.url:
                    return redirect(
                        get_config("sso_server_address") + "?serviceUrl=" + quote(request.url + "&type=encryptedticket",
                                                                                  safe=""))
                else:
                    return redirect(
                        get_config("sso_server_address") + "?serviceUrl=" + quote(request.url + "?type=encryptedticket",
                                                                                  safe=""))

        ticket = session_ticket

        decrypted_ticket = decrypt_ticket(ticket)
        ticket_data = json.loads(decrypted_ticket)

        snamex = ticket_data.get("USER_NAME")
        sidx = ticket_data.get("ID_NUMBER")

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email_address = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()
            sid = sidx

            website = request.form.get("website")
            affiliation = request.form.get("affiliation")
            country = request.form.get("country")
            registration_code = str(request.form.get("registration_code", ""))

            name_len = len(name) == 0
            names = Users.query.add_columns("name", "id").filter_by(name=name).first()
            emails = (
                Users.query.add_columns("email", "id")
                .filter_by(email=email_address)
                .first()
            )

            sid = Users.query.add_columns("sid", "id").filter_by(sid=sid).first()

            pass_short = len(password) == 0
            pass_long = len(password) > 128
            valid_email = validators.validate_email(email_address)
            team_name_email_check = validators.validate_email(name)

            if get_config("registration_code"):
                if (
                        registration_code.lower()
                        != str(get_config("registration_code", default="")).lower()
                ):
                    if language == "zh":
                        errors.append("注册码错误")
                    else:
                        errors.append("The registration code you entered was incorrect")

            # Process additional user fields
            fields = {}
            for field in UserFields.query.all():
                fields[field.id] = field

            entries = {}
            for field_id, field in fields.items():
                value = request.form.get(f"fields[{field_id}]", "").strip()
                if field.required is True and (value is None or value == ""):
                    if language == "zh":
                        errors.append("请提供所有必填字段")
                    else:
                        errors.append("Please provide all required fields")
                    break

                # Handle special casing of existing profile fields
                if field.name.lower() == "affiliation":
                    affiliation = value
                    break
                elif field.name.lower() == "website":
                    website = value
                    break

                if field.field_type == "boolean":
                    entries[field_id] = bool(value)
                else:
                    entries[field_id] = value

            if country:
                try:
                    validators.validate_country_code(country)
                    valid_country = True
                except ValidationError:
                    valid_country = False
            else:
                valid_country = True

            if website:
                valid_website = validators.validate_url(website)
            else:
                valid_website = True

            if affiliation:
                valid_affiliation = len(affiliation) < 128
            else:
                valid_affiliation = True

            if language == "zh":
                if not valid_email:
                    errors.append("邮箱名无效")
                if email.check_email_is_whitelisted(email_address) is False:
                    errors.append("您的电子邮件地址不是来自允许的域")
                if names:
                    errors.append("名字已经被占用了，换一个吧")
                if team_name_email_check is True:
                    errors.append("你的用户名不能是邮箱名")
                if emails:
                    errors.append("此邮箱已经存在帐号了！")

                if sid:
                    errors.append("此学号已经存在帐号了！")

                if pass_short:
                    errors.append("密码太短了")
                if pass_long:
                    errors.append("密码太长了")
                if name_len:
                    errors.append("名字太短了")
                if valid_website is False:
                    errors.append(
                        "网站必须是以 http 或 https 开头的正确 URL")
                if valid_country is False:
                    errors.append("国家无效")
                if valid_affiliation is False:
                    errors.append("签名过长")
            else:
                if not valid_email:
                    errors.append("Please enter a valid email address")
                if email.check_email_is_whitelisted(email_address) is False:
                    errors.append("Your email address is not from an allowed domain")
                if names:
                    errors.append("That user name is already taken")
                if team_name_email_check is True:
                    errors.append("Your user name cannot be an email address")
                if emails:
                    errors.append("That email has already been used")

                if sid:
                    errors.append("Same student number already in use!")

                if pass_short:
                    errors.append("Pick a longer password")
                if pass_long:
                    errors.append("Pick a shorter password")
                if name_len:
                    errors.append("Pick a longer user name")
                if valid_website is False:
                    errors.append("Websites must be a proper URL starting with http or https")
                if valid_country is False:
                    errors.append("Invalid country")
                if valid_affiliation is False:
                    errors.append("Please provide a shorter affiliation")

            if len(errors) > 0:
                return render_template(
                    "register.html",
                    errors=errors,
                    name=request.form["name"],
                    email=request.form["email"],
                    password=request.form["password"],
                )
            else:
                with app.app_context():
                    user = Users(name=name,
                                 email=email_address,
                                 password=password,
                                 sname=snamex,
                                 sid=sidx
                                 )

                    if website:
                        user.website = website
                    if affiliation:
                        user.affiliation = affiliation
                    if country:
                        user.country = country

                    db.session.add(user)
                    db.session.commit()
                    db.session.flush()

                    for field_id, value in entries.items():
                        entry = UserFieldEntries(
                            field_id=field_id, value=value, user_id=user.id
                        )
                        db.session.add(entry)
                    db.session.commit()

                    login_user(user)

                    if request.args.get("next") and validators.is_safe_url(
                            request.args.get("next")
                    ):
                        return redirect(request.args.get("next"))

                    if config.can_send_mail() and get_config(
                            "verify_emails"
                    ):  # Confirming users is enabled and we can send email.
                        result, text = email.verify_email_address(user.email)
                        if result:
                            log(
                                "registrations",
                                format="[{date}] {name} 在 {ip} 使用 {email} 注册了一个尚未确认邮箱的账户",
                                name=user.name,
                                email=user.email,
                            )
                            db.session.close()
                            return redirect(url_for("auth.confirm"))
                        else:
                            log(
                                "registrations",
                                format="[{date}] {name} 在 {ip} 使用 {email} 注册了一个尚未确认邮箱的账户，验证邮件发送失败",
                                name=user.name,
                                email=user.email,
                            )
                            db.session.close()
                            if language == "zh":
                                return render_template(
                                    "confirm.html", errors=[f"验证邮件发送失败，请联系管理员!"]
                                )
                            else:
                                return render_template(
                                    "confirm.html", errors=[f"Confirmation email sent failed,please contact admin!"]
                                )
                    else:  # Don't care about confirming users
                        if (
                                config.can_send_mail()
                        ):  # We want to notify the user that they have registered.
                            email.successful_registration_notification(user.email)

            log(
                "registrations",
                format="[{date}] {name} 在 {ip} 使用邮箱 {email} 注册了一个账户",
                name=user.name,
                email=user.email,
            )
            db.session.close()

            if is_teams_mode():
                return redirect(url_for("teams.private"))

            return redirect(url_for("challenges.listing"))
        else:
            return render_template("register.html", errors=errors)
    else:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email_address = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()
            sname = request.form.get("sname", "").strip()

            sid = ""
            register_uid = get_config("register_uid")
            if register_uid:
                sid = request.form.get("sid", "").strip()

            website = request.form.get("website")
            affiliation = request.form.get("affiliation")
            country = request.form.get("country")
            registration_code = str(request.form.get("registration_code", ""))

            name_len = len(name) == 0
            names = Users.query.add_columns("name", "id").filter_by(name=name).first()
            emails = (
                Users.query.add_columns("email", "id")
                .filter_by(email=email_address)
                .first()
            )

            if register_uid:
                sid = Users.query.add_columns("sid", "id").filter_by(sid=sid).first()

            pass_short = len(password) == 0
            pass_long = len(password) > 128
            vaild_number = validators.validate_sid(
                request.form.get("sid", "").strip())
            valid_email = validators.validate_email(email_address)
            team_name_email_check = validators.validate_email(name)

            if get_config("registration_code"):
                if (
                        registration_code.lower()
                        != str(get_config("registration_code", default="")).lower()
                ):
                    if language == "zh":
                        errors.append("注册码错误")
                    else:
                        errors.append("The registration code you entered was incorrect")

            # Process additional user fields
            fields = {}
            for field in UserFields.query.all():
                fields[field.id] = field

            entries = {}
            for field_id, field in fields.items():
                value = request.form.get(f"fields[{field_id}]", "").strip()
                if field.required is True and (value is None or value == ""):
                    if language == "zh":
                        errors.append("请提供所有必填字段")
                    else:
                        errors.append("Please provide all required fields")
                    break

                # Handle special casing of existing profile fields
                if field.name.lower() == "affiliation":
                    affiliation = value
                    break
                elif field.name.lower() == "website":
                    website = value
                    break

                if field.field_type == "boolean":
                    entries[field_id] = bool(value)
                else:
                    entries[field_id] = value

            if country:
                try:
                    validators.validate_country_code(country)
                    valid_country = True
                except ValidationError:
                    valid_country = False
            else:
                valid_country = True

            register_uid_empty = get_config("register_uid_empty")

            if language == "zh":
                if not vaild_number:
                    if register_uid:
                        if not register_uid_empty:
                            errors.append("请输入有效的学号")
                        else:
                            if not request.form.get("sid", "").strip() == "":
                                errors.append("请输入有效的学号")
            else:
                if not vaild_number:
                    if register_uid:
                        if not register_uid_empty:
                            errors.append("Please enter a valid student number")
                        else:
                            if not request.form.get("sid", "").strip() == "":
                                errors.append("Please enter a valid student number")

            if website:
                valid_website = validators.validate_url(website)
            else:
                valid_website = True

            if affiliation:
                valid_affiliation = len(affiliation) < 128
            else:
                valid_affiliation = True

            if language == "zh":
                if not valid_email:
                    errors.append("邮箱名无效")
                if email.check_email_is_whitelisted(email_address) is False:
                    errors.append("您的电子邮件地址不是来自允许的域")
                if names:
                    errors.append("名字已经被占用了，换一个吧")
                if team_name_email_check is True:
                    errors.append("你的用户名不能是邮箱名")
                if emails:
                    errors.append("此邮箱已经存在帐号了！")

                if register_uid:
                    if sid:
                        if request.form.get("sid", "").strip() == "":
                            if not register_uid_empty:
                                errors.append("学号不能为空！")
                        else:
                            errors.append("此学号已经存在帐号了！")

                if pass_short:
                    errors.append("密码太短了")
                if pass_long:
                    errors.append("密码太长了")
                if name_len:
                    errors.append("名字太短了")
                if valid_website is False:
                    errors.append(
                        "网站必须是以 http 或 https 开头的正确 URL")
                if valid_country is False:
                    errors.append("国家无效")
                if valid_affiliation is False:
                    errors.append("签名过长")
            else:
                if not valid_email:
                    errors.append("Please enter a valid email address")
                if email.check_email_is_whitelisted(email_address) is False:
                    errors.append("Your email address is not from an allowed domain")
                if names:
                    errors.append("That user name is already taken")
                if team_name_email_check is True:
                    errors.append("Your user name cannot be an email address")
                if emails:
                    errors.append("That email has already been used")

                if register_uid:
                    if sid:
                        if request.form.get("sid", "").strip() == "":
                            if not register_uid_empty:
                                errors.append("Student number cannot be empty!")
                        else:
                            errors.append("Same student number already in use!")

                if pass_short:
                    errors.append("Pick a longer password")
                if pass_long:
                    errors.append("Pick a shorter password")
                if name_len:
                    errors.append("Pick a longer user name")
                if valid_website is False:
                    errors.append("Websites must be a proper URL starting with http or https")
                if valid_country is False:
                    errors.append("Invalid country")
                if valid_affiliation is False:
                    errors.append("Please provide a shorter affiliation")

            if len(errors) > 0:
                return render_template(
                    "register.html",
                    errors=errors,
                    name=request.form["name"],
                    email=request.form["email"],
                    password=request.form["password"],
                )
            else:
                with app.app_context():
                    user = Users(name=name,
                                 email=email_address,
                                 password=password,
                                 sname=request.form.get("sname", "").strip(),
                                 sid=request.form.get("sid", "").strip())

                    if website:
                        user.website = website
                    if affiliation:
                        user.affiliation = affiliation
                    if country:
                        user.country = country

                    db.session.add(user)
                    db.session.commit()
                    db.session.flush()

                    for field_id, value in entries.items():
                        entry = UserFieldEntries(
                            field_id=field_id, value=value, user_id=user.id
                        )
                        db.session.add(entry)
                    db.session.commit()

                    login_user(user)

                    if request.args.get("next") and validators.is_safe_url(
                            request.args.get("next")
                    ):
                        return redirect(request.args.get("next"))

                    if config.can_send_mail() and get_config(
                            "verify_emails"
                    ):  # Confirming users is enabled and we can send email.
                        result, text = email.verify_email_address(user.email)
                        if result:
                            log(
                                "registrations",
                                format="[{date}] {name} 在 {ip} 使用 {email} 注册了一个尚未确认邮箱的账户",
                                name=user.name,
                                email=user.email,
                            )
                            db.session.close()
                            return redirect(url_for("auth.confirm"))
                        else:
                            log(
                                "registrations",
                                format="[{date}] {name} 在 {ip} 使用 {email} 注册了一个尚未确认邮箱的账户，验证邮件发送失败",
                                name=user.name,
                                email=user.email,
                            )
                            db.session.close()
                            if language == "zh":
                                return render_template(
                                    "confirm.html", errors=[f"验证邮件发送失败，请联系管理员!"]
                                )
                            else:
                                return render_template(
                                    "confirm.html", errors=[f"Confirmation email sent failed,please contact admin!"]
                                )
                    else:  # Don't care about confirming users
                        if (
                                config.can_send_mail()
                        ):  # We want to notify the user that they have registered.
                            email.successful_registration_notification(user.email)

            log(
                "registrations",
                format="[{date}] {name} 在 {ip} 使用邮箱 {email} 注册了一个账户",
                name=user.name,
                email=user.email,
            )
            db.session.close()

            if is_teams_mode():
                return redirect(url_for("teams.private"))

            return redirect(url_for("challenges.listing"))
        else:
            return render_template("register.html", errors=errors)


@auth.route("/login", methods=["POST", "GET"])
@ratelimit(method="POST", limit=10, interval=5)
def login():
    language = request.cookies.get("Scr1wCTFdLanguage", "zh")
    errors = get_errors()
    if request.method == "POST":
        name = request.form["name"]

        # Check if the user submitted an email address or a team name
        if validators.validate_email(name) is True:
            user = Users.query.filter_by(email=name).first()
        else:
            user = Users.query.filter_by(name=name).first()

        if user:
            if user.password is None:
                if language == "zh":
                    errors.append(
                        "您的帐户已通过第三方身份验证提供商注册。"
                        "请尝试使用配置的身份验证提供程序登录。"
                    )
                else:
                    errors.append(
                        "Your account was registered with a 3rd party authentication provider. "
                        "Please try logging in with a configured authentication provider."
                    )
                return render_template("login.html", errors=errors)

            if user and verify_password(request.form["password"], user.password):
                session.regenerate()

                login_user(user)
                log("logins", "[{date}] {name} 在 {ip} 登陆", name=user.name)

                db.session.close()
                if request.args.get("next") and validators.is_safe_url(
                        request.args.get("next")
                ):
                    return redirect(request.args.get("next"))
                return redirect(url_for("challenges.listing"))

            else:
                # This user exists but the password is wrong
                log(
                    "logins",
                    "[{date}] {ip} 在尝试登陆 {name} 时提交了错误的密码",
                    name=user.name,
                )
                if language == "zh":
                    errors.append("账户名或密码错误")
                else:
                    errors.append("Your username or password is incorrect")

                db.session.close()
                return render_template("login.html", errors=errors)
        else:
            # This user just doesn't exist
            log("logins", "[{date}] {ip} 尝试登陆一个不存在的账号")
            if language == "zh":
                errors.append("账户名或密码错误")
            else:
                errors.append("Your username or password is incorrect")

            db.session.close()
            return render_template("login.html", errors=errors)
    else:
        ticket = request.args.get("ticket")
        if ticket:
            try:
                decrypted_ticket = decrypt_ticket(ticket)
                json_data = json.loads(decrypted_ticket)
                id_number = json_data.get('ID_NUMBER')
                user_name = json_data.get('USER_NAME')
                user = Users.query.filter_by(sid=id_number).first()
                if user:
                    if user.sname:
                        if user.sname == user_name:
                            session.regenerate()
                            login_user(user)
                            log("logins", "[{date}] {name} 在 {ip} 通过sso认证登陆", name=user.name)
                            db.session.close()
                            if request.args.get("next") and validators.is_safe_url(
                                    request.args.get("next")):
                                return redirect(request.args.get("next"))
                            return redirect(url_for("challenges.listing"))
                if language == "zh":
                    errors.append("账户不存在或对应账户未实名")
                else:
                    errors.append("The account does not exist or the corresponding account's real name is not verified")
                return render_template("login.html", errors=errors)
            except Exception as e:
                db.session.close()
                if language == "zh":
                    errors.append("身份验证失败")
                else:
                    errors.append("Authentication failed")
                print(e)
                return render_template("login.html", errors=errors)
        else:
            db.session.close()
            return render_template("login.html", errors=errors)


def decrypt_ticket(ticket):
    # 解密的密钥（假设为32字节长度的密钥）
    key = b"key"  # 替换为你的密钥
    # 使用base64解码ticket参数
    encrypted_data = base64.b64decode(ticket)
    # 创建AES CBC解密器
    cipher = Cipher(algorithms.AES(key), modes.CBC(b"iv"), backend=default_backend())
    decryptor = cipher.decryptor()
    # 解密数据
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
    # 使用PKCS7填充模式删除填充
    unpadder = padding.PKCS7(128).unpadder()
    decrypted_data = unpadder.update(decrypted_data) + unpadder.finalize()
    # 返回解密后的数据（假设为字符串）
    return decrypted_data.decode("utf-8")


@auth.route("/oauth")
def oauth_login():
    language = request.cookies.get("Scr1wCTFdLanguage", "zh")
    endpoint = (
            get_app_config("OAUTH_AUTHORIZATION_ENDPOINT")
            or get_config("oauth_authorization_endpoint")
            or "https://auth.majorleaguecyber.org/oauth/authorize"
    )

    if get_config("user_mode") == "teams":
        scope = "profile team"
    else:
        scope = "profile"

    client_id = get_app_config("OAUTH_CLIENT_ID") or get_config("oauth_client_id")

    if client_id is None:
        if language == "zh":
            error_for(
                endpoint="auth.login",
                message="未配置 OAuth 设置。"
                        "请您的 CTF 管理员配置 MLC 集成。",
            )
        else:
            error_for(
                endpoint="auth.login",
                message="OAuth Settings not configured. "
                        "Ask your CTF administrator to configure MajorLeagueCyber integration.",
            )
        return redirect(url_for("auth.login"))

    redirect_url = "{endpoint}?response_type=code&client_id={client_id}&scope={scope}&state={state}".format(
        endpoint=endpoint, client_id=client_id, scope=scope, state=session["nonce"]
    )
    return redirect(redirect_url)


@auth.route("/redirect", methods=["GET"])
@ratelimit(method="GET", limit=10, interval=60)
def oauth_redirect():
    language = request.cookies.get("Scr1wCTFdLanguage", "zh")
    oauth_code = request.args.get("code")
    state = request.args.get("state")
    if session["nonce"] != state:
        log("logins", "[{date}] {ip} - OAuth 状态验证不匹配")
        if language == "zh":
            error_for(endpoint="auth.login", message="OAuth 状态验证不匹配。")
        else:
            error_for(endpoint="auth.login", message="OAuth State validation mismatch.")

        return redirect(url_for("auth.login"))

    if oauth_code:
        url = (
                get_app_config("OAUTH_TOKEN_ENDPOINT")
                or get_config("oauth_token_endpoint")
                or "https://auth.majorleaguecyber.org/oauth/token"
        )

        client_id = get_app_config("OAUTH_CLIENT_ID") or get_config("oauth_client_id")
        client_secret = get_app_config("OAUTH_CLIENT_SECRET") or get_config(
            "oauth_client_secret"
        )
        headers = {"content-type": "application/x-www-form-urlencoded"}
        data = {
            "code": oauth_code,
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
        }
        token_request = requests.post(url, data=data, headers=headers)

        if token_request.status_code == requests.codes.ok:
            token = token_request.json()["access_token"]
            user_url = (
                    get_app_config("OAUTH_API_ENDPOINT")
                    or get_config("oauth_api_endpoint")
                    or "https://api.majorleaguecyber.org/user"
            )

            headers = {
                "Authorization": "Bearer " + str(token),
                "Content-type": "application/json",
            }
            api_data = requests.get(url=user_url, headers=headers).json()

            user_id = api_data["id"]
            user_name = api_data["name"]
            user_email = api_data["email"]

            user = Users.query.filter_by(email=user_email).first()
            if user is None:
                # Check if we are allowing registration before creating users
                if registration_visible() or mlc_registration():
                    user = Users(
                        name=user_name,
                        email=user_email,
                        oauth_id=user_id,
                        verified=True,
                    )
                    db.session.add(user)
                    db.session.commit()
                else:
                    log("logins", "[{date}] {ip} - 通过 MLC 的公共注册被阻止")
                    if language == "zh":
                        error_for(
                            endpoint="auth.login",
                            message="公共注册被禁用。 请稍后再试。",
                        )
                    else:
                        error_for(
                            endpoint="auth.login",
                            message="Public registration is disabled. Please try again later.",
                        )

                    return redirect(url_for("auth.login"))

            if get_config("user_mode") == TEAMS_MODE and user.team_id is None:
                team_id = api_data["team"]["id"]
                team_name = api_data["team"]["name"]

                team = Teams.query.filter_by(oauth_id=team_id).first()
                if team is None:
                    num_teams_limit = int(get_config("num_teams", default=0))
                    num_teams = Teams.query.filter_by(
                        banned=False, hidden=False
                    ).count()
                    if num_teams_limit and num_teams >= num_teams_limit:
                        if language == "zh":
                            abort(
                                403,
                                description=f"已达到最大团队数量 ({num_teams_limit})。 请加入现有团队。",
                            )
                        else:
                            abort(
                                403,
                                description=f"Reached the maximum number of teams ({num_teams_limit}). Please join an existing team.",
                            )

                    team = Teams(name=team_name, oauth_id=team_id, captain_id=user.id)
                    db.session.add(team)
                    db.session.commit()
                    clear_team_session(team_id=team.id)

                team_size_limit = get_config("team_size", default=0)
                if team_size_limit and len(team.members) >= team_size_limit:
                    if language == "zh":
                        size_error = "队伍上线{limit}人。".format(
                            limit=team_size_limit
                        )
                        error_for(endpoint="auth.login", message=size_error)
                        return redirect(url_for("auth.login"))
                    else:
                        plural = "" if team_size_limit == 1 else "s"
                        size_error = "Teams are limited to {limit} member{plural}.".format(
                            limit=team_size_limit, plural=plural
                        )
                        error_for(endpoint="auth.login", message=size_error)
                        return redirect(url_for("auth.login"))

                team.members.append(user)
                db.session.commit()

            if user.oauth_id is None:
                user.oauth_id = user_id
                user.verified = True
                db.session.commit()
                clear_user_session(user_id=user.id)

            login_user(user)

            return redirect(url_for("challenges.listing"))
        else:
            log("logins", "[{date}] {ip} - OAuth 令牌检索失败。")
            if language == "zh":
                error_for(endpoint="auth.login", message="OAuth 令牌检索失败。")
            else:
                error_for(endpoint="auth.login", message="OAuth token retrieval failure.")
            return redirect(url_for("auth.login"))
    else:
        log("logins", "[{date}] {ip} - 收到没有 OAuth 代码的重定向。")
        if language == "zh":
            error_for(
                endpoint="auth.login", message="收到没有 OAuth 代码的重定向。"
            )
        else:
            error_for(
                endpoint="auth.login", message="Received redirect without OAuth code."
            )
        return redirect(url_for("auth.login"))


@auth.route("/logout")
def logout():
    if current_user.authed():
        logout_user()
    return redirect(url_for("views.static_html"))
