import os  # noqa: I001

from flask import Blueprint, abort
from flask import current_app as app
from flask import (
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from flask.helpers import safe_join
from jinja2.exceptions import TemplateNotFound
from sqlalchemy.exc import IntegrityError

from CTFd.cache import cache
from CTFd.constants.config import (
    AccountVisibilityTypes,
    ChallengeVisibilityTypes,
    ConfigTypes,
    RegistrationVisibilityTypes,
    ScoreVisibilityTypes,
)
from CTFd.constants.themes import DEFAULT_THEME
from CTFd.models import (
    Admins,
    Files,
    Notifications,
    Pages,
    Teams,
    Users,
    UserTokens,
    db,
)
from CTFd.utils import config, get_config, set_config
from CTFd.utils import user as current_user
from CTFd.utils import validators
from CTFd.utils.config import is_setup, is_teams_mode
from CTFd.utils.config.pages import build_markdown, get_page
from CTFd.utils.config.visibility import challenges_visible
from CTFd.utils.dates import ctf_ended, ctftime, view_after_ctf
from CTFd.utils.decorators import authed_only
from CTFd.utils.email import (
    DEFAULT_PASSWORD_RESET_BODY,
    DEFAULT_PASSWORD_RESET_SUBJECT,
    DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_BODY,
    DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_SUBJECT,
    DEFAULT_USER_CREATION_EMAIL_BODY,
    DEFAULT_USER_CREATION_EMAIL_SUBJECT,
    DEFAULT_VERIFICATION_EMAIL_BODY,
    DEFAULT_VERIFICATION_EMAIL_SUBJECT,
)
from CTFd.utils.health import check_config, check_database
from CTFd.utils.helpers import get_errors, get_infos, markup
from CTFd.utils.modes import USERS_MODE
from CTFd.utils.security.auth import login_user
from CTFd.utils.security.csrf import generate_nonce
from CTFd.utils.security.signing import (
    BadSignature,
    BadTimeSignature,
    SignatureExpired,
    serialize,
    unserialize,
)
from CTFd.utils.uploads import get_uploader, upload_file
from CTFd.utils.user import authed, get_current_team, get_current_user, is_admin

views = Blueprint("views", __name__)


@views.route("/setup", methods=["GET", "POST"])
def setup():
    errors = get_errors()
    if not config.is_setup():
        if not session.get("nonce"):
            session["nonce"] = generate_nonce()
        if request.method == "POST":
            # General
            ctf_name = request.form.get("ctf_name")
            ctf_description = request.form.get("ctf_description")
            user_mode = request.form.get("user_mode", USERS_MODE)
            set_config("ctf_name", ctf_name)
            set_config("ctf_description", ctf_description)
            set_config("user_mode", user_mode)

            # Robot
            bot = request.form.get("bot")
            bottext = request.form.get("bottext")  # 解题播报消息 e.g.恭喜%s做出题目%s，默认第一个参数为用户名，第二个参数为题目名称
            createtext = request.form.get("createtext")  # 题目可见播报
            updatetext = request.form.get("updatetext")  # 题目更新播报

            # 上面三个text为用户自定格式化字符串，处理不正确将存在FSA漏洞
            # 检查 bottext 中 % 和 %s 的数量是否符合要求
            if bottext is not None:
                if bottext.count('%') != 2 or bottext.count('%s') != 2:
                    errors.append("bottext must contain exactly two '%' and two '%s' placeholders")
            # 检查 createtext 中 % 和 %s 的数量是否符合要求
            if createtext is not None:
                if createtext.count('%') != 2 or createtext.count('%s') != 2:
                    errors.append("createtext must contain exactly two '%' and two '%s' placeholders")
            # 检查 updatetext 中 % 和 %s 的数量是否符合要求
            if updatetext is not None:
                if updatetext.count('%') != 2 or updatetext.count('%s') != 2:
                    errors.append("updatetext must contain exactly two '%' and two '%s' placeholders")

            group_id = request.form.get("group_id")  # qq群号
            bot_ip = request.form.get("bot_ip")  # 机器人服务地址,如 127.0.0.1:8000
            set_config("bot", bot)
            set_config("bottext", bottext)
            set_config("createtext", createtext)
            set_config("updatetext", updatetext)
            set_config("group_id", group_id)
            set_config("bot_ip", bot_ip)

            # Style
            ctf_logo = request.files.get("ctf_logo")
            if ctf_logo:
                f = upload_file(file=ctf_logo)
                set_config("ctf_logo", f.location)

            ctf_small_icon = request.files.get("ctf_small_icon")
            if ctf_small_icon:
                f = upload_file(file=ctf_small_icon)
                set_config("ctf_small_icon", f.location)

            theme = request.form.get("ctf_theme", DEFAULT_THEME)
            set_config("ctf_theme", theme)
            theme_color = request.form.get("theme_color")
            theme_header = get_config("theme_header")
            if theme_color and bool(theme_header) is False:
                # Uses {{ and }} to insert curly braces while using the format method
                css = (
                    '<style id="theme-color">\n'
                    ":root {{--theme-color: {theme_color};}}\n"
                    ".navbar{{background-color: var(--theme-color) !important;}}\n"
                    ".jumbotron{{background-color: var(--theme-color) !important;}}\n"
                    "</style>\n"
                ).format(theme_color=theme_color)
                set_config("theme_header", css)

            # DateTime
            start = request.form.get("start")
            end = request.form.get("end")
            set_config("start", start)
            set_config("end", end)
            set_config("freeze", None)

            # Administration
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]

            name_len = len(name) == 0
            names = Users.query.add_columns("name", "id").filter_by(name=name).first()
            emails = (
                Users.query.add_columns("email", "id").filter_by(email=email).first()
            )
            pass_short = len(password) == 0
            pass_long = len(password) > 128
            valid_email = validators.validate_email(request.form["email"])
            team_name_email_check = validators.validate_email(name)

            language = request.cookies.get("Scr1wCTFdLanguage", "zh")
            if language == "zh":
                if not valid_email:
                    errors.append("请输入有效的邮箱地址")
                if names:
                    errors.append("名字已经被占用了，换一个吧")
                if team_name_email_check is True:
                    errors.append("你的用户名不能是邮箱名")
                if emails:
                    errors.append("此邮箱已经存在帐号了！")
                if pass_short:
                    errors.append("密码太短了")
                if pass_long:
                    errors.append("密码太长了")
                if name_len:
                    errors.append("名字太短了")
            else:
                if not valid_email:
                    errors.append("Please enter a valid email address")
                if names:
                    errors.append("That user name is already taken")
                if team_name_email_check is True:
                    errors.append("Your user name cannot be an email address")
                if emails:
                    errors.append("That email has already been used")
                if pass_short:
                    errors.append("Pick a longer password")
                if pass_long:
                    errors.append("Pick a shorter password")
                if name_len:
                    errors.append("Pick a longer user name")

            if len(errors) > 0:
                return render_template(
                    "setup.html",
                    errors=errors,
                    name=name,
                    email=email,
                    password=password,
                    state=serialize(generate_nonce()),
                )

            admin = Admins(
                name=name, email=email, password=password, type="admin", hidden=True
            )

            # Create an empty index page
            page = Pages(title=None, route="index", content="", draft=False)

            # Upload banner
            default_ctf_banner_location = url_for("views.themes", path="img/logo.png")
            ctf_banner = request.files.get("ctf_banner")
            if ctf_banner:
                f = upload_file(file=ctf_banner, page_id=page.id)
                default_ctf_banner_location = url_for("views.files", path=f.location)

            # Splice in our banner
            index = f"""<div class="row">
    <div class="col-md-6 offset-md-3">
        <img class="w-100 mx-auto d-block" style="max-width: 500px;padding: 50px;padding-top: 14vh;" src="/themes/core/static/img/logo.png?d=a33b5bf6" />
        <h3 class="text-center">
            <p>来自 <a href="http://scr1w.dlut.edu.cn/">Scr1w</a> 的一个很酷的 CTF 平台</p>
            <p>在社交媒体上关注我们：</p>
            <a href="https://space.bilibili.com/690549848"><i class="fab fa-youtube fa-2x" aria-hidden="true"></i></a>&nbsp;
            <a href="https://github.com/dlut-sss"><i class="fab fa-github fa-2x" aria-hidden="true"></i></a>
        </h3>
        <br>
        <h4 class="text-center">
            <a href="admin">点击此处</a>登录并设置您的 CTF
        </h4>
    </div>
</div>"""
            page.content = index

            # Visibility
            set_config(
                ConfigTypes.CHALLENGE_VISIBILITY, ChallengeVisibilityTypes.PRIVATE
            )
            set_config(
                ConfigTypes.REGISTRATION_VISIBILITY, RegistrationVisibilityTypes.PUBLIC
            )
            set_config(ConfigTypes.SCORE_VISIBILITY, ScoreVisibilityTypes.PUBLIC)
            set_config(ConfigTypes.ACCOUNT_VISIBILITY, AccountVisibilityTypes.PUBLIC)

            # Verify emails
            set_config("verify_emails", None)

            set_config("mail_server", None)
            set_config("mail_port", None)
            set_config("mail_tls", None)
            set_config("mail_ssl", None)
            set_config("mail_username", None)
            set_config("mail_password", None)
            set_config("mail_useauth", None)

            # Set up default emails
            set_config("verification_email_subject", DEFAULT_VERIFICATION_EMAIL_SUBJECT)
            set_config("verification_email_body", DEFAULT_VERIFICATION_EMAIL_BODY)

            set_config(
                "successful_registration_email_subject",
                DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_SUBJECT,
            )
            set_config(
                "successful_registration_email_body",
                DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_BODY,
            )

            set_config(
                "user_creation_email_subject", DEFAULT_USER_CREATION_EMAIL_SUBJECT
            )
            set_config("user_creation_email_body", DEFAULT_USER_CREATION_EMAIL_BODY)

            set_config("password_reset_subject", DEFAULT_PASSWORD_RESET_SUBJECT)
            set_config("password_reset_body", DEFAULT_PASSWORD_RESET_BODY)

            set_config(
                "password_change_alert_subject",
                "{ctf_name} 的密码更改确认",
            )
            set_config(
                "password_change_alert_body",
                (
                    "您的 {ctf_name} 密码已更改。\n\n"
                    "如果您没有请求更改密码，您可以在此处重置密码：{url}"
                ),
            )

            # 默认关闭QQbot播报
            set_config("bot", 0)

            # sso默认设置
            set_config("sso_auth", 0)
            set_config("sso_enabled", 0)
            set_config("register_uid", 0)
            set_config("register_uid_empty", 0)

            set_config("setup", True)

            try:
                db.session.add(admin)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

            try:
                db.session.add(page)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

            login_user(admin)

            db.session.close()
            with app.app_context():
                cache.clear()

            return redirect(url_for("views.static_html"))
        try:
            return render_template("setup.html", state=serialize(generate_nonce()))
        except TemplateNotFound:
            # Set theme to default and try again
            set_config("ctf_theme", DEFAULT_THEME)
            return render_template("setup.html", state=serialize(generate_nonce()))
    return redirect(url_for("views.static_html"))


@views.route("/setup/integrations", methods=["GET", "POST"])
def integrations():
    if is_admin() or is_setup() is False:
        name = request.values.get("name")
        state = request.values.get("state")

        try:
            state = unserialize(state, max_age=3600)
        except (BadSignature, BadTimeSignature):
            state = False
        except Exception:
            state = False

        if state:
            if name == "mlc":
                mlc_client_id = request.values.get("mlc_client_id")
                mlc_client_secret = request.values.get("mlc_client_secret")
                set_config("oauth_client_id", mlc_client_id)
                set_config("oauth_client_secret", mlc_client_secret)
                return render_template("admin/integrations.html")
            else:
                abort(404)
        else:
            abort(403)
    else:
        abort(403)


@views.route("/notifications", methods=["GET"])
def notifications():
    notifications = Notifications.query.order_by(Notifications.id.desc()).all()
    return render_template("notifications.html", notifications=notifications)


@views.route("/settings", methods=["GET"])
@authed_only
def settings():
    infos = get_infos()
    errors = get_errors()
    language = request.cookies.get("Scr1wCTFdLanguage", "zh")

    user = get_current_user()
    name = user.name
    email = user.email
    sname = user.sname
    sid = user.sid
    website = user.website
    affiliation = user.affiliation
    country = user.country

    if is_teams_mode() and get_current_team() is None:
        team_url = url_for("teams.private")
        if language == "zh":
            infos.append(
                markup(
                    f'为了参与，您必须<a href="{team_url}">加入或创建团队</a>。'
                )
            )
        else:
            infos.append(
                markup(
                    f'In order to participate you must either <a href="{team_url}">join or create a team</a>.'
                )
            )

    tokens = UserTokens.query.filter_by(user_id=user.id).all()

    prevent_name_change = get_config("prevent_name_change")

    if get_config("verify_emails") and not user.verified:
        confirm_url = markup(url_for("auth.confirm"))
        if language == "zh":
            infos.append(
                markup(
                    "您的电子邮件地址尚未确认！<br>"
                    "请检查您的电子邮件以确认您的电子邮件地址。<br>"
                    f'如需重新发送确认电子邮件，请 <a href="{confirm_url}">点击此处</a>.'
                )
            )
        else:
            infos.append(
                markup(
                    "Your email address isn't confirmed!<br>"
                    "Please check your email to confirm your email address.<br>"
                    f'To have the confirmation email resent please <a href="{confirm_url}">click here</a>.'
                )
            )

    return render_template(
        "settings.html",
        name=name,
        email=email,
        sname=sname,
        sid=sid,
        website=website,
        affiliation=affiliation,
        country=country,
        tokens=tokens,
        prevent_name_change=prevent_name_change,
        infos=infos,
        errors=errors,
    )


