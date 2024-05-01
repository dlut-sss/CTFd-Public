from CTFd.utils import set_config


def setup_default_configs():
    for key, val in {
        'setup': 'true',
        'docker_flag_prefix': 'flag',
        'docker_api_url': 'unix:///var/run/docker.sock',
        'docker_max_container_count': '100',
        'docker_max_renew_count': '5',
        'docker_timeout': '3600',
        'frp_http_domain_suffix': '127.0.0.1.xip.io',
        'frp_direct_ip_address': '127.0.0.1',
        'frp_direct_port_minimum': '10100',
        'frp_direct_port_maximum': '10200',
        'frpc_api_url': 'http://compose-frpc:7400',
        'docker_run_folder': '/home/owl',
    }.items():
        set_config('owl:' + key, val)
