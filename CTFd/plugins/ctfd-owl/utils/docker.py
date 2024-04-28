import os
import random
import subprocess
import traceback
import uuid

from CTFd.models import Flags
from CTFd.utils import get_config
from .db import DBUtils
from .extensions import log
from ..models import DynamicCheckChallenge, OwlContainers


class DockerUtils:
    @staticmethod
    def gen_flag():
        prefix = get_config("owl:docker_flag_prefix")
        flag = "{" + str(uuid.uuid4()) + "}"
        flag = prefix + flag
        while OwlContainers.query.filter_by(flag=flag).first() is not None:
            flag = prefix + "{" + str(uuid.uuid4()) + "}"
        return flag

    @staticmethod
    def get_socket():
        socket = get_config("owl:docker_api_url")
        return socket

    @staticmethod
    def up_docker_compose(user_id, challenge_id):
        try:
            # 判断Flag类型并生成
            flag = DockerUtils.gen_flag()
            flags = Flags.query.filter_by(challenge_id=challenge_id).all()
            if len(flags) > 0:
                flag = flags[0].content

            # 确定源文件和目标目录
            challenge = DynamicCheckChallenge.query.filter_by(id=challenge_id).first_or_404()
            parent_dir = os.path.dirname(os.path.dirname(__file__))
            sname = os.path.join(parent_dir, "source/" + challenge.dirname)  # 源文件目录
            prefix = get_config("owl:docker_flag_prefix")
            name = "{}_user{}_challenge{}".format(prefix, user_id, challenge_id).lower()
            problem_docker_run_dir = get_config('owl:docker_run_folder', '/tmp')
            dname = os.path.join(problem_docker_run_dir, name)  # 目标文件目录

            # 确定可用端口
            min_port, max_port = int(get_config("owl:frp_direct_port_minimum")), int(
                get_config("owl:frp_direct_port_maximum"))
            all_container = DBUtils.get_all_container()
            port, ports_list = random.randint(min_port, max_port), [_.port for _ in all_container]
            while port in ports_list:
                port = random.randint(min_port, max_port)

            # 清空目标目录并复制源文件
            command = "rm -rf {}".format(dname)
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            command = "cp -r {} {}".format(sname, dname)
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 进入目标缓存目录替换9999端口为生成的随机端口并将FLAG写入env文件
            command = "cd {} && echo 'FLAG={}' > .env && sed 's/9999/{}/g' docker-compose.yml > run.yml".format(
                dname,
                flag,
                port)
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 进入目标目录并启动
            socket = DockerUtils.get_socket()
            command = "cd " + dname + " && docker -H={} compose -f run.yml up -d".format(socket)
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            log(
                "owl",
                '[CTFd-owl] [{date}] {msg}',
                msg=name + "启动完成。"
            )
            docker_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, name)).replace("-", "")
            return (docker_id, port, flag, challenge.redirect_type)
        except subprocess.CalledProcessError as e:
            log("owl",
                '[CTFd-owl] [{date}] Error: {e}\n{stdout}\n{stderr}\n{trace}',
                e=e, stdout=str(e.stdout), stderr=str(e.stderr),
                trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                )
            try:
                DockerUtils.down_docker_compose(user_id, challenge_id)
            except:
                pass
            raise e
        except Exception as e:
            log("owl",
                '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                )
            try:
                DockerUtils.down_docker_compose(user_id, challenge_id)
            except:
                pass
            raise e

    @staticmethod
    def down_docker_compose(user_id, challenge_id):
        try:
            # 生成目标目录信息
            prefix = get_config("owl:docker_flag_prefix")
            name = "{}_user{}_challenge{}".format(prefix, user_id, challenge_id).lower()
            problem_docker_run_dir = get_config('owl:docker_run_folder', '/tmp')
            dname = os.path.join(problem_docker_run_dir, name)

            # 关闭实例
            socket = DockerUtils.get_socket()
            command = "cd {} && docker -H={} compose -f run.yml down".format(dname, socket)
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 清空缓存目录
            command = "rm -rf {}".format(dname)
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            log(
                "owl",
                "[CTFd-owl] [{date}] {msg}",
                msg=name + "关闭完成。",
            )
            return True
        except subprocess.CalledProcessError as e:
            log("owl",
                '[CTFd-owl] [{date}] Error: {e}\n{stdout}\n{stderr}\n{trace}',
                e=e, stdout=str(e.stdout), stderr=str(e.stderr),
                trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                )
            raise e
        except Exception as e:
            log("owl",
                '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                )
            raise e

    @staticmethod
    def remove_current_docker_container(user_id):
        container = DBUtils.get_current_containers(user_id=user_id)

        if container is None:
            return False
        try:
            DockerUtils.down_docker_compose(user_id, challenge_id=container.challenge_id)
            DBUtils.remove_current_container(user_id)
            return True
        except Exception as e:
            log("owl",
                '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                )
            return False
