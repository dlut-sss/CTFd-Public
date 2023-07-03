from wtforms import (
    BooleanField,
    HiddenField,
    MultipleFileField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import InputRequired

from CTFd.forms import BaseForm


class PageEditForm(BaseForm):
    title = StringField(
        "标题", description="这是导航栏上显示的标题"
    )
    route = StringField(
        "路由",
        description="这是您的页面所在的 URL 路由（例如 /page）。 您还可以输入链接到该页面的链接。",
    )
    draft = BooleanField("草稿")
    hidden = BooleanField("是否隐藏")
    auth_required = BooleanField("仅认证后")
    content = TextAreaField("内容")
    format = SelectField(
        "Format",
        choices=[("markdown", "Markdown"), ("html", "HTML")],
        default="markdown",
        validators=[InputRequired()],
        description="用于呈现页面的标记格式",
    )


class PageFilesUploadForm(BaseForm):
    file = MultipleFileField(
        "上传文件",
        description="使用 Control+单击或 Cmd+单击附加多个文件。",
        validators=[InputRequired()],
    )
    type = HiddenField("Page Type", default="page", validators=[InputRequired()])
