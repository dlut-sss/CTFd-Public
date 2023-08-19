import functools
import time
from flask import request, current_app, session
from flask_restx import abort
from sqlalchemy.sql import and_

from CTFd.models import Challenges
from CTFd.utils.user import is_admin, get_current_user
from .utils.cache import CacheProvider


def challenge_visible(func):
    @functools.wraps(func)
    def _challenge_visible(*args, **kwargs):
        language = request.cookies.get("Scr1wCTFdLanguage", "zh")
        challenge_id = request.args.get('challenge_id')
        if is_admin():
            if not Challenges.query.filter(
                Challenges.id == challenge_id
            ).first():
                if language == "zh":
                    abort(404, '题目不存在', success=False)
                else:
                    abort(404, 'Challenge not exist', success=False)
        else:
            if not Challenges.query.filter(
                Challenges.id == challenge_id,
                and_(Challenges.state != "hidden", Challenges.state != "locked"),
            ).first():
                if language == "zh":
                    abort(403, '题目不可见', success=False)
                else:
                    abort(403, 'Challenge is hidden', success=False)
        return func(*args, **kwargs)

    return _challenge_visible


def frequency_limited(func):
    @functools.wraps(func)
    def _frequency_limited(*args, **kwargs):
        language = request.cookies.get("Scr1wCTFdLanguage", "zh")
        if is_admin():
            return func(*args, **kwargs)
        redis_util = CacheProvider(app=current_app, user_id=get_current_user().id)
        if not redis_util.acquire_lock():
            if language == "zh":
                abort(403, '请求速度过快！', success=False)
            else:
                abort(403, 'Request speed too fast!', success=False)
            # last request was unsuccessful. this is for protection.

        if "limit" not in session:
            session["limit"] = int(time.time())
        else:
            if int(time.time()) - session["limit"] < 60:
                if language == "zh":
                    abort(403, '达到请求频率限制，请等待1分钟后再试。', success=False)
                else:
                    abort(403, 'Reach request frequency limit, please wait for 1 minute and try again.', success=False)
        session["limit"] = int(time.time())

        result = func(*args, **kwargs)
        redis_util.release_lock()  # if any exception is raised, lock will not be released
        return result

    return _frequency_limited
