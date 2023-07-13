"""
    @Author: ImYrS Yang
    @Date: 2023/3/31
    @Copyright: ImYrS Yang
    @Description: 
"""

from typing import Optional
import logging

import requests
from configobj import ConfigObj


class Pusher:

    def __init__(
            self,
            endpoint: str,
            user_id: str,
            access_token: Optional[str] = None,
    ):
        self.endpoint = endpoint
        self.user_id = user_id
        self.access_token = access_token

    def send(self, title: str, content: str) -> dict:
        """
        发送消息

        :param title: 通知标题
        :param content: 消息内容
        :return:
        """
        request = requests.get(
            self.endpoint + '/send_private_msg',
            params={
                'user_id': self.user_id,
                'message': f'{title}\n\n{content}',
                'access_token': self.access_token,
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
    if (
            not config['cqhttp_endpoint']
            or not config['cqhttp_user_id']
    ):
        logging.error('go-cqhttp 推送参数配置不完整')
        return False

    try:
        pusher = Pusher(config['cqhttp_endpoint'], config['cqhttp_user_id'], config['cqhttp_access_token'])
        pusher.send(title, content)
        logging.info('go-cqhttp 推送成功')
    except Exception as e:
        logging.error(f'go-cqhttp 推送失败, 错误信息: {e}')
        return False

    return True
