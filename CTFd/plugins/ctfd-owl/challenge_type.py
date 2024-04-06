from flask import Blueprint

from CTFd.models import (
    db,
    Flags,
)
from CTFd.plugins.challenges import BaseChallenge
from CTFd.plugins.dynamic_challenges import DynamicValueChallenge
from CTFd.plugins.flags import get_flag_class
from CTFd.utils import user as current_user
from .models import DynamicCheckChallenge, OwlContainers


class DynamicCheckValueChallenge(BaseChallenge):
    id = "dynamic_docker_compose"
    name = "dynamic_docker_compose"
    blueprint = Blueprint(
        "ctfd-owl-challenge",
        __name__,
        template_folder="templates",
        static_folder="assets",
        url_prefix="/plugins/ctfd-owl"
    )
    challenge_model = DynamicCheckChallenge

    @classmethod
    def read(cls, challenge):
        challenge = DynamicCheckChallenge.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "initial": challenge.initial,
            "decay": challenge.decay,
            "minimum": challenge.minimum,
            "description": challenge.description,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }
        return data

    @classmethod
    def update(cls, challenge, request):
        data = request.form or request.get_json()

        for attr, value in data.items():
            if attr in ("initial", "minimum", "decay"):
                value = float(value)
            setattr(challenge, attr, value)

        challenge.value = challenge.initial
        db.session.commit()

        if challenge.dynamic_score == 1:
            return DynamicValueChallenge.calculate_value(challenge)

        db.session.commit()
        return challenge

    @classmethod
    def delete(cls, challenge):
        OwlContainers.query.filter_by(id=challenge.id).delete()
        DynamicCheckChallenge.query.filter_by(id=challenge.id).delete()
        super().delete(challenge)

    @classmethod
    def attempt(cls, challenge, request):
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        language = "zh"
        try:
            language = request.cookies.get("Scr1wCTFdLanguage", "zh")
        except:
            pass
        flags = Flags.query.filter_by(challenge_id=challenge.id).all()

        if len(flags) > 0:
            for flag in flags:
                if get_flag_class(flag.type).compare(flag, submission):
                    if language == "zh":
                        return True, "Bingo！答对啦！"
                    else:
                        return True, "Correct!"
            if language == "zh":
                return False, "答案不对喵！"
            else:
                return False, "Incorrect!"
        else:
            user_id = current_user.get_current_user().id
            q = db.session.query(OwlContainers)
            q = q.filter(OwlContainers.user_id == user_id)
            q = q.filter(OwlContainers.challenge_id == challenge.id)
            records = q.all()
            if len(records) == 0:
                if language == "zh":
                    return False, "请在容器处于开启状态时提交答案"
                else:
                    return False, "Please solve it during the container is running"

            container = records[0]
            if container.flag == submission:
                if language == "zh":
                    return True, "Bingo！答对啦！"
                else:
                    return True, "Correct!"
            if language == "zh":
                return False, "答案不对喵！"
            else:
                return False, "Incorrect!"

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)

        if challenge.dynamic_score == 1:
            DynamicValueChallenge.calculate_value(challenge)

        db.session.commit()
