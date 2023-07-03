from wtforms import BooleanField, FileField, SelectField, StringField, TextAreaField
from wtforms.fields.html5 import IntegerField, URLField
from wtforms.widgets.html5 import NumberInput

from CTFd.forms import BaseForm
from CTFd.forms.fields import SubmitField
from CTFd.utils.csv import get_dumpable_tables


class ResetInstanceForm(BaseForm):
    accounts = BooleanField(
        "账户",
        description="删除所有用户和团队帐户及其关联信息",
    )
    submissions = BooleanField(
        "提交记录",
        description="删除所有提交记录",
    )
    challenges = BooleanField(
        "题目", description="删除所有挑战和相关数据"
    )
    pages = BooleanField(
        "页面", description="删除所有页面及其关联文件"
    )
    notifications = BooleanField(
        "通知", description="删除所有通知"
    )
    submit = SubmitField("重置CTF")


class AccountSettingsForm(BaseForm):
    domain_whitelist = StringField(
        "账户邮箱白名单",
        description="用户可以注册的逗号分隔电子邮件域（例如 ctfd.io、gmail.com、yahoo.com）",
    )
    team_creation = SelectField(
        "团队创建",
        description="控制用户是否可以创建自己的团队（仅限团队模式）",
        choices=[("true", "允许"), ("false", "不允许")],
        default="true",
    )
    team_size = IntegerField(
        "队伍大小",
        widget=NumberInput(min=0),
        description="每个团队的用户数量（仅限团队模式）",
    )
    num_teams = IntegerField(
        "队伍总数",
        widget=NumberInput(min=0),
        description="最大团队数量（仅限团队模式）",
    )
    verify_emails = SelectField(
        "验证电子邮件",
        description="控制用户在参赛之前是否必须确认他们的电子邮件地址",
        choices=[("true", "启用"), ("false", "禁用")],
        default="false",
    )
    team_disbanding = SelectField(
        "团队解散",
        description="控制队长是否可以解散自己的队伍",
        choices=[
            ("inactive_only", "为不活跃的团队启用"),
            ("disabled", "禁用"),
        ],
        default="inactive_only",
    )
    name_changes = SelectField(
        "名称变更",
        description="控制用户和团队是否可以更改名称",
        choices=[("true", "允许"), ("false", "不允许")],
        default="true",
    )
    incorrect_submissions_per_min = IntegerField(
        "每分钟错误提交数",
        widget=NumberInput(min=1),
        description="防爆破，每分钟允许的提交数量（默认值：10）",
    )

    submit = SubmitField("更新")


class ExportCSVForm(BaseForm):
    table = SelectField("数据库表", choices=get_dumpable_tables())
    submit = SubmitField("下载csv")


class ImportCSVForm(BaseForm):
    csv_type = SelectField(
        "CSV类型",
        choices=[("users", "用户数据"), ("teams", "团队数据"), ("challenges", "题目数据")],
        description="CSV 数据类型",
    )
    csv_file = FileField("CSV文件", description="CSV 文件内容")


class LegalSettingsForm(BaseForm):
    tos_url = URLField(
        "服务条款网址",
        description="其他地方托管的服务条款文档的外部 URL",
    )
    tos_text = TextAreaField(
        "服务条款", description="服务条款页面上显示的文本",
    )
    privacy_url = URLField(
        "隐私政策网址",
        description="其他地方托管的隐私政策文档的外部 URL",
    )
    privacy_text = TextAreaField(
        "隐私政策", description="隐私政策页面上显示的文本",
    )
    submit = SubmitField("更新")
