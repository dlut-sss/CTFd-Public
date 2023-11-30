from abc import ABC, abstractmethod
from lxml import etree
from requests.exceptions import RequestException
from urllib.parse import urlencode
import logging
import requests

logger = logging.getLogger('captcha')


class VerificationError(Exception):
    """当验证无法完成时引发，例如当提供者返回错误时。"""


class CaptchaProvider(ABC):
    @property
    @abstractmethod
    def verification_url(self):
        pass

    @property
    @abstractmethod
    def response_form_key(self):
        pass

    @classmethod
    def parse(cls, string):
        if string is None:
            raise ValueError('验证码提供商未指定。 选项包括“Google”和“hCpatcha”')

        if string.lower() in ['google', 'recaptcha', 're']:
            return ReCaptchaProvider
        if string.lower() in ['intuition machines', 'hcaptcha', 'h']:
            return HCaptchaProvider

        raise ValueError('{!r} 无法解析为验证码提供程序')

    @abstractmethod
    def script_tag(self):
        pass

    @abstractmethod
    def challenge_tag(self):
        pass

    def post_data(self, response, remote_ip=None):
        data = {
            'secret': self.secret,
            'response': response,
        }

        if self.verify_remote_ip:
            if remote_ip is None:
                logger.error("配置为验证远程 IP，但未提供远程 IP。")
                raise VerificationError()
            data['remoteip'] = remote_ip

        return data

    def verify(self, form, remote_ip=None):
        # 如果表单不包含验证码响应，则立即失败。
        if not form.get(self.response_form_key, None):
            return False

        # 向验证码提供者发出请求。
        post_data = self.post_data(form[self.response_form_key], remote_ip)
        logger.debug("正在向 {} 发送验证码验证请求 {}".format(post_data, self.verification_url))
        verify_reponse = requests.post(self.verification_url, data=post_data)

        # 如果HTTP请求失败，则bail。
        try:
            verify_reponse.raise_for_status()
        except RequestException as e:
            logger.error("验证码请求失败，代码为 {}}".format(verify_response.status_code))
            raise VerificationError() from e

        # 解析响应并检查错误代码。
        verify = verify_reponse.json()
        logger.debug("收到验证码验证响应：{}".format(verify))
        if verify.get('error-codes', None):
            logger.error("验证码服务返回错误代码 {}".format(verify['error-codes']))
            raise VerificationError()

        return verify['success']


class ReCaptchaProvider(CaptchaProvider):
    verification_url = 'https://www.recaptcha.net/recaptcha/api/siteverify'
    response_form_key = 'g-recaptcha-response'

    def __init__(self, site_key, secret, verify_remote_ip=False):
        self.site_key = site_key
        self.secret = secret
        self.verify_remote_ip = verify_remote_ip

    def script_tag(self):
        script_element = etree.Element(
            'script',
            attrib={
                'src': 'https://www.recaptcha.net/recaptcha/api.js',
                'async': 'true',
                'defer': 'true',
                'id': 'captchaScript'
            }
        )
        onerror_code = """
            console.log('验证码脚本加载失败');
            try{
                CTFd.ui.ezq.ezToast({
                    title: '出现错误',
                    body: '验证码脚本加载失败！'
                });
            }catch(e){
                alert('验证码脚本加载失败！请刷新页面后重试!')
            }
        """
        script_element.set('onerror', onerror_code)
        return script_element

    def challenge_tag(self):
        return etree.Element(
            'div',
            attrib={
                'class': 'g-recaptcha float-left',
                'data-sitekey': self.site_key,
            }
        )


class HCaptchaProvider(CaptchaProvider):
    verification_url = 'https://hcaptcha.com/siteverify'
    response_form_key = 'h-captcha-response'

    def __init__(self, site_key, secret, verify_remote_ip=False):
        self.site_key = site_key
        self.secret = secret
        self.verify_remote_ip = verify_remote_ip

    def script_tag(self):
        return etree.Element(
            'script',
            attrib={
                'src': 'https://hcaptcha.com/1/api.js',
                'async': 'true',
                'defer': 'true'
            }
        )

    def challenge_tag(self):
        return etree.Element(
            'div',
            attrib={
                'class': 'h-captcha float-left',
                'data-sitekey': self.site_key,
            }
        )

    def post_data(self, response, remote_ip=None):
        data = {
            'secret': self.secret,
            'sitekey': self.site_key,
            'response': response,
        }

        if self.verify_remote_ip:
            if remote_ip is None:
                logger.error("配置为验证远程 IP，但未提供远程 IP。")
                raise VerificationError()
            data['remoteip'] = remote_ip

        return data
