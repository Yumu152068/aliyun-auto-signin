"""
    @Author: ImYrS Yang
    @Date: 2023/2/10
    @Copyright: ImYrS Yang
    @Description:
"""

import logging
from os import environ
from typing import NoReturn, Optional
import json
import argparse
import time

from configobj import ConfigObj
import requests

from modules import cqhttp, dingtalk, feishu, pushdeer, pushplus, serverchan, smtp, telegram, webhook
import github


class SignIn:
    """
    签到
    """

    def __init__(
            self,
            config: ConfigObj | dict,
            refresh_token: str,
            do_not_reward: Optional[bool] = False,
    ):
        """
        初始化

        :param config: 配置文件, ConfigObj 对象或字典
        :param refresh_token: refresh_token
        :param do_not_reward: 是否不领取奖励
        """
        self.config = config
        self.refresh_token = refresh_token
        self.hide_refresh_token = self.__hide_refresh_token()
        self.access_token = None
        self.new_refresh_token = None
        self.phone = None
        self.signin_count = 0
        self.signin_reward = None
        self.error = None
        self.do_not_reward = do_not_reward

    def __hide_refresh_token(self) -> str:
        """
        隐藏 refresh_token

        :return: 隐藏后的 refresh_token
        """
        try:
            return self.refresh_token[:4] + '*' * len(self.refresh_token[4:-4]) + self.refresh_token[-4:]
        except IndexError:
            return self.refresh_token

    def __get_access_token(self, retry: bool = False) -> bool:
        """
        获取 access_token

        :param retry: 是否重试
        :return: 是否成功
        """
        try:
            data = requests.post(
                'https://auth.aliyundrive.com/v2/account/token',
                json={
                    'grant_type': 'refresh_token',
                    'refresh_token': self.refresh_token,
                }
            ).json()
        except requests.RequestException as e:
            logging.error(f'[{self.hide_refresh_token}] 获取 access token 请求失败: {e}')
            if not retry:
                logging.info(f'[{self.hide_refresh_token}] 正在重试...')
                return self.__get_access_token(retry=True)

            self.error = e
            return False

        try:
            if data['code'] in [
                'RefreshTokenExpired', 'InvalidParameter.RefreshToken',
            ]:
                logging.error(f'[{self.hide_refresh_token}] 获取 access token 失败, 可能是 refresh token 无效.')
                self.error = data
                return False
        except KeyError:
            pass

        try:
            self.access_token = data['access_token']
            self.new_refresh_token = data['refresh_token']
            self.phone = data['user_name']
        except KeyError:
            logging.error(f'[{self.hide_refresh_token}] 获取 access token 失败, 参数缺失: {data}')
            self.error = f'获取 access token 失败, 参数缺失: {data}'
            return False

        return True

    def __sign_in(self, retry: bool = False) -> NoReturn:
        """
        签到函数

        :return:
        """
        try:
            data = requests.post(
                'https://member.aliyundrive.com/v1/activity/sign_in_list',
                params={'_rx-s': 'mobile'},
                headers={'Authorization': f'Bearer {self.access_token}'},
                json={'isReward': False},
            ).json()
            logging.debug(str(data))
        except requests.RequestException as e:
            logging.error(f'[{self.phone}] 签到请求失败: {e}')
            if not retry:
                logging.info(f'[{self.phone}] 正在重试...')
                return self.__sign_in(retry=True)

            self.error = e
            return

        if data['code'] == 'AccessTokenInvalid':
            logging.error(f'[{self.phone}] access token 无效, 正在重新获取...')
            if not retry:
                logging.info(f'[{self.phone}] 签到失败, 正在重试...')
                return self.__sign_in(retry=True)

        if 'success' not in data:
            logging.error(f'[{self.phone}] 签到失败, 错误信息: {data}')
            self.error = data
            return

        self.signin_count = data['result']['signInCount']

        if self.do_not_reward:
            if self.signin_count < len(data['result']['signInLogs']):
                logging.info(f'[{self.phone}] 已设置不领取奖励.')
                self.signin_reward = '跳过领取奖励'
                return

            self.__reward_all(len(data['result']['signInLogs']))
            return

        try:
            data = requests.post(
                'https://member.aliyundrive.com/v1/activity/sign_in_reward',
                params={'_rx-s': 'mobile'},
                headers={'Authorization': f'Bearer {self.access_token}'},
                json={'signInDay': self.signin_count},
            ).json()
            logging.debug(str(data))
        except requests.RequestException as e:
            logging.error(f'[{self.phone}] 兑换请求失败: {e}')
            if not retry:
                logging.info(f'[{self.phone}] 正在重试...')
                return self.__sign_in(retry=True)

        reward = (
            '无奖励'
            if not data['result']
            else f'获得 {data["result"]["name"]} {data["result"]["description"]}'
        )

        self.signin_reward = reward

        logging.info(f'[{self.phone}] 签到成功, 本月累计签到 {self.signin_count} 天.')
        logging.info(f'[{self.phone}] 本次签到{reward}')

    def __reward_all(self, max_day: int) -> NoReturn:
        """
        兑换当月全部奖励

        :param max_day: 最大天数
        :return:
        """
        url = 'https://member.aliyundrive.com/v1/activity/sign_in_reward'
        params = {'_rx-s': 'mobile'}
        headers = {'Authorization': f'Bearer {self.access_token}'}

        for day in range(1, max_day + 1):
            try:
                requests.post(
                    url,
                    params=params,
                    headers=headers,
                    json={'signInDay': day},
                )
            except requests.RequestException as e:
                logging.error(f'[{self.phone}] 签到请求失败: {e}')

        self.signin_reward = '已自动领取本月全部奖励'

    def __generate_result(self) -> dict:
        """
        获取签到结果

        :return: 签到结果
        """
        user = self.phone or self.hide_refresh_token
        text = (
            f'[{user}] 签到成功, 本月累计签到 {self.signin_count} 天.\n本次签到{self.signin_reward}'
            if not self.error
            else f'[{user}] 签到失败\n{json.dumps(str(self.error), indent=2, ensure_ascii=False)}'
        )

        text_html = (
            f'<code>{user}</code> 签到成功, 本月累计签到 {self.signin_count} 天.\n本次签到{self.signin_reward}'
            if not self.error
            else (
                f'<code>{user}</code> 签到失败\n'
                f'<code>{json.dumps(str(self.error), indent=2, ensure_ascii=False)}</code>'
            )
        )

        return {
            'success': True if self.signin_count else False,
            'user': self.phone or self.hide_refresh_token,
            'refresh_token': self.new_refresh_token or self.refresh_token,
            'count': self.signin_count,
            'reward': self.signin_reward,
            'text': text,
            'text_html': text_html,
        }

    def run(self) -> dict:
        """
        运行签到

        :return: 签到结果
        """
        result = self.__get_access_token()

        if result:
            time.sleep(3)
            self.__sign_in()

        return self.__generate_result()


