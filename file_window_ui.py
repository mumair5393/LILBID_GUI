# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'file_window.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtWidgets

class Ui_FileWindow(object):
    def setupUi(self, FileWindow):
        FileWindow.setObjectName("FileWindow")
        FileWindow.resize(870, 720)
        self.textEdit = QtWidgets.QPlainTextEdit(FileWindow)
        self.textEdit.setGeometry(QtCore.QRect(20, 20, 831, 481))
        self.textEdit.setObjectName("textEdit")
        self.pushButton = QtWidgets.QPushButton(FileWindow)
        self.pushButton.setGeometry(QtCore.QRect(260, 520, 331, 25))
        self.pushButton.setObjectName("pushButton")
        self.pushButton_2 = QtWidgets.QPushButton(FileWindow)
        self.pushButton_2.setGeometry(QtCore.QRect(260, 550, 331, 25))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_3 = QtWidgets.QPushButton(FileWindow)
        self.pushButton_3.setGeometry(QtCore.QRect(260, 580, 331, 25))
        self.pushButton_3.setObjectName("pushButton_3")
        self.pushButton_4 = QtWidgets.QPushButton(FileWindow)
        self.pushButton_4.setGeometry(QtCore.QRect(260, 610, 331, 25))
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_5 = QtWidgets.QPushButton(FileWindow)
        self.pushButton_5.setGeometry(QtCore.QRect(260, 640, 331, 25))
        self.pushButton_5.setObjectName("pushButton_5")
        self.pushButton_6 = QtWidgets.QPushButton(FileWindow)
        self.pushButton_6.setGeometry(QtCore.QRect(260, 670, 331, 25))
        self.pushButton_6.setObjectName("pushButton_6")

        self.retranslateUi(FileWindow)
        QtCore.QMetaObject.connectSlotsByName(FileWindow)

    def retranslateUi(self, FileWindow):
        _translate = QtCore.QCoreApplication.translate
        FileWindow.setWindowTitle(_translate("FileWindow", "Form"))
        self.pushButton.setText(_translate("FileWindow", "PLOT"))
        self.pushButton_2.setText(_translate("FileWindow", "BASELINE CORRECT"))
        self.pushButton_3.setText(_translate("FileWindow", "BASELINE CORRECT & RE-CALIBRATE"))
        self.pushButton_4.setText(_translate("FileWindow", "ANALYSE"))
        self.pushButton_5.setText(_translate("FileWindow", "MANUAL RE-CALIBRATION"))
        self.pushButton_6.setText(_translate("FileWindow", "MANUAL BASELINE CORRECTION"))