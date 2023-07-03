from wtforms import (
    FileField,
    HiddenField,
    PasswordField,
    RadioField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired

from CTFd.constants.themes import DEFAULT_THEME
from CTFd.forms import BaseForm
from CTFd.forms.fields import SubmitField
from CTFd.utils.config import get_themes


class SetupForm(BaseForm):
    ctf_name = StringField(
        "赛事名称", description="您的 CTF 名称"
    )
    ctf_description = TextAreaField(
        "活动简介", description="CTF 简介"
    )
    user_mode = RadioField(
        "用户模式",
        choices=[("teams", "团队模式"), ("users", "用户模式")],
        default="users",
        description="控制用户是否加入团队一起答题（团队模式）或单人答题（用户模式）",
        validators=[InputRequired()],
    )

    name = StringField(
        "管理员用户名",
        description="您的管理帐户的用户名",
        validators=[InputRequired()],
    )
    email = EmailField(
        "管理员邮箱",
        description="您的管理帐户的电子邮件地址",
        validators=[InputRequired()],
    )
    password = PasswordField(
        "管理员密码",
        description="您的管理帐户的密码",
        validators=[InputRequired()],
    )

    ctf_logo = FileField(
        "Logo",
        description="用于网站的徽标，而不是 CTF 名称。 用作主页按钮。 可选。",
    )
    ctf_banner = FileField(
        "横幅", description="用于主页的横幅。可选。"
    )
    ctf_small_icon = FileField(
        "小图标",
        description="用户浏览器中使用的图标。 仅接受 PNG。 必须为 32x32 像素。 可选。",
    )
    ctf_theme = SelectField(
        "主题",
        description="要使用的 CTFd 主题。 以后可以更改。",
        choices=list(zip(get_themes(), get_themes())),
        default=DEFAULT_THEME,
        validators=[InputRequired()],
    )
    theme_color = HiddenField(
        "主题颜色",
        description="主题使用颜色来控制美观。 需要主题支持。 可选。",
    )

    start = StringField(
        "开始时间", description="您的 CTF 计划开始的时间。 可选。"
    )
    end = StringField(
        "结束时间", description="您的 CTF 计划结束的时间。 可选。"
    )
    submit = SubmitField("完成")
