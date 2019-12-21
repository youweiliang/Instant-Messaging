# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import time
import pickle
import os
import socket
from Client import Client
from send_voice import send_voice
from recv_voice import receive_voice
from file_transfer import send_file, recv_file
from multiprocessing import Process


online_status = {}
user_address = {}
file_ip = []
Output = None
my_id = ''

# 首界面
class Mainui(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initui()
        self.windowList = []

    def initui(self):

        QToolTip.setFont(QFont('SansSerif', 15))

        self.user_id = QLabel(self)
        self.user_id.setText('用户名:')
        self.user_id.setGeometry(40, 60, 61, 21)
        self.user_id_text = QLineEdit(self)
        self.user_id_text.setPlaceholderText('例如：xxxx')
        self.user_id_text.setGeometry(90, 60, 191, 31)

        self.password = QLabel(self)
        self.password.setText('密码:')
        self.password.setGeometry(40, 100, 41, 21)
        self.password_text = QLineEdit(self)
        self.password_text.setEchoMode(QLineEdit.Password)
        self.password_text.setPlaceholderText('例如：xxxx')
        self.password_text.setGeometry(90, 100, 191, 31)

        self.Login = QPushButton('用户登录', self)
        self.Login.setGeometry(200, 150, 75, 23)
        self.Login.clicked.connect(self.main_event)

        self.Register = QPushButton("用户注册", self)
        self.Register.setGeometry(90, 150, 75, 23)
        self.Register.clicked.connect(self.main_event)

        self.setGeometry(500, 500, 350, 200)
        self.setWindowTitle('MessageTalk')
        self.setWindowIcon(QIcon('MessageTalk.ico'))

# 登陆注册响应
    def main_event(self):
        user_id = self.user_id_text.text()
        password = self.password_text.text()
        sender = self.sender()
        # 登陆
        if sender == self.Login:
            operation = 'login'
            Client_t.login(user_id, password)
            try:
                text, original_data = Client_t.recv()
                if text == 'login_succeeded':
                    global my_id
                    my_id = user_id
                    Client_t.user_id = user_id
                    the_window = normalui()
                    self.windowList.append(the_window)
                    self.close()
                    the_window.show()
                else:
                    QMessageBox.information(self, '提示信息', '密码错误！')
            except:
                QMessageBox.information(self,'提示信息','服务器无反应！')
        # 注册
        elif sender == self.Register:
            operation = 'register'
            Client_t.register(user_id, password, user_id)
            text, original_data = Client_t.recv()
            if text == 'login_succeeded':
                QMessageBox.information(self, '提示信息', '注册成功！')
                my_id = user_id
                Client_t.user_id = user_id
                the_window = normalui()
                self.windowList.append(the_window)
                self.close()
                the_window.show()
            else:
                QMessageBox.information(self, '提示信息', '注册失败！')
                pass

# 第二界面


class normalui(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initui()
        self.windowList = []

    def initui(self):
        global to_user_id
        to_user_id = ''
        # 接收监听、获取用户列表
        self.recvthread = operate()
        self.recvthread.start()
        self.recvthread.sinOut.connect(self.getlist)

        self.to_user_id = QLabel(self)
        self.to_user_id.setText('聊天对象：')
        self.to_user_id.setGeometry(10, 10, 61, 20)
        self.to_user_id_text = QLabel(self)
        self.to_user_id_text.setGeometry(70, 10, 61, 21)

        self.user_id = QLabel(self)
        self.user_id.setText('我的名字：')
        self.user_id.setGeometry(370, 10, 61, 20)
        self.user_id_text = QLabel(self)
        self.user_id_text.setGeometry(430, 10, 61, 21)
        self.user_id_text.setText(my_id)

        self.Wordbrowser = QTextBrowser(self)
        self.Wordbrowser.setGeometry(10, 40, 351, 301)

        self.frilist = QListWidget(self)
        self.frilist.setGeometry(370, 40, 121, 381)
        self.frilist.itemClicked.connect(self.getintalk)
        self.frilist.itemClicked.connect(self.getmessage)

        self.Fileupload = QPushButton('发送文件', self)
        self.Fileupload.setGeometry(10, 430, 91, 31)
        self.Fileupload.clicked.connect(self.send_file)

        self.Communicate = QPushButton('多方通话', self)
        self.Communicate.setGeometry(140, 430, 91, 31)
        self.Communicate.clicked.connect(self.tele)

        self.Word = QLineEdit(self)
        self.Word.setGeometry(10, 350, 351, 71)
        self.Word_communicate = QPushButton('发送信息', self)
        self.Word_communicate.setGeometry(270, 430, 91, 31)
        self.Word_communicate.clicked.connect(self.sendmessage)

        # self.grouptalk = QPushButton('切换帐号', self)
        # self.grouptalk.clicked.connect(self.back)
        # self.grouptalk.setGeometry(190, 10, 71, 21)

        self.setGeometry(500, 500, 509, 467)
        self.setWindowTitle('MessageTalk')

    # 关闭事件重写
    def closeEvent(self, e):
        Client_t.logout()
        e.accept()

    # 发送信息
    def sendmessage(self):
        message = self.Word.text()
        Client_t.send_message(message, to_user_id)
        Client_t.save_mess(message, to_user_id, Client_t.user_id)
        self.Word.setText('')

        self.Wordbrowser.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        self.Wordbrowser.setAlignment(Qt.AlignRight)
        data = "<p style=\"color: blue;\">%s</p>" % message
        self.Wordbrowser.append(data)

        # self.Wordbrowser.append("<p style=\"text-align: left\">This paragraph is left aligned"
        #            "<p style=\"text-align: right\">This paragraph is right aligned")

    # 通信调用
    def tele(self):

        the_window = choose()
        self.windowList.append(the_window)
        the_window.show()


    # 处理获取
    def getlist(self, text):
        global on_line_id
        if text.startswith('All-users:'):
            print(text)
            try:
                self.frilist.clear()
                on_line_id = text.split(' ')[1:]
                on_line_id.remove(my_id)
                self.frilist.addItem('所有用户：')
                for i in on_line_id:
                    self.frilist.addItem(i)
            except:
                pass
        elif text.startswith('text_messaging'):
            operation, sender, recipient, message = text.split(' ', 3)
            if to_user_id == '':
                Client_t.save_message(message, sender, my_id)
            elif sender == to_user_id:
                Client_t.save_message(message, sender, my_id)
                data = "<p style=\"color: green;\">%s</p>" % message

                self.Wordbrowser.append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                self.Wordbrowser.setAlignment(Qt.AlignLeft)
                self.Wordbrowser.append(data)

        elif text.startswith('permission'):
            t = text.split(' ', 1)[1]
            message, sender, recipient, user_ip, port = t.split()
            user_address[sender] = (user_ip, int(port))

            if t.startswith('allow_file?'):
                reply = QMessageBox.information(self, "文件传输申请",  "是否接受" + sender + '的文件',
                                                QMessageBox.Yes | QMessageBox.No)
                file_ip.append(user_ip)
                if reply == QMessageBox.Yes:
                    Client_t.send_permission(sender, message='yes_allow_file')
                    print('yes_allow_file')
                    print(file_ip[-1])
                    v = Process(target=recv_file, args=(file_ip[-1],))
                    v.start()

                else:
                    Client_t.send_permission(sender, message='not_allow_file')

            elif t.startswith('yes_allow_file'):
                print('receive')
                to_ip, port = user_address[sender]
                print(to_ip, port)
                v = Process(target=send_file, args=(to_ip,))
                v.start()

            elif t.startswith('not_allow_file'):
                QMessageBox.information(self, '提示信息', '对方不接受！')

        elif text.startswith('telecon'):
            if text.startswith('telecon not_online'):
                user_a = text.split(' ')[-1]
                QMessageBox.information(self, '提示信息', user_a + '不在线！')
                return

            if text.startswith('telecon not_allow'):
                """显示用户a不同意参加，关闭多方通话"""
                user_a = text.split(' ')[-1]
                if user_a != my_id:
                    QMessageBox.information(self, '提示信息', user_a + '不同意参加！')
                return

            if text.startswith('telecon?'):
                """问用户是否同意参加多方通话，显示参与者"""
                participants = text.split(' ')[1:]
                num = len(participants)
                people = text[9:]
                reply = QMessageBox.information(self, "是否参与多方通话？",  "参与者：" + people,
                                                QMessageBox.Yes | QMessageBox.No)

                if reply == QMessageBox.Yes:
                    ports = []
                    for i in range(num):
                        if Client_t.user_id == participants[i]:
                            ports.append('0')
                        else:
                            available_port = get_free_port()
                            ports.append(str(available_port))
                    self.free_ports = ports
                    data = bytes("telecon OK " + ' '.join(ports), 'gbk')
                else:
                    data = bytes("telecon NO", 'gbk')
                Client_t.send(data)

            elif text.startswith('telecon ready'):
                """提示多方通话现在开始"""
                QMessageBox.information(self, '提示信息', '通话正在进行中...')
                address = text.split(' ')[2:]
                process = []
                for port in self.free_ports:
                    if port == '0':
                        continue
                    v = Process(target=receive_voice, args=(int(port),))
                    v.start()
                    process.append(v)
                self.voise_process = process

                num = int(len(address) / 2)
                addr = []
                for i in range(num):
                    (ip, port) = address[2 * i], int(address[2 * i + 1])
                    if port == 0:  # do not add my own port
                        continue
                    addr.append((ip, port))
                print(addr)
                s = Process(target=send_voice, args=(addr, ))
                self.send_voice_process = s
                s.start()
                """这里显示一个结束语音通话按钮，
                如果用户没按下结束按钮，就阻塞住，不继续执行下面的代码
                """
                reply = QMessageBox.information(self, "语音通话", "结束语音通话？" ,
                                                QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.terminate()
                # self.Communicate.setText('取消语音')
                # self.Communicate.clicked.connect(self.terminate)
    # 终止语音
    def terminate(self):
        self.send_voice_process.terminate()
        for v in self.voise_process:
            v.terminate()

    # 发送文件
    def send_file(self):
        result = Client_t.check_user_status(to_user_id)
        if result == 'online':
            Client_t.send_permission(to_user_id, message='allow_file?')
        elif result == 'not_online':
            QMessageBox.information(self, '提示信息', '用户不在线！')
        elif result == 'no_responce':
            QMessageBox.information(self, '提示信息', '服务器无反应！')

    # 显示聊天记录
    def getmessage(self):
        file_name = Client_t.user_id + to_user_id + '-message.pkl'
        try:
            if os.path.getsize(file_name) > 0:
                with open(file_name, 'rb') as f:
                    m = pickle.load(f)
                self.Wordbrowser.setText('')
                for t in m:
                    if t.startswith("<p style=\"color: blue") :
                        self.Wordbrowser.setAlignment(Qt.AlignRight)
                        self.Wordbrowser.append(t)
                    elif t.startswith("<p style=\"color: green"):
                        self.Wordbrowser.setAlignment(Qt.AlignLeft)
                        self.Wordbrowser.append(t)
                    else:
                        self.Wordbrowser.append(t)
            else:
                self.Wordbrowser.setText('')
        except:
            self.Wordbrowser.setText('')

    # 点击进入对话
    def getintalk(self, item):
        global to_user_id
        if item.text() == 'All-users:':
            pass
        elif item.text() != None:
            to_user_id = item.text()
            self.to_user_id_text.setText(to_user_id)

    # 切换账号
    def back(self):
        Client_t.logout()
        the_window = Mainui()
        self.windowList.append(the_window)
        self.close()
        the_window.show()

# 选择通讯
class choose(QWidget):


    def __init__(self, *args, **kwargs):
        super().__init__()
        self.windowList = []
        QToolTip.setFont(QFont('SansSerif', 15))
        ensure = QPushButton('确认名单', self)
        hbox = QHBoxLayout()
        hbox.addWidget(ensure)
        self.setGeometry(500, 500, 300, 300)
        self.setWindowTitle('语音通讯')
        ensure.clicked.connect(self.select)
        vbox = QVBoxLayout()
        self.check = []
        for i in range(len(on_line_id) - 1):
            checkBox = 'checkBox' + str(i)
            self.check.append(checkBox)
        print(self.check)
        for i in range(len(on_line_id) - 1):
            name = on_line_id[i + 1]
            self.check[i] = QCheckBox(name, self)
            vbox.addWidget(self.check[i])
            self.check[i].setChecked(True)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

    def select(self):
        global Output
        Output = []
        for i in range(len(self.check)):
            if self.check[i].isChecked() == True:
                Output.append(on_line_id[i + 1])
        Output.append(my_id)
        print('---------',Output)
        self.close()
        Client_t.ask_for_telecon(Output)


# 接收信息监听
class operate(QThread):
    sinOut = pyqtSignal(str)  # 自定义信号，执行run()函数时，从相关线程发射此信号

    def __init__(self, parent=None):
        super(operate, self).__init__(parent)
        self.working = True

    def stop(self):
        self.working = False
        self.wait()

    def run(self):
        while self.working == True:
            text, original_data = Client_t.recv()
            if text.startswith('All-users:'):
                self.sinOut.emit(text)
            elif text.startswith('text_messaging'):
                self.sinOut.emit(text)
            elif text.startswith('online_responce'):
                Client_t.handle_online_responce(text)
            elif text.startswith('permission'):
                self.sinOut.emit(text)
            elif text.startswith('telecon'):
                # Client_t.telecon(text, original_data)
                self.sinOut.emit(text)

# 读取记录监听
class Worker(QThread):
    sinOut = pyqtSignal(str)  # 自定义信号，执行run()函数时，从相关线程发射此信号

    def __init__(self, parent=None):
        super(Worker, self).__init__(parent)
        self.working = True

    def stop(self):
        self.working = False

    def run(self):
        while self.working == True:
            try:
                file_name = Client_t.user_id + to_user_id + '-message.pkl'
                with open(file_name, 'rb') as f:
                    m = pickle.load(f)
                    for t in m:
                        self.sinOut.emit(t)
                        time.sleep(0.1)
            except:
                pass

# 获取可用端口
def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    free_port = s.getsockname()[1]
    s.close()
    return free_port


if __name__ == '__main__':
    Client_t = Client()
    app = QApplication(sys.argv)
    mainui = Mainui()
    mainui.show()
    sys.exit(app.exec_())
