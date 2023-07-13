"""
    @Author: ImYrS Yang
    @Date: 2023/3/16
    @Copyright: ImYrS Yang
    @Description: 
"""

import logging

import requests
from configobj import ConfigObj


class Pusher:
    def __init__(self, webhook: str):
        self.webhook = webhook

    def send(self, title: str, content: str) -> dict:
        """
        发送消息

        :param title: 通知标题
        :param content: 消息内容
        :return:
        """
        request = requests.post(
            self.webhook,
            json={
                'msg_type': 'post',
                'content': {
                    'post': {
                        'zh_cn': {
                            'title': title,
                            'content': [
                                [{
                                    'tag': 'text',
                                    'text': content
                                }]
                            ]
                        },
                    }
                }
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
    if not config['feishu_webhook']:
        logging.error('飞书 推送参数配置不完整')
        return False

    try:
        pusher = Pusher(config['feishu_webhook'])
        pusher.send(title, content)
        logging.info('飞书 推送成功')
    except Exception as e:
        logging.error(f'飞书 推送失败, 错误信息: {e}')
        return False

    return True
