"""
    @Author: ImYrS Yang
    @Date: 2023/2/27
    @Copyright: ImYrS Yang
    @Description: 
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

from configobj import ConfigObj


class Pusher:

    def __init__(
            self,
            host: str,
            port: int,
            tls: bool,
            user: str,
            password: str,
            sender: str,
            receiver: str,
    ):
        self.host = host
        self.port = port
        self.tls = tls
        self.user = user
        self.password = password
        self.sender = sender
        self.receiver = receiver

    def send(self, title: str, content: str) -> None:
        """
        发送消息

        :param title: 通知标题
        :param content: 消息内容
        :return:
        """
        smtp = smtplib.SMTP(self.host, self.port)
        smtp.ehlo()

        if self.tls:
            smtp.starttls()

        smtp.login(self.user, self.password)

        message = MIMEText(content, 'plain', 'utf-8')
        message['From'] = formataddr((str(Header('AliyunDrive Auto Signin', 'utf-8')), self.sender))
        message['To'] = self.receiver
        message['Subject'] = title

        smtp.sendmail(self.sender, [self.receiver], message.as_string())


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
            not config['smtp_host']
            or not config['smtp_port']
            or not config['smtp_tls']
            or not config['smtp_user']
            or not config['smtp_password']
            or not config['smtp_sender']
            or not config['smtp_receiver']
    ):
        logging.error('SMTP 推送参数配置不完整')
        return False

    try:
        pusher = Pusher(
            host=config['smtp_host'],
            port=config['smtp_port'],
            tls=config['smtp_tls'],
            user=config['smtp_user'],
            password=config['smtp_password'],
            sender=config['smtp_sender'],
            receiver=config['smtp_receiver'],
        )
        pusher.send(title, content)
        logging.info('SMTP 推送成功')
    except Exception as e:
        logging.error(f'SMTP 推送失败, 错误信息: {e}')
        return False

    return True
