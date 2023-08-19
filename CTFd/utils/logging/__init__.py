import logging
import logging.handlers

from flask import session

from CTFd.utils import current_backend_time
from CTFd.utils.user import get_ip


def log(logger, format, **kwargs):
    logger = logging.getLogger(logger)
    props = {
        "id": session.get("id"),
        "date": current_backend_time().strftime("%Y/%m/%d %X"),
        "ip": get_ip(),
    }
    props.update(kwargs)
    msg = format.format(**props)
    logger.info(msg)
