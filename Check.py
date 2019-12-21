import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


def getcheck(people):
    global on_line_id
    on_line_id = people
    class choose(QWidget):

        def __init__(self, *args, **kwargs):
            super().__init__()
            QToolTip.setFont(QFont('SansSerif', 15))

            self.setGeometry(300, 300, 175, 206)
            self.setWindowTitle('语音通讯')
            self.ensure = QPushButton('确认名单', self)
            self.ensure.setGeometry(30, 170, 80, 23)
            self.ensure.clicked.connect(self.select)

            self.check = []
            for i in range(len(on_line_id)-1):
                checkBox = 'checkBox' + str(i)
                self.check.append(checkBox)
            print(self.check)
            for i in range(len(on_line_id)-1):
                name = on_line_id[i+1]
                self.check[i] = QCheckBox(name, self)
                self.check[i].move(70, (16 * 2*i))
                self.check[i].setChecked(True)
                self.check[i].stateChanged.connect(self.btnstate, i)

        def btnstate(self, i):

            status = self.check[i].isChecked()
            print('change')

        def select(self):
            global Output
            Output = []
            for i in range(len(self.check)):
                if self.check[i].isChecked() == True:
                    Output.append(self.check[i].text())
            
            self.close()
    app = QApplication(sys.argv)
    a = choose()
    a.show()
    app.exec_()
    