@views.route("/", defaults={"route": "index"})
@views.route("/<path:route>")
def static_html(route):
    """
    Route in charge of routing users to Pages.
    :param route:
    :return:
    """
    page = get_page(route)
    if page is None:
        abort(404)
    else:
        if page.auth_required and authed() is False:
            return redirect(url_for("auth.login", next=request.full_path))

        return render_template("page.html", content=page.html, title=page.title)


@views.route("/tos")
def tos():
    tos_url = get_config("tos_url")
    tos_text = get_config("tos_text")
    if tos_url:
        return redirect(tos_url)
    elif tos_text:
        return render_template("page.html", content=build_markdown(tos_text))
    else:
        abort(404)


@views.route("/privacy")
def privacy():
    privacy_url = get_config("privacy_url")
    privacy_text = get_config("privacy_text")
    if privacy_url:
        return redirect(privacy_url)
    elif privacy_text:
        return render_template("page.html", content=build_markdown(privacy_text))
    else:
        abort(404)


@views.route("/files", defaults={"path": ""})
@views.route("/files/<path:path>")
def files(path):
    """
    Route in charge of dealing with making sure that CTF challenges are only accessible during the competition.
    :param path:
    :return:
    """
    f = Files.query.filter_by(location=path).first_or_404()
    if f.type == "challenge":
        if challenges_visible():
            if current_user.is_admin() is False:
                if not ctftime():
                    if ctf_ended() and view_after_ctf():
                        pass
                    else:
                        abort(403)
        else:
            # User cannot view challenges based on challenge visibility
            # e.g. ctf requires registration but user isn't authed or
            # ctf requires admin account but user isn't admin
            if not ctftime():
                # It's not CTF time. The only edge case is if the CTF is ended
                # but we have view_after_ctf enabled
                if ctf_ended() and view_after_ctf():
                    pass
                else:
                    # In all other situations we should block challenge files
                    abort(403)

            # Allow downloads if a valid token is provided
            token = request.args.get("token", "")
            try:
                data = unserialize(token, max_age=3600)
                user_id = data.get("user_id")
                team_id = data.get("team_id")
                file_id = data.get("file_id")
                user = Users.query.filter_by(id=user_id).first()
                team = Teams.query.filter_by(id=team_id).first()

                # Check user is admin if challenge_visibility is admins only
                if (
                        get_config(ConfigTypes.CHALLENGE_VISIBILITY) == "admins"
                        and user.type != "admin"
                ):
                    abort(403)

                # Check that the user exists and isn't banned
                if user:
                    if user.banned:
                        abort(403)
                else:
                    abort(403)

                # Check that the team isn't banned
                if team:
                    if team.banned:
                        abort(403)
                else:
                    pass

                # Check that the token properly refers to the file
                if file_id != f.id:
                    abort(403)

            # The token isn't expired or broken
            except (BadTimeSignature, SignatureExpired, BadSignature):
                abort(403)

    uploader = get_uploader()
    try:
        return uploader.download(f.location)
    except IOError:
        abort(404)


