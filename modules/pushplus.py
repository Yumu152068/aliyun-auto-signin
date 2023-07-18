import logging

import requests
from configobj import ConfigObj


class Pusher:
    def __init__(
            self,
            token: str,
            topic: str
    ):
        self.token = token
        self.topic = topic

    def send(self, title: str, content: str) -> dict:
        """
        发送消息

        :param title: 通知标题
        :param content: 消息内容
        :return:
        """
        request =  requests.post(
            'http://www.pushplus.plus/send',
            json={
                'token': self.token,
                'title': title,
                'content': content,
                'topic': self.topic,
            }
        )

        request.raise_for_status()

        data = request.json()

        if data['code'] != 200:
            raise Exception(f'[{data["code"]}] {data["msg"]}')

        return request.json()


def push(
        config: ConfigObj | dict,
        content: str,
        content_html: str,
        title: str,
) -> bool:
    """
    签到消息推送

    :param config: 配置文件, ConfigObj 对象 | dict
    :param content: 推送内容
    :param content_html: 推送内容, HTML 格式
    :param title: 标题
    :return:
    """
    if not config['pushplus_token']:
        logging.error('PushPlus 推送参数配置不完整')
        return False

    try:
        pusher = Pusher(
            config['pushplus_token'],
            config['pushplus_topic'],
        )
        pusher.send(title, content)
        logging.info('PushPlus 推送成功')
    except Exception as e:
        logging.error(f'PushPlus 推送失败, 错误信息: {e}')
        return False

    return True
