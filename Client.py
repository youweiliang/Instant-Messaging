# -*- coding: utf-8 -*-

import time
import socket
import rsa
import pickle
import threading
import os
from cryptography.fernet import Fernet
from send_voice import send_voice
from recv_voice import receive_voice
from file_transfer import send_file, recv_file
from multiprocessing import Process
from PyQt5.QtWidgets import *

header_length = 4
SERVER_IP = 'localhost' # '172.16.34.231'
SERVER_PORT = 11111

online_status = {}
user_address = {}
file_ip = []


def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    free_port = s.getsockname()[1]
    s.close()
    return free_port


class Client():

    def __init__(self):
        self.buffer = b''
        self.create_conn(SERVER_IP, SERVER_PORT)
        self.send_key()
        self.recv_key()
        self.user_id = ''

    def send_permission(self, to_user_id, message):
        s = ' '.join(('permission', message, self.user_id, to_user_id))
        data = bytes(s, 'gbk')
        self.send(data)

    def ask_for_telecon(self, participants):
        people = ' '.join(participants)
        data = bytes("telecon? " + people, 'gbk')
        self.send(data)

    def telecon(self, text, original_data):
        if text.startswith('telecon not_online'):
            user_a = text.split(' ')[-1]
            QMessageBox.information(self, '提示信息', user_a+'退出多方通话！')
            return

        if text.startswith('telecon not_allow'):
            """显示用户a不同意参加，关闭多方通话"""
            user_a = text.split(' ')[-1]
            QMessageBox.information(self, '提示信息', user_a+'不同意参加！')
            return

        if text.startswith('telecon?'):
            """问用户是否同意参加多方通话，显示参与者"""
            participants = text.split(' ')[1:]
            num = len(participants)
            reply = QMessageBox.information(self,"多方通话申请",  "多方通话参与者："+participants,  
                     QMessageBox.Yes | QMessageBox.No)

            if reply:
                ports = []
                for i in range(num):
                    if self.user_id == participants[i]:
                        ports.append('0')
                    else:
                        available_port = get_free_port()
                        ports.append(str(available_port))
                self.free_ports = ports
                data = bytes("telecon OK " + ' '.join(ports), 'gbk')
            else:
                data = bytes("telecon NO", 'gbk')
            self.send(data)

        elif text.startswith('telecon ready'):
            """提示多方通话现在开始"""
            address = text.split(' ')[2:]
            process = []
            for port in self.free_ports:
                if port == '0':
                    continue
                v = Process(target=receive_voice, args=(int(port),))
                v.start()
                process.append(v)

            num = int(len(address) / 2)
            addr = []
            for i in range(num):
                (ip, port) = address[2 * i], int(address[2 * i + 1])
                if port == 0:  # do not add my own port
                    continue
                addr.append((ip, port))
            print(addr)
            s = Process(target=send_voice, args=(addr, ))
            s.start()
            """这里显示一个结束语音通话按钮，
            如果用户没按下结束按钮，就阻塞住，不继续执行下面的代码
            """
            self.Communicate.setText('取消多方')
            self.Communicate.clicked.connect()

            time.sleep(60)
            for v in process:
                v.terminate()
            s.terminate()

    def save_message(self,text,sender,my_id):

        data = "<p style=\"color: green;\">%s</p>" % text

        file_name = my_id+sender + '-message.pkl'
        # if os.path.exists(file_name):
        #     with open(file_name, 'rb') as f:
        #         m = pickle.load(f)
        #         m += data
        # else:
        #     m = data
        m = []
        try:
            if os.path.getsize(file_name) > 0:
                with open(file_name, 'rb') as f:
                    m = pickle.load(f)
                    m.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                    m.append(data)
            else:
                m.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                m.append(data)
        except:
            m.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            m.append(data)

        with open(file_name, 'wb') as f:
            pickle.dump(m, f, -1)

    def save_mess(self,text,sender,user_id):
        data = "<p style=\"color: blue;\">%s</p>" % text

        file_name = user_id+sender + '-message.pkl'
        m = []

        try:
            if os.path.getsize(file_name) > 0:
                with open(file_name, 'rb') as f:
                    m = pickle.load(f)
                    m.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                    m.append(data)
            else:
                m.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                m.append(data)
        except:
            m.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            m.append(data)
        with open(file_name, 'wb') as f:
            pickle.dump(m, f, -1)
            
    def get_message(self, user_id):
        file_name = user_id + '-message.pkl'
        with open(file_name, 'rb') as f:
            m = pickle.load(f)

    """-------以下不需要图形界面-------"""

    def create_conn(self, ip, port):
        # 连接服务器
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # conn.bind()
            conn.connect((ip, port))
            self.conn = conn
        except Exception as e:
            print("连接失败！", e)

    def send_key(self):
        (pubkey, private_key) = rsa.newkeys(2048)
        pubkey_bytes = pickle.dumps(pubkey)
        self.conn.sendall(pubkey_bytes)
        self.private_key = private_key

    def recv_key(self):
        sym_key = self.conn.recv(2048)
        key = rsa.decrypt(sym_key, self.private_key)
        self.cipher_suite = Fernet(key)

    def send(self, data):
        """所有消息都经过加密后再发送"""
        secret_message = self.cipher_suite.encrypt(data)
        packet_length = len(secret_message)
        if packet_length > 9999:  # 因为包头长度是固定的4字节，4字节对应的最大数字是9999
            print('packet too long')
            return

        s = str(packet_length)
        # 在包头长度之前填充0，凑够4字节，例如将'23'凑成'0023'
        header = '0' * (header_length - len(s)) + s
        # 为了方便起见，包头不加密
        self.conn.sendall(bytes(header, 'gbk') + secret_message)

    def check_user_status(self, user_id):
        self.online_query(user_id)
        t = time.time()
        while time.time() - t < 15:
            if online_status[user_id] == 1:
                # ip, port = user_address[user_id]
                return 'online'
            elif online_status[user_id] == 0:
                return 'not_online'
            else:
                time.sleep(1)
        if online_status[user_id] == -1:
            return 'no_responce'

    def online_query(self, user_id):
        """客户端要查询user是否online"""
        online_status[user_id] = -1
        s = "online_query {j}".format(j=user_id)
        data = bytes(s, 'gbk')
        self.send(data)


    def handle_online_responce(self,text):
        s = text.split(' ')
        if s[2] == '1':
            user_address[s[1]] = (s[-2], int(s[-1]))
            online_status[s[1]] = 1
        else:
            online_status[s[1]] = 0

    def login(self, user_id, password):
        data = bytes("login {i} {j}".format(i=user_id, j=password), 'gbk')
        self.send(data)

    def logout(self):
        s = "logout {j}".format(j=self.user_id)
        data = bytes(s, 'gbk')
        self.send(data)

    def register(self, user_id, password, username):
        data = bytes("register {} {} {}".format(
            user_id, password, username), 'gbk')
        self.user_id = user_id
        self.send(data)

    def send_message(self, message, to_user):
        s = "text_messaging {i} {j} {k}".format(
            i=self.user_id, j=to_user, k=message)
        data = bytes(s, 'gbk')
        self.send(data)

    def recv(self):
        """完整地读取一次客户端发来的数据，正确处理TCP粘包和拆包的问题"""
        buffer = self.buffer
        while len(buffer) < header_length:
            buffer += self.conn.recv(2048)
        packet_len = int(buffer[:header_length].decode('gbk'))
        while len(buffer) < packet_len:
            buffer += self.conn.recv(2048)
        self.buffer = buffer[packet_len + header_length:]

        # 用对称密钥解密接收到的数据
        message = self.cipher_suite.decrypt(
            buffer[header_length:packet_len + header_length])
        original_data = message
        text = message.decode('gbk')
        # 返回值text是字符串，original_data是原始的二进制数据bytes
        return text, original_data
