from wtforms import BooleanField, RadioField, StringField, TextAreaField
from wtforms.validators import InputRequired

from CTFd.forms import BaseForm
from CTFd.forms.fields import SubmitField


class NotificationForm(BaseForm):
    title = StringField("标题", description="通知标题")
    content = TextAreaField(
        "内容",
        description="通知内容。 可以由 HTML 和/或 Markdown 组成。",
    )
    type = RadioField(
        "通知类型",
        choices=[("toast", "Toast"), ("alert", "警告"), ("background", "后台")],
        default="toast",
        description="通知的类型",
        validators=[InputRequired()],
    )
    sound = BooleanField(
        "播放声音",
        default=True,
        description="当用户收到通知时为用户播放声音",
    )
    submit = SubmitField("提交")