@views.route("/themes/<theme>/static/<path:path>")
def themes(theme, path):
    """
    General static file handler
    :param theme:
    :param path:
    :return:
    """
    for cand_path in (
            safe_join(app.root_path, "themes", cand_theme, "static", path)
            # The `theme` value passed in may not be the configured one, e.g. for
            # admin pages, so we check that first
            for cand_theme in (theme, *config.ctf_theme_candidates())
    ):
        if os.path.isfile(cand_path):
            return send_file(cand_path)
    abort(404)


@views.route("/themes/<theme>/static/<path:path>")
def themes_beta(theme, path):
    """
    This is a copy of the above themes route used to avoid
    the current appending of .dev and .min for theme assets.

    In CTFd 4.0 this url_for behavior and this themes_beta
    route will be removed.
    """
    for cand_path in (
            safe_join(app.root_path, "themes", cand_theme, "static", path)
            # The `theme` value passed in may not be the configured one, e.g. for
            # admin pages, so we check that first
            for cand_theme in (theme, *config.ctf_theme_candidates())
    ):
        if os.path.isfile(cand_path):
            return send_file(cand_path)
    abort(404)


@views.route("/healthcheck")
def healthcheck():
    if check_database() is False:
        return "ERR", 500
    if check_config() is False:
        return "ERR", 500
    return "OK", 200


@views.route("/robots.txt")
def robots():
    text = get_config("robots_txt", "User-agent: *\nDisallow: /admin\n")
    r = make_response(text, 200)
    r.mimetype = "text/plain"
    return r