def push(
        config: ConfigObj | dict,
        content: str,
        content_html: str,
        title: Optional[str] = None,
) -> NoReturn:
    """
    推送签到结果

    :param config: 配置文件, ConfigObj 对象或字典
    :param content: 推送内容
    :param content_html: 推送内容, HTML 格式
    :param title: 推送标题

    :return:
    """
    configured_push_types = [
        i.lower().strip()
        for i in (
            [config['push_types']]
            if type(config['push_types']) == str
            else config['push_types']
        )
    ]

    for push_type, pusher in {
        'go-cqhttp': cqhttp,
        'dingtalk': dingtalk,
        'feishu': feishu,
        'pushdeer': pushdeer,
        'pushplus': pushplus,
        'serverchan': serverchan,
        'smtp': smtp,
        'telegram': telegram,
        'webhook': webhook,
    }.items():
        if push_type in configured_push_types:
            pusher.push(config, content, content_html, title)


def init_logger(debug: Optional[bool] = False) -> NoReturn:
    """
    初始化日志系统

    :return:
    """
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log_format = logging.Formatter(
        '%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s: %(message)s'
    )

    # Console
    ch = logging.StreamHandler()
    log.setLevel(logging.DEBUG if debug else logging.INFO)
    ch.setFormatter(log_format)
    log.addHandler(ch)

    # Log file
    log_name = 'aliyun_auto_signin.log'
    fh = logging.FileHandler(log_name, mode='a', encoding='utf-8')
    log.setLevel(logging.DEBUG if debug else logging.INFO)
    fh.setFormatter(log_format)
    log.addHandler(fh)


