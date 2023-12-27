import datetime
import traceback

from flask import request

from CTFd.utils import get_config
from CTFd.utils.logging import log_simple as log
from .db import DBContainer, db
from .docker import DockerUtils
from .routers import Router


class ControlUtil:
    @staticmethod
    def try_add_container(user_id, challenge_id):
        language = "zh"
        try:
            language = request.cookies.get("Scr1wCTFdLanguage", "zh")
        except:
            pass
        container = DBContainer.create_container_record(user_id, challenge_id)
        try:
            log(
                "whale",
                "[{date}] [CTFd Whale] 用户{user_name}申请启动题目(ID:{chal_id})的实例容器{name}",
                user_name=container.user.name,
                chal_id=challenge_id,
                name=container.challenge.docker_image,
            )
            DockerUtils.add_container(container)
        except Exception as e:
            DBContainer.remove_container_record(user_id)
            traceback_str = ''.join(traceback.format_tb(e.__traceback__))
            log(
                "whale",
                "[{date}] [CTFd Whale] 用户{user_name}申请的题目(ID:{chal_id})的实例容器{name}启动失败。\n{tb}",
                user_name=container.user.name,
                chal_id=challenge_id,
                name=container.challenge.docker_image,
                tb=traceback_str,
            )
            if language == "zh":
                return False, 'Docker启动失败'
            else:
                return False, 'Docker launch failed'
        ok, msg = Router.register(container)
        if not ok:
            DockerUtils.remove_container(container)
            DBContainer.remove_container_record(user_id)
            log(
                "whale",
                "[{date}] [CTFd Whale] 用户{user_name}申请的题目(ID:{chal_id})的实例容器{name}启动失败。{tb}",
                user_name=container.user.name,
                chal_id=challenge_id,
                name=container.challenge.docker_image,
                tb=msg,
            )
            return False, msg
        log(
            "whale",
            "[{date}] [CTFd Whale] 用户{user_name}申请的题目(ID:{chal_id})的实例容器{name}启动成功",
            user_name=container.user.name,
            chal_id=challenge_id,
            name=container.challenge.docker_image,
        )
        if language == "zh":
            return True, 'Docker启动成功'
        else:
            return True, 'Docker launch success!'

    @staticmethod
    def try_remove_container(user_id):
        language = "zh"
        try:
            language = request.cookies.get("Scr1wCTFdLanguage", "zh")
        except:
            pass
        container = DBContainer.get_current_containers(user_id=user_id)
        if not container:
            if language == "zh":
                return False, '找不到请求的容器'
            else:
                return False, 'The requested container could not be found'
        log(
            "whale",
            "[{date}] [CTFd Whale] 用户{user_name}申请关闭实例容器{name}。",
            user_name=container.user.name,
            name=container.challenge.docker_image,
        )
        for _ in range(3):  # configurable? as "onerror_retry_cnt"
            try:
                ok, msg = Router.unregister(container)
                if not ok:
                    log(
                        "whale",
                        "[{date}] [CTFd Whale] 用户{user_name}申请的实例容器{name}关闭失败。{msg}",
                        user_name=container.user.name,
                        name=container.challenge.docker_image,
                        msg=msg,
                    )
                    return False, msg
                DockerUtils.remove_container(container)
                DBContainer.remove_container_record(user_id)
                log(
                    "whale",
                    "[{date}] [CTFd Whale] 用户{user_name}申请的实例容器{name}关闭成功。",
                    user_name=container.user.name,
                    name=container.challenge.docker_image,
                )
                if language == "zh":
                    return True, '容器关闭成功'
                else:
                    return True, 'Container closed successfully'
            except Exception as e:
                traceback_str = ''.join(traceback.format_tb(e.__traceback__))
                log(
                    "whale",
                    "[{date}] [CTFd Whale] 用户{user_name}申请的实例容器{name}关闭失败。\n{tb}",
                    user_name=container.user.name,
                    name=container.challenge.docker_image,
                    tb=traceback_str,
                )
                print(traceback.format_exc())
        if language == "zh":
            return False, '关闭容器时出错，请联系管理员'
        else:
            return False, 'Error shutting down container, please contact administrator'

    @staticmethod
    def try_renew_container(user_id):
        language = "zh"
        try:
            language = request.cookies.get("Scr1wCTFdLanguage", "zh")
        except:
            pass
        container = DBContainer.get_current_containers(user_id)
        if not container:
            if language == "zh":
                return False, '找不到请求的容器'
            else:
                return False, 'The requested container could not be found'
        log(
            "whale",
            "[{date}] [CTFd Whale] 用户{user_name}申请延期容器{name}。",
            user_name=container.user.name,
            name=container.challenge.docker_image,
        )
        timeout = int(get_config("whale:docker_timeout", "3600"))
        container.start_time = container.start_time + \
                               datetime.timedelta(seconds=timeout)
        if container.start_time > datetime.datetime.utcnow():
            container.start_time = datetime.datetime.utcnow()
            # race condition? useless maybe?
            # useful when docker_timeout < poll timeout (10 seconds)
            # doesn't make any sense
        else:
            log(
                "whale",
                "[{date}] [CTFd Whale] 用户{user_name}申请延期的容器{name}无效。",
                user_name=container.user.name,
                name=container.challenge.docker_image,
            )
            if language == "zh":
                return False, '无效的容器'
            else:
                return False, 'invalid container'
        container.renew_count += 1
        db.session.commit()
        log(
            "whale",
            "[{date}] [CTFd Whale] 用户{user_name}申请的容器{name}延期成功。总延期次数{count}次。",
            user_name=container.user.name,
            name=container.challenge.docker_image,
            count=container.renew_count,
        )
        if language == "zh":
            return True, '容器延时成功'
        else:
            return True, 'Container Renew Success'
