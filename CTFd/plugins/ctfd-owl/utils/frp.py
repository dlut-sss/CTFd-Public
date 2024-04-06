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
            dirname = dynamic_docker_challenge.dirname.split("/")[1]
            redirect_port = dynamic_docker_challenge.redirect_port
            container_service_local_ip = "{}_user{}_{}_service_1".format(prefix, c.user_id,
                                                                         dirname).lower()  # nginx, etc
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
        # print(output)
        try:
            if get_config("owl:frpc_config_template") is not None:
                assert requests.put(frp_api + "/api/config", output,
                                    timeout=5).status_code == 200
                assert requests.get(frp_api + "/api/reload",
                                    timeout=5).status_code == 200
            else:
                pass
        except Exception as e:
            log("owl",
                '[CTFd-owl] [{date}] Error: {e}\n{trace}',
                e=e, trace=''.join(traceback.format_exception(type(e), e, e.__traceback__)), flush=True
                )
            pass
