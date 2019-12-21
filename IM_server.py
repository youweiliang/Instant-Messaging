# -*- coding: utf-8 -*-


import queue
import rsa
import time
import pickle
import threading
import socketserver
import socket
from encrypt import encrypt_byte, decrypt, multi_encrypt
from cryptography.fernet import Fernet
import mysql.connector

PWD = "111111"

login_db = mysql.connector.connect(host="localhost", user="root", passwd=PWD, database="login_data")
login_cursor = login_db.cursor()
message_db = mysql.connector.connect(host="localhost", user="root", passwd=PWD, database="message_data")
message_cursor = message_db.cursor()

# 生成密钥
(pubkey, private_key) = rsa.newkeys(1024)

SERVER_PORT = 11111
header_length = 4  # bytes
client_address = {}
client_socket = []
max_trial = 100
on_line_users = []
all_users = []
client_queue = {}
telecon_address = []
tele_people = []


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def setup(self):
        client_ip = self.client_address[0].strip()  # 获取客户端的ip
        if client_ip == '127.0.0.1':
            IPs = socket.gethostbyname_ex(socket.gethostname())[-1]
            local_ip = [i for i in IPs if i.startswith('192.168')]
            if len(local_ip) > 1:
                print(local_ip)
            client_ip = local_ip[-1]
        port = self.client_address[1]  # 获取客户端的port

        print(client_ip + ": " + str(port) + " is connect!")
        self.address = (client_ip, port)
        self.buffer = b''

    def handle(self):
        """处理客户端请求的主方法"""

        # 建立连接后客户端应该马上把它的公钥发送给服务器
        self.pubkey = self.recv_pubkey()  # 接收客户端的pubkey

        key = Fernet.generate_key()  # 生成对称加密的密钥
        sym_key = rsa.encrypt(key, self.pubkey)  # 用rsa加密该密钥后发送给客户端
        self.request.sendall(sym_key)  # 客户端收到密钥后用该密钥加密/解密消息
        self.cipher_suite = Fernet(key)  # 生成加密工具，用该工具进行加密/解密

        if not self.authentication():  # 判断客户端是要登录还是要创建账号
            self.request.close()  # 不成功，关闭连接
            return

        # 成功登录或注册

        self.send_user_list()

        on_line_users.append(self.user_id)
        client_address[self.user_id] = self.address
        self.check_unsent_message()  # 检查离线的这段时间内是否有发送给自己的消息
        self.q = queue.Queue()
        client_queue[self.user_id] = self.q
        t = threading.Thread(target=self.check_queue)
        t.start()

        # 进入循环，不断处理客户端发来的请求
        while True:
            text, original_data = self.recv()
            # 确定客户端这一次要求执行的操作是什么，并执行相应的操作
            if text.startswith('text_messaging'):
                self.text_messaging(text, original_data)
            elif text.startswith('online_query'):
                self.online_responce(text)
            elif text.startswith('permission'):
                self.handle_permission(text, original_data)
            elif text.startswith('telecon'):
                self.telecon(text, original_data)
            elif text.startswith('logout'):
                self.logout()
                break

    def finish(self):
        try:
            if self.user_id in on_line_users:
                on_line_users.remove(self.user_id)
        except:
            pass
        print("client is disconnect!")

    def send_user_list(self):
        login_cursor.execute("SELECT user_id FROM user")
        result = login_cursor.fetchall()
        if result is not None:
            global all_users
            all_users = [i[0] for i in result]
            s = "All-users: " + " ".join(all_users)
            response = bytes(s, 'gbk')
            self.send(response)

    def update_user_list(self):
        s = "All-users: " + " ".join(all_users)
        response = bytes(s, 'gbk')
        for user in on_line_users:
            client_queue[user].put(('update_user_list', response))

    def check_queue(self):
        """实时消息发送功能的核心：检查queue中是否有发送给自己的消息，如有则将消息发送给客户端"""
        while True:
            option, data = self.q.get()
            self.send(data)

    def send(self, data):
        """所有消息都经过加密后再发送给客户端"""
        secret_message = self.cipher_suite.encrypt(data)
        packet_length = len(secret_message)
        if packet_length > 9999:  # 因为包头长度是固定的4字节，4字节对应的最大数字是9999
            print('packet too long')
            return

        s = str(packet_length)
        # 在包头长度之前填充0，凑够4字节，例如将'23'凑成'0023'
        header = '0' * (header_length - len(s)) + s
        # 为了方便起见，包头不加密
        self.request.sendall(bytes(header, 'gbk') + secret_message)

    def recv_pubkey(self):
        """接收客户端发来的公钥"""
        buffer = b''
        while len(buffer) < 168:  # 经测试，公钥的数据量是168
            buffer += self.request.recv(2048)
        client_pubkey = pickle.loads(buffer)
        return client_pubkey

    def recv(self):
        """完整地读取一次客户端发来的数据，正确处理TCP粘包和拆包的问题"""
        buffer = self.buffer
        while len(buffer) < header_length:
            buffer += self.request.recv(2048)
        packet_len = int(buffer[:header_length].decode('gbk'))
        while len(buffer) < packet_len:
            buffer += self.request.recv(2048)
        self.buffer = buffer[packet_len + header_length:]

        # 用对称密钥解密接收到的数据
        message = self.cipher_suite.decrypt(buffer[header_length:packet_len + header_length])
        original_data = message
        text = message.decode('gbk')
        # 返回值text是字符串，original_data是原始的二进制数据bytes
        return text, original_data

    def authentication(self):
        """判断客户端是要登录还是要注册，如果成功返回True, 否则返回False"""
        n = 0
        while n < max_trial:
            n += 1
            text, original_data = self.recv()
            data = text.split(' ', 3)
            if len(data) < 3:
                return False
            user_id = data[1]
            password = data[2]
            if data[0] == 'login':
                if self.check_login_info(user_id, password):
                    return True
            elif data[0] == 'register':
                username = data[3]
                if self.register(user_id, username, password):
                    return True

    def telecon(self, text, original_data):
        if text.startswith('telecon?'):
            participants = text.split(' ')[1:]
            for recipient in participants:
                if not self.is_online(recipient):
                    response = bytes('telecon not_online ' + recipient, 'gbk')
                    self.send(response)
                    return

            # 全都在线的情况
            global tele_people
            tele_people = tuple(participants)
            global telecon_address
            telecon_address = []
            for recipient in participants:
                # 询问参与者是否原因参加多方通话
                client_queue[recipient].put(('telecon', original_data))
            return

        if text.startswith('telecon OK'):
            ports = text.split(' ')[2:]
            num = len(ports)
            # ['ip port1', 'ip port2', ...]
            client_ip = self.address[0]
            self.telecon_addr = [client_ip + ' ' + str(ports[i]) for i in range(num)]
            telecon_address.append(self.telecon_addr)

            if num == len(telecon_address):
                for j, user in enumerate(tele_people):
                    p = [telecon_address[i][j] for i in range(num)]
                    s = 'telecon ready ' + ' '.join(p)
                    client_queue[user].put(('telecon ready', bytes(s, 'gbk')))

        if text.startswith('telecon NO'):
            s = bytes('telecon not_allow ' + self.user_id, 'gbk')
            for user in tele_people:
                client_queue[user].put(('telecon not_allow', s))

    @staticmethod
    def is_online(user):
        """检查user是否在线"""
        if user in on_line_users:
            return True
        return False

    def online_responce(self, text):
        """
        客户端要查询user是否online（比如在发送文件之前），
        如果online，返回 b"online_responce user_id 1 user_ip port"，
        否则返回 b"online_responce user_id 0"
        """
        user_id = text.split(' ', 1)[1]
        if user_id in on_line_users:
            a = client_address[user_id]
            s = 'online_responce {} 1 {} {}'.format(user_id, a[0], a[1])
        else:
            s = 'online_responce {} 0'.format(user_id)
        response = bytes(s, 'gbk')
        self.send(response)

    def text_messaging(self, text, original_data):
        """发送文本消息"""

        # operation是操作，sender是发送方， recipient是消息的接收方，message是消息
        operation, sender, recipient, message = text.split(' ', 3)
        if self.is_online(recipient):
            # 如果接收方在线，就将消息放入负责与接收方通信的那个子进程B的queue，
            # B检查到queue中有消息后就会将消息通过socket发送给接收方客户端，
            # 客户端需要有处理机制
            client_queue[recipient].put(('text_messaging', original_data))
            self.save_message(sender, recipient, original_data)  # 保存消息到原始数据库
        else:
            self.save_message(sender, recipient, original_data, unsent=True)  # 保存消息到原始数据库和未发送数据库

    def handle_permission(self, text, original_data):
        _, message, sender, recipient = text.split(' ')
        address = self.address[0] + ' ' + str(self.address[1])
        data = original_data + b' ' + bytes(address, 'gbk')
        client_queue[recipient].put(('permission', data))

    def logout(self):
        on_line_users.remove(self.user_id)


    @staticmethod
    def save_message(sender, recipient, original_data, unsent=False):
        """将加密消息后，保存到数据库"""
        operation = 'INSERT INTO original_message(sender, recipient, message) VALUES(%s, %s, %s)'
        encrypted_args = (sender, recipient, encrypt_byte(original_data))
        message_cursor.execute(operation, encrypted_args)
        message_db.commit()
        if unsent:
            operation = 'INSERT INTO unsent_message(sender, recipient, message) VALUES(%s, %s, %s)'
            message_cursor.execute(operation, encrypted_args)
            message_db.commit()

    def check_unsent_message(self):
        """用户登录后马上检查“未发送数据库”里是否有自己的消息，如有则发送给客户端"""
        operation = "SELECT message FROM unsent_message WHERE recipient=%s"
        encrypted_args = (self.user_id,)
        message_cursor.execute(operation, encrypted_args)
        result = message_cursor.fetchall()
        if len(result) == 0:
            return
        for a in result:
            message = bytes(a[0], 'gbk')
            data = decrypt(message)
            self.send(data)

        # 从“未发送数据库”删除已发送的消息
        operation = "DELETE FROM unsent_message WHERE recipient=%s"
        message_cursor.execute(operation, encrypted_args)
        message_db.commit()

    def check_login_info(self, user_id, pwd):
        """检查用户数据库中是否有该用户，如有则返回True"""
        login_cursor.execute("SELECT password FROM user WHERE user_id=%s LIMIT 1", (user_id,))
        result = login_cursor.fetchone()
        if result is not None:
            password = decrypt(bytes(result[0], 'utf-8')).decode()
            if password == pwd:
                self.user_id = user_id
                self.login_response(success=True)
                return True
        self.login_response(success=False)
        return False

    def login_response(self, success=True):
        if success:
            s = b'login_succeeded'
        else:
            s = b'login_failed'
        self.send(s)

    def register(self, user_id, username, pwd):
        """注册账号，user_id是用户唯一标识符（建议使用邮箱）, username可以重复"""
        try:
            encrypted_args = [user_id] + multi_encrypt((username, pwd))
            # 将用户信息写入用户数据库中
            login_cursor.execute("INSERT INTO user(user_id, username, password) VALUES (%s, %s, %s)", encrypted_args)
            login_db.commit()
            self.user_id = user_id
            all_users.append(user_id)
            self.update_user_list()
            # self.username = username
            self.login_response(success=True)
            return True
        except Exception as e:
            self.login_response(success=False)
            print('register error', e)

    def change_user(self):
        if not self.authentication():  # 判断客户端是要登录还是要创建账号
            self.request.close()  # 不成功，关闭连接
            return

        # 成功登录或注册

        self.send_user_list()

        on_line_users.append(self.user_id)
        client_address[self.user_id] = self.address
        self.check_unsent_message()  # 检查离线的这段时间内是否有发送给自己的消息
        self.q = queue.Queue()
        client_queue[self.user_id] = self.q
        t = threading.Thread(target=self.check_queue)
        t.start()

        # 进入循环，不断处理客户端发来的请求
        while True:
            text, original_data = self.recv()
            # 确定客户端这一次要求执行的操作是什么，并执行相应的操作
            if text.startswith('text_messaging'):
                self.text_messaging(text, original_data)
            elif text.startswith('online_query'):
                self.online_responce(text)
            elif text.startswith('permission'):
                self.handle_permission(text, original_data)
            elif text.startswith('telecon'):
                self.telecon(text, original_data)
            elif text.startswith('logout'):
                self.logout()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == "__main__":
    HOST, PORT = "", SERVER_PORT

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address
    print(ip, port)

    # 启动主进程，每当一个客户端请求连接服务器时，主进程自动创建一个新的子进程，
    # 这个子进程负责与该客户端的通信
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)

    if input() == '0':
        server.shutdown()
        server.server_close()
