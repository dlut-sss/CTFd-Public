import traceback

import requests

from CTFd.utils import get_config
from .db import DBUtils
from ..models import DynamicCheckChallenge
from .extensions import log


class FrpUtils:
    @staticmethod
    def update_frp_redirect():

        containers = DBUtils.get_all_alive_container()
        # frps config
        output = get_config("owl:frpc_config_template")
        prefix = get_config("owl:docker_flag_prefix")

        http_template = "\n\n[http_%s]\n" + \
                        "type = http\n" + \
                        "local_ip = %s\n" + \
                        "local_port = %s\n" + \
                        "subdomain = %s\n" + \
                        "use_compression = true"

        direct_template = "\n\n[direct_%s_tcp]\n" + \
                          "type = tcp\n" + \
                          "local_ip = %s\n" + \
                          "local_port = %s\n" + \
                          "remote_port = %s\n" + \
                          "use_compression = true" + \
                          "\n\n[direct_%s_udp]\n" + \
                          "type = udp\n" + \
                          "local_ip = %s\n" + \
                          "local_port = %s\n" + \
                          "remote_port = %s\n" + \
                          "use_compression = true"

        for c in containers:
            dynamic_docker_challenge = DynamicCheckChallenge.query \
                .filter(DynamicCheckChallenge.id == c.challenge_id) \
                .first_or_404()
            redirect_port = dynamic_docker_challenge.redirect_port
            # 使用9999替换成随机端口，无需frp映射
            if redirect_port != 9999:
                container_service_local_ip = "{}_user{}_challenge{}-service-1".format(prefix, c.user_id,
                                                                                      c.challenge_id).lower()
                if dynamic_docker_challenge.redirect_type.upper() == 'HTTP':
                    output += http_template % (
                        container_service_local_ip
                        , container_service_local_ip
                        , redirect_port
                        , c.docker_id)
                else:
                    output += direct_template % (
                        container_service_local_ip
                        , container_service_local_ip
                        , redirect_port
                        , c.port
                        , container_service_local_ip
                        , container_service_local_ip
                        , redirect_port
                        , c.port)

        frp_api = get_config("owl:frpc_api_url", "http://compose-frpc:7400")
        try:
            if get_config("owl:frpc_config_template") is not None:
                response = requests.put(frp_api + "/api/config", output, timeout=5)
                if response.status_code != 200:
                    log("owl",
                        '[CTFd-owl] [{date}] frp设定配置出错: [{code}] {re}',
                        code=response.status_code, re=response.text, flush=True
                        )
                else:
                    response = requests.get(frp_api + "/api/reload", timeout=5)
                    if response.status_code != 200:
                        log("owl",
                            '[CTFd-owl] [{date}] frp配置重载出错: [{code}] {re}',
                            code=response.status_code, re=response.text, flush=True
                            )

        except Exception as e:
            log("owl",
                '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                )
            pass
