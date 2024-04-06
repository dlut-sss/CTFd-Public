import time
import traceback

from flask import session
from sqlalchemy.sql import and_

from CTFd.models import Challenges, Users
from .db import DBUtils
from .docker import DockerUtils
from .extensions import log


class ControlUtil:
    @staticmethod
    def new_container(user_id, challenge_id):
        rq = DockerUtils.up_docker_compose(user_id=user_id, challenge_id=challenge_id)
        if isinstance(rq, tuple):
            DBUtils.new_container(user_id, challenge_id, flag=rq[2], port=rq[1], docker_id=rq[0], ip=rq[3])
            return True
        else:
            return rq

    @staticmethod
    def destroy_container(user_id):
        try:
            return DockerUtils.remove_current_docker_container(user_id)
        except Exception as e:
            log("owl",
                '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                )
            return False

    @staticmethod
    def expired_container(user_id):
        return DBUtils.renew_current_container(user_id=user_id)

    @staticmethod
    def get_container(user_id):
        return DBUtils.get_current_containers(user_id=user_id)

    @staticmethod
    def check_challenge(challenge_id, user_id):
        user = Users.query.filter_by(id=user_id).first()

        if user.type == "admin":
            Challenges.query.filter(
                Challenges.id == challenge_id
            ).first_or_404()
        else:
            Challenges.query.filter(
                Challenges.id == challenge_id,
                and_(Challenges.state != "hidden", Challenges.state != "locked"),
            ).first_or_404()

    @staticmethod
    def frequency_limit():
        if "limit" not in session:
            session["limit"] = int(time.time())
            return False

        if int(time.time()) - session["limit"] < 1:
            return True

        session["limit"] = int(time.time())
        return False
