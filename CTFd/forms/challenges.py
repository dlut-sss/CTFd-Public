from wtforms import MultipleFileField, SelectField, StringField
from wtforms.validators import InputRequired

from CTFd.forms import BaseForm
from CTFd.forms.fields import SubmitField


class ChallengeSearchForm(BaseForm):
    field = SelectField(
        "Search Field",
        choices=[
            ("name", "名称"),
            ("id", "ID"),
            ("category", "类别"),
            ("subcategory", "子类别"),
            ("type", "类型"),
        ],
        default="name",
        validators=[InputRequired()],
    )
    q = StringField("Parameter", validators=[InputRequired()])
    submit = SubmitField("搜索")


class ChallengeFilesUploadForm(BaseForm):
    file = MultipleFileField(
        "上传文件",
        description="使用 Control+单击或 Cmd+单击附加多个文件。",
        validators=[InputRequired()],
    )
    submit = SubmitField("上传")
