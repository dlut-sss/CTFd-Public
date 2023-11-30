from wtforms import TextAreaField, StringField
from wtforms.validators import InputRequired

from CTFd.forms import BaseForm
from CTFd.forms.fields import SubmitField


class SendEmailForm(BaseForm):
    title = StringField("标题", validators=[InputRequired()])
    text = TextAreaField("消息", validators=[InputRequired()])
    submit = SubmitField("发送")
