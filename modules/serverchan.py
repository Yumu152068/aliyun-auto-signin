import logging

import requests
from configobj import ConfigObj


class Pusher:
    def __init__(self, send_key):
        self.send_key = send_key

    def send(self, title: str, content: str) -> dict:
        """
        发送消息

        :param title: 通知标题
        :param content: 消息内容
        :return:
        """
        url = 'https://sc.ftqq.com/%s.send' % self.send_key

        request = requests.post(
            url,
            data={
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
    if not config['serverchan_send_key']:
        logging.error('ServerChan 推送参数配置不完整')
        return False

    try:
        pusher = Pusher(config['serverchan_send_key'])
        pusher.send(title, content)
        logging.info('ServerChan 推送成功')
    except Exception as e:
        logging.error(f'ServerChan 推送失败, 错误信息: {e}')
        return False

    return True