def get_config_from_env() -> Optional[dict]:
    """
    从环境变量获取配置

    :return: 配置字典, 配置缺失返回 None
    """
    try:
        refresh_tokens = environ['REFRESH_TOKENS'] or ''
        push_types = environ['PUSH_TYPES'] or ''

        return {
            'refresh_tokens': refresh_tokens.split(','),
            'push_types': push_types.split(','),
            'serverchan_send_key': environ['SERVERCHAN_SEND_KEY'],
            'telegram_endpoint': 'https://api.telegram.org',
            'telegram_bot_token': environ['TELEGRAM_BOT_TOKEN'],
            'telegram_chat_id': environ['TELEGRAM_CHAT_ID'],
            'telegram_proxy': None,
            'pushplus_token': environ['PUSHPLUS_TOKEN'],
            'pushplus_topic': environ['PUSHPLUS_TOPIC'],
            'smtp_host': environ['SMTP_HOST'],
            'smtp_port': environ['SMTP_PORT'],
            'smtp_tls': environ['SMTP_TLS'],
            'smtp_user': environ['SMTP_USER'],
            'smtp_password': environ['SMTP_PASSWORD'],
            'smtp_sender': environ['SMTP_SENDER'],
            'smtp_receiver': environ['SMTP_RECEIVER'],
            'feishu_webhook': environ['FEISHU_WEBHOOK'],
            'webhook_url': environ['WEBHOOK_URL'],
            'cqhttp_endpoint': environ['CQHTTP_ENDPOINT'],
            'cqhttp_user_id': environ['CQHTTP_USER_ID'],
            'cqhttp_access_token': environ['CQHTTP_ACCESS_TOKEN'],
        }
    except KeyError as e:
        logging.error(f'环境变量 {e} 缺失.')
        return None


def get_args() -> argparse.Namespace:
    """
    获取命令行参数

    :return: 命令行参数
    """
    parser = argparse.ArgumentParser(description='阿里云盘自动签到 by @ImYrS')

    parser.add_argument('-a', '--action', help='由 GitHub Actions 调用', action='store_true', default=False)
    parser.add_argument('-d', '--debug', help='调试模式, 会输出更多调试数据', action='store_true', default=False)
    parser.add_argument('--do-not-reward', help='仅签到, 不进行奖励兑换', action='store_true', default=False)

    return parser.parse_args()


def main():
    """
    主函数

    :return:
    """
    environ['NO_PROXY'] = '*'  # 禁止代理

    args = get_args()

    init_logger(args.debug)  # 初始化日志系统

    # 获取配置
    config = (
        get_config_from_env()
        if args.action
        else ConfigObj('config.ini', encoding='UTF8')
    )

    if not config:
        logging.error('获取配置失败.')
        raise ValueError('获取配置失败.')

    # 获取所有 refresh token 指向用户
    users = (
        [config['refresh_tokens']]
        if type(config['refresh_tokens']) == str
        else config['refresh_tokens']
    )

    results = []
    do_not_reward = (
        environ['DO_NOT_REWARD'] == 'true'
        if args.action
        else
        args.do_not_reward
    )

    for user in users:
        signin = SignIn(
            config=config,
            refresh_token=user,
            do_not_reward=do_not_reward,
        )

        results.append(signin.run())

    # 合并推送
    text = '\n\n'.join([i['text'] for i in results])
    text_html = '\n\n'.join([i['text_html'] for i in results])

    if args.action and not environ['GP_TOKEN']:
        text += (
            '\n\n当前 Actions 尚未配置 GP_TOKEN, 请参考 '
            'https://imyrs.cn/posts/2023/auto-signin-aliyundrive-by-using-github-action/#github-personal-token'
            ' 尽快处理.'
        )
        text_html += (
            '\n\n当前 Actions 尚未配置 GP_TOKEN, 请参考 '
            'https://imyrs.cn/posts/2023/auto-signin-aliyundrive-by-using-github-action/#github-personal-token'
            ' 尽快处理.'
        )

    push(config, text, text_html, '阿里云盘签到')

    # 更新 refresh token
    new_users = [i['refresh_token'] for i in results]

    if not args.action:
        config['refresh_tokens'] = ','.join(new_users)
    else:
        try:
            github.update_secret('REFRESH_TOKENS', ','.join(new_users))
            logging.info('refresh tokens 更新成功.')
        except Exception as e:
            logging.error(f'更新 refresh tokens 失败: {e}')


if __name__ == '__main__':
    main()
