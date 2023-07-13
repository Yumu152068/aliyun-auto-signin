from os import environ
from base64 import b64encode
import logging
from typing import NoReturn

import requests
from nacl import encoding, public


def encrypt(public_key, secret_value) -> str:
    """
    Encrypt a Unicode string using the public key.

    :param public_key: The public key to use for encryption.
    :param secret_value: The secret value to encrypt.
    :return: The encrypted secret value.
    """
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder)
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")


def get_pub_key(repos: str, token: str) -> tuple[str, int]:
    url = 'https://api.github.com/repos/{}/actions/secrets/public-key'.format(repos)
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer {}'.format(token),
        'X-GitHub-Api-Version': '2022-11-28'
    }

    r = requests.get(url, headers=headers)
    return r.json()['key'], r.json()['key_id']


def update_secret(name: str, value: str) -> NoReturn:
    """
    更新 secret

    :param name: secret 名称
    :param value: secret 值
    :return:
    """
    repos = environ['GITHUB_REPOS']
    token = environ['GP_TOKEN']

    if not token:
        raise ValueError('未配置 GP_TOKEN')

    key, key_id = get_pub_key(repos, token)

    url = 'https://api.github.com/repos/{}/actions/secrets/{}'.format(repos, name)
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer {}'.format(token),
        'X-GitHub-Api-Version': '2022-11-28'
    }
    payload = {
        'encrypted_value': encrypt(key, value),
        'key_id': key_id
    }

    requests.put(url, headers=headers, json=payload)
