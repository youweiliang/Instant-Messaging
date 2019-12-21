# -*- coding: utf-8 -*-
import pickle
from cryptography.fernet import Fernet
# key = Fernet.generate_key()
with open('key.pkl', 'rb') as file:
    key = pickle.load(file)
cipher_suite = Fernet(key)


def encrypt(data):
    byte = bytes(data, 'gbk')
    encrypted_data = cipher_suite.encrypt(byte)
    return encrypted_data

def encrypt_byte(data):
    encrypted_data = cipher_suite.encrypt(data)
    return encrypted_data

def decrypt(data):
    return cipher_suite.decrypt(data)


def multi_encrypt(multiple_data):
    return [encrypt(d) for d in multiple_data]


def multi_decrypt(multiple_data):
    return [decrypt(d) for d in multiple_data]
