from wtforms import TextAreaField
from wtforms.validators import InputRequired

from CTFd.forms import BaseForm
from CTFd.forms.fields import SubmitField


class SendEmailForm(BaseForm):
    text = TextAreaField("消息", validators=[InputRequired()])
    submit = SubmitField("发送")
