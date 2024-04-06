import datetime

from CTFd.models import (
    db
)
from CTFd.utils import get_config
from ..models import OwlContainers


class DBUtils:

    @staticmethod
    def new_container(user_id, challenge_id, flag, docker_id, port=0, ip=""):
        container = OwlContainers(user_id=user_id, challenge_id=challenge_id, flag=flag, docker_id=docker_id, port=port,
                                  ip=ip)
        db.session.add(container)
        db.session.commit()
        db.session.close()
        return str(docker_id)

    @staticmethod
    def get_current_containers(user_id):
        q = db.session.query(OwlContainers)
        q = q.filter(OwlContainers.user_id == user_id)
        records = q.all()
        if len(records) == 0:
            return None

        return records[0]

    @staticmethod
    def get_container_by_port(port):
        q = db.session.query(OwlContainers)
        q = q.filter(OwlContainers.port == port)
        records = q.all()
        if len(records) == 0:
            return None

        return records[0]

    @staticmethod
    def remove_current_container(user_id):
        q = db.session.query(OwlContainers)
        q = q.filter(OwlContainers.user_id == user_id)
        # records = q.all()
        # for r in records:
        #     pass

        q.delete()
        db.session.commit()
        db.session.close()

    @staticmethod
    def renew_current_container(user_id):
        q = db.session.query(OwlContainers)
        q = q.filter(OwlContainers.user_id == user_id)
        # q = q.filter(OwlContainers.challenge_id == challenge_id)
        records = q.all()
        if len(records) == 0:
            return

        timeout = int(get_config("owl:docker_timeout", "3600"))

        r = records[0]
        r.start_time = r.start_time + datetime.timedelta(seconds=timeout)

        if r.start_time > datetime.datetime.utcnow():
            r.start_time = datetime.datetime.utcnow()

        r.renew_count += 1
        db.session.commit()
        db.session.close()

    @staticmethod
    def get_all_expired_container():
        timeout = int(get_config("owl:docker_timeout", "3600"))

        q = db.session.query(OwlContainers)
        q = q.filter(OwlContainers.start_time < datetime.datetime.utcnow() - datetime.timedelta(seconds=timeout))
        return q.all()

    @staticmethod
    def get_all_alive_container():
        timeout = int(get_config("owl:docker_timeout", "3600"))

        q = db.session.query(OwlContainers)
        q = q.filter(OwlContainers.start_time >= datetime.datetime.utcnow() - datetime.timedelta(seconds=timeout))
        return q.all()

    @staticmethod
    def get_all_container():
        q = db.session.query(OwlContainers)
        return q.all()

    @staticmethod
    def get_all_alive_container_page(page_start, page_end):
        timeout = int(get_config("owl:docker_timeout", "3600"))

        q = db.session.query(OwlContainers)
        q = q.filter(OwlContainers.start_time >= datetime.datetime.utcnow() - datetime.timedelta(seconds=timeout))
        q = q.slice(page_start, page_end)
        return q.all()

    @staticmethod
    def get_all_alive_container_count():
        timeout = int(get_config("owl:docker_timeout", "3600"))

        q = db.session.query(OwlContainers)
        q = q.filter(OwlContainers.start_time >= datetime.datetime.utcnow() - datetime.timedelta(seconds=timeout))
        return q.count()
