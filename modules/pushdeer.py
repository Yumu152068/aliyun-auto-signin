"""
    @Author: ImYrS Yang
    @Date: 2023/2/12
    @Copyright: ImYrS Yang
    @Description: 
"""

import logging

import requests
from configobj import ConfigObj


class Pusher:

    def __init__(self, endpoint: str, push_key: str):
        self.endpoint = endpoint
        self.push_key = push_key

    def send(self, title: str, content: str) -> dict:
        """
        发送消息

        :param title: 通知标题
        :param content: 消息内容
        :return:
        """
        request = requests.post(
            self.endpoint + '/message/push',
            json={
                'pushkey': self.push_key,
                'type': 'markdown',
                'text': title,
                'desp': content,
            }
        )

        request.raise_for_status()

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
    if (
            not config['pushdeer_endpoint']
            or not config['pushdeer_send_key']
    ):
        logging.error('PushDeer 推送参数配置不完整')
        return False

    try:
        pusher = Pusher(config['pushdeer_endpoint'], config['pushdeer_send_key'])
        pusher.send(title, content)
        logging.info('PushDeer 推送成功')
    except Exception as e:
        logging.error(f'PushDeer 推送失败, 错误信息: {e}')
        return False

    return True
