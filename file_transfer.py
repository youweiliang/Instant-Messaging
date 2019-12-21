# -*- coding: utf-8 -*-
import os
import json
import socket
import struct
import tkinter as tk
from tkinter.filedialog import askopenfilename
from PyQt5.QtWidgets import QApplication, QProgressBar, QPushButton
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QBasicTimer

RECV_PORT = 44444
SEND_PORT = 44444


def send_file(to_ip):

    class ProgressBar(QtWidgets.QWidget):
        def __init__(self, parent=None):
            QtWidgets.QWidget.__init__(self)

            self.setGeometry(300, 300, 250, 150)
            self.setWindowTitle('文件传输进度')
            self.pbar = QProgressBar(self)
            self.pbar.setGeometry(30, 40, 200, 25)

            self.button = QPushButton('开始发送', self)
            self.button.setFocusPolicy(Qt.NoFocus)
            self.button.move(40, 80)

            self.button.clicked.connect(self.onStart)
            self.timer = QBasicTimer()
            self.step = 0
            self.sent_size = 0

        def timerEvent(self, event):
            if self.step >= 100:
                self.timer.stop()
                self.button.setText('发送完毕')
                return

            data = f.read(10240)
            conn.sendall(data)
            self.sent_size += len(data)
            self.step = self.sent_size / file_size_bytes * 100
            self.pbar.setValue(self.step)

        def onStart(self):
            if self.timer.isActive():
                self.timer.stop()
                self.button.setText('继续')
            else:
                self.timer.start(0, self)
                self.button.setText('暂停')

    tk.Tk().withdraw()
    file_name = askopenfilename()
    file_size_bytes = os.path.getsize(file_name)
    name = file_name.split('/')[-1]
    head_dir = {
        "file_name": name,
        "file_size_bytes": file_size_bytes,
    }
    head_info = json.dumps(head_dir)
    head_info = bytes(head_info, 'utf-8')
    head_info_len = struct.pack("i", len(head_info))
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((to_ip, SEND_PORT))
        conn.send(head_info_len)  # 字节为4
        conn.send(head_info)  # 发送报头的内容
        with open(file_name, "rb") as f:
            import sys

            app = QApplication(sys.argv)
            qb = ProgressBar()
            qb.show()
            app.exec_()

            print("文件传输完成!")
    except Exception as e:
        print("connection fail!", e)


def recv_file(from_ip):
    
    class ProgressBar(QtWidgets.QWidget):
        def __init__(self, parent=None):
            QtWidgets.QWidget.__init__(self)

            self.setGeometry(300, 300, 250, 150)
            self.setWindowTitle('文件传输进度')
            self.pbar = QProgressBar(self)
            self.pbar.setGeometry(30, 40, 200, 25)

            self.button = QPushButton('开始接收', self)
            self.button.setFocusPolicy(Qt.NoFocus)
            self.button.move(40, 80)

            self.timer = QBasicTimer()
            self.step = 0

            self.recv_size = 0  # 已接收字节
            self.onStart()

        def timerEvent(self, event):
            if self.step >= 100:
                self.timer.stop()
                self.button.setText('接收完毕')
                return

            if (file_size - self.recv_size) > 1024:
                recv_mesg = sender_conn.recv(1024)
                self.recv_size += len(recv_mesg)
                f.write(recv_mesg)
            else:
                recv_mesg = sender_conn.recv(file_size - self.recv_size)
                self.recv_size += len(recv_mesg)
                f.write(recv_mesg)

            self.step = self.recv_size / file_size * 100
            self.pbar.setValue(self.step)

        def onStart(self):
            if self.timer.isActive():
                self.timer.stop()
                self.button.setText('继续')
            else:
                self.timer.start(0, self)
                self.button.setText('暂停')
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.bind(('', RECV_PORT))
    conn.listen(1)

    (sender_conn, address) = conn.accept()

    struct_len = sender_conn.recv(4)  # 接受报头长度
    struct_info_len = struct.unpack('i', struct_len)[0]  # 解析报文长度
    head_info = sender_conn.recv(struct_info_len)  # 接受报文内容
    head_dir = json.loads(head_info.decode("utf-8"))  # 反序列化
    file_name = head_dir["file_name"]  # 文件名
    file_size = head_dir["file_size_bytes"]  # 文件大小

    with open(file_name, "wb") as f:
        import sys
        app = QApplication(sys.argv)
        qb = ProgressBar()
        qb.show()
        app.exec_()

    print("文件传输完成!")

    conn.close()



