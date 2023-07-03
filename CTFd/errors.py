import jinja2.exceptions
from flask import render_template
from werkzeug.exceptions import InternalServerError


def render_error(error):
    if (
        isinstance(error, InternalServerError)
        and error.description == InternalServerError.description
    ):
        error.description = "发生了内部服务器错误"
    try:
        return (
            render_template(
                "errors/{}.html".format(error.code), error=error.description,
            ),
            error.code,
        )
    except jinja2.exceptions.TemplateNotFound:
        return error.get_response()
