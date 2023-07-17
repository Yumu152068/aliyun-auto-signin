"""
    @Author: ImYrS Yang
    @Date: 2023/3/31
    @Copyright: ImYrS Yang
    @Description: 
"""

import logging

import requests
from configobj import ConfigObj


class Pusher:

    def __init__(self, url: str):
        self.url = url

    def send(
            self,
            title: str,
            content: str,
            content_html: str,
    ) -> dict:
        """
        发送消息

        :param title: 通知标题
        :param content: 消息内容
        :param content_html: 消息内容, HTML 格式
        :return:
        """
        request = requests.post(
            self.url,
            json={
                'title': title,
                'text': content,
                'html': content_html,
            },
            timeout=10,
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
    if not config['webhook_url']:
        logging.error('Webhook 推送参数配置不完整')
        return False

    try:
        pusher = Pusher(config['webhook_url'])
        pusher.send(title, content, content_html)
        logging.info('Webhook 推送成功')
    except Exception as e:
        logging.error(f'Webhook 推送失败, 错误信息: {e}')
        return False

    return True
