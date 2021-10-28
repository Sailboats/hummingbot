from datetime import datetime
import time
import hashlib
import hmac
from typing import Optional
from typing import (
    Any,
    Dict
)
from collections import OrderedDict
import logging
from hummingbot.logger import HummingbotLogger


class BitglobalAuth:
    _bitglobalau_logger: Optional[HummingbotLogger] = None

    @classmethod
    def logger(cls) -> HummingbotLogger:
        if cls._bitglobalau_logger is None:
            cls._bitglobalau_logger = logging.getLogger(__name__)
        return cls._bitglobalau_logger

    def __init__(self, api_key: str, secret_key: str, passphrase: Optional[str] = None):
        self.logger().debug(f'__init__: api_key = {api_key}, secret_key = {secret_key}')
        self.api_key: str = api_key
        self.secret_key: str = secret_key
        # self.passphrase: str = passphrase

    @staticmethod
    def keysort(dictionary: Dict[str, str]) -> Dict[str, str]:
        return OrderedDict(sorted(dictionary.items(), key=lambda t: t[0]))

    @staticmethod
    def get_timestamp() -> str:
        miliseconds = int(time.time() * 1000)
        utc = datetime.utcfromtimestamp(miliseconds // 1000)
        return utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-6] + "{:03d}".format(int(miliseconds) % 1000) + 'Z'

    def get_signature(self, path, time_stamp, api_key) -> str:
        return self.get_sign(path + time_stamp + api_key, self.secret_key)

    def get_sign(self, data, key) -> str:
        sign = hmac.new(key.encode(), data.encode(), hashlib.sha256)
        # print(sign.hexdigest())
        return sign.hexdigest()

    def add_auth_to_params(self,
                           method: str,
                           path_url: str,
                           args: Dict[str, Any] = {}) -> Dict[str, Any]:
        uppercase_method = method.upper()

        timestamp = self.get_timestamp()

        request = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": self.get_signature(timestamp, uppercase_method, path_url, args),
            "OK-ACCESS-TIMESTAMP": timestamp,
            # "OK-ACCESS-PASSPHRASE": self.passphrase,
        }

        sorted_request = self.keysort(request)

        return sorted_request

    def generate_rest_auth(self, data: Dict[str, str]) -> str:
        self.logger().debug(f'generate_rest_auth: data = {data}')
        data = list(data.items())
        data.sort()
        msg = '&'.join(['%s=%s' % (k, v) for k, v in data])
        # return digest(self.secret_key, msg.encode('utf-8'), 'sha256').hex()
        # is_first : bool = True
        # paramString = ""
        # if data:
        #     for key in sorted(data):
        #         if is_first:
        #             is_first = False
        #         else:
        #             paramString += "&"
        #         paramString += key
        #         paramString += "="
        #         paramString += str(data[key])
        self.logger().debug(f"generate_rest_auth: msg = {msg}")
        return self.get_sign(msg, self.secret_key)

    def generate_ws_auth(self):
        self.logger().debug('generate_ws_auth:')
        timestamp = str(int(time.time()))

        return {
            "cmd": "authKey",
            "args": [
                self.api_key,
                timestamp,
                self.get_signature(path="/message/realtime", time_stamp=timestamp, api_key=self.api_key)
            ]
        }
