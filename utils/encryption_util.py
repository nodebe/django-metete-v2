import hashlib
from base64 import b64decode, b64encode
from decimal import Decimal

from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from django.db.models import QuerySet


class AESCipher:
    """
    Usage:
        c = AESCipher('password').encrypt('message')
        m = AESCipher('password').decrypt(c)
    Tested under Python 3 and PyCrypto 2.6.1.
    """

    def __init__(self, key, vector):
        self.key = bytes(key, 'ascii')
        self.vector = bytes(vector, 'ascii')

    def encrypt(self, raw):
        if raw == "" or raw is None:
            return raw
        raw = bytes(raw, 'utf8')
        cipher = AES.new(self.key, AES.MODE_CBC, iv=self.vector)
        return b64encode(cipher.encrypt(pad(raw, AES.block_size))).decode('utf8')

    def decrypt(self, enc):
        if enc == "" or enc is None or enc == "null" or enc == "None":
            return enc

        text = b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, self.vector)
        return unpad(cipher.decrypt(text), AES.block_size).decode('utf8')

    def encrypt_nested(self, ob):
        if isinstance(ob, dict):
            ret_obj = {}
            for k, v in ob.items():
                if isinstance(v, str) or isinstance(v, int) or isinstance(v, Decimal):
                    ret_obj[k] = self.encrypt(str(v))
                else:
                    ret_obj[k] = self.encrypt_nested(v)
        elif isinstance(ob, list) or isinstance(ob, QuerySet):
            ret_obj = []
            for v in ob:
                ret_obj.append(self.encrypt_nested(v))
        else:
            ret_obj = self.encrypt(str(ob))
        return ret_obj

    def decrypt_nested(self, ob):
        if isinstance(ob, dict):
            for k, v in ob.items():
                if isinstance(v, str):
                    value = self.decrypt(v)
                    if value == "true":
                        value = True
                    elif value == "false":
                        value = False
                    ob[k] = value
                else:
                    self.decrypt_nested(v)
        elif isinstance(ob, list):
            for ind, v in enumerate(ob):
                ob[ind] = self.decrypt_nested(v)
        else:
            ob = self.decrypt(str(ob))
        return ob

    def decrypt_body(self, body):
        try:
            body_copy = body.copy()
            return self.decrypt_nested(body_copy)
        except Exception as e:
            print("Decrypt Error: ", e)
            return None


def md5_str(data):
    md5_hash = hashlib.md5()
    md5_hash.update(data.encode('utf-8'))
    return str(md5_hash.hexdigest())
