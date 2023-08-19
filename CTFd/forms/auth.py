from wtforms import PasswordField, StringField
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired

from CTFd.forms import BaseForm
from CTFd.forms.fields import SubmitField
from CTFd.forms.users import (
    attach_custom_user_fields,
    attach_registration_code_field,
    build_custom_user_fields,
    build_registration_code_field,
)
from CTFd.utils import get_config


def RegistrationForm(*args, **kwargs):
    class _RegistrationForm(BaseForm):
        name = StringField(
            "用户名", validators=[InputRequired()], render_kw={"autofocus": True}
        )
        email = EmailField("邮箱地址", validators=[InputRequired()])
        sname = StringField("真实姓名", validators=[InputRequired()])
        sid = StringField("学号", validators=[InputRequired()])
        register_uid_empty = get_config("register_uid_empty")
        if register_uid_empty:
            sid = StringField("学号")
        password = PasswordField("密码", validators=[InputRequired()])
        submit = SubmitField("提交")

        @property
        def extra(self):
            return build_custom_user_fields(
                self, include_entries=False, blacklisted_items=()
            ) + build_registration_code_field(self)

    attach_custom_user_fields(_RegistrationForm)
    attach_registration_code_field(_RegistrationForm)

    return _RegistrationForm(*args, **kwargs)


class LoginForm(BaseForm):
    name = StringField(
        "用户名或邮箱",
        validators=[InputRequired()],
        render_kw={"autofocus": True},
    )
    password = PasswordField("密码", validators=[InputRequired()])
    submit = SubmitField("提交")


class ConfirmForm(BaseForm):
    submit = SubmitField("重新发送确认邮件")


class ResetPasswordRequestForm(BaseForm):
    email = EmailField(
        "邮箱", validators=[InputRequired()], render_kw={"autofocus": True}
    )
    submit = SubmitField("提交")


class ResetPasswordForm(BaseForm):
    password = PasswordField(
        "密码", validators=[InputRequired()], render_kw={"autofocus": True}
    )
    submit = SubmitField("提交")
