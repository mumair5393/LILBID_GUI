import pyqtgraph as pg
pg.setConfigOption('background', 'w')
import numpy as np
from PyQt5.QtCore import Qt
from manual_recal_ui import Ui_Manual_Recalibration
from automated_recalibration import manual_recalibration
from PyQt5.QtWidgets import *
import os

class QCustomTableWidgetItem (QTableWidgetItem):
    def __init__ (self, value):
        super(QCustomTableWidgetItem, self).__init__(str('%s' % value))

    def __lt__ (self, other):
        if (isinstance(other, QCustomTableWidgetItem)):
            selfDataValue  = float(str(self.data(Qt.EditRole)))
            otherDataValue = float(str(other.data(Qt.EditRole)))
            return selfDataValue < otherDataValue
        else:
            return QTableWidgetItem.__lt__(self, other)


class Manual_Recalibration_Window(QWidget, Ui_Manual_Recalibration):
    def __init__(self, file_name, data_dictionary, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.file_name = file_name
        self.setWindowTitle(self.file_name)
        self.data_dictionary = data_dictionary
        self.data = self.data_dictionary[file_name]['original_data']
        self.c = []
        self.hidden_peaks = {}
        self.selected_peaks = {}

        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(["Detected mass", "Corrected mass", "Peak intensity"])

        self.p1 = self.graphicsView.addPlot(ignoreBounds=True)
        self.p1.setLogMode(False, True)
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.annot = pg.TextItem(color='w', fill='k')
        self.p1.addItem(self.annot, ignoreBounds=True)
        self.p1.addItem(self.vLine, ignoreBounds=True)
        self.p1.addItem(self.hLine, ignoreBounds=True)

        self.c.append(self.p1.plot(self.data, pen='k'))
        self.p1.scene().sigMouseClicked.connect(self.hidePeaks)
        self.p1.scene().sigMouseClicked.connect(self.selectPeaks)
        self.p1.scene().sigMouseClicked.connect(self.unselectPeaks)
        self.proxy = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

        self.pushButton.clicked.connect(lambda: self.manual_recalibrate_save())
        self.pushButton_2.clicked.connect(lambda: self.clear())

    # Hide peaks
    def hidePeaks(self, event):
        if event.double():
            if self.p1.sceneBoundingRect().contains(event._scenePos):
                mousePoint = self.p1.vb.mapSceneToView(event._scenePos)
                x, y = self.data[:,0], self.data[:,1]
                x_point, y_point = mousePoint.x(), mousePoint.y()
                indx = min(np.searchsorted(x, x_point), len(x) - 1)
                peak_index = np.argmax(y[indx - 100:indx + 100])
                peak_index = np.arange(len(x))[indx - 100:indx + 100][peak_index]
                print(x[peak_index], y[peak_index])
                self.hidden_peaks[str(peak_index)] = {}
                self.hidden_peaks[str(peak_index)]['plot'] = self.p1.plot(x[peak_index-20:peak_index+20], y[peak_index-20:peak_index+20], pen=(228, 228, 255))

    def selectPeaks(self, event):
        modifierPressed = QApplication.keyboardModifiers()
        if modifierPressed  == Qt.ShiftModifier and event._button == Qt.LeftButton:
            if self.p1.sceneBoundingRect().contains(event._scenePos):
                mousePoint = self.p1.vb.mapSceneToView(event._scenePos)
                x, y = self.data[:, 0], self.data[:, 1]
                x_point, y_point = mousePoint.x(), mousePoint.y()
                indx = min(np.searchsorted(x, x_point), len(x) - 1)
                peak_index = np.argmax(y[indx - 100:indx + 100])
                peak_index = np.arange(len(x))[indx - 100:indx + 100][peak_index]
                print(x[peak_index], y[peak_index])
                self.selected_peaks[str(peak_index)] = {}
                self.selected_peaks[str(peak_index)]['plot'] = self.p1.plot(x[peak_index - 20:peak_index + 20],
                                                                          y[peak_index - 20:peak_index + 20],
                                                                          pen=(255,0,0))
                #self.selected_peaks[str(peak_index)]['marker'] = self.p1.plot(x[peak_index], y[peak_index], color=(255,0,0))


                rowPosition = self.tableWidget.rowCount()
                self.tableWidget.insertRow(rowPosition)
                self.tableWidget.setItem(rowPosition, 0, QCustomTableWidgetItem(x[peak_index]))
                self.tableWidget.setItem(rowPosition, 2, QCustomTableWidgetItem(y[peak_index]))
                self.tableWidget.setItem(rowPosition, 1, QCustomTableWidgetItem(0))
                self.tableWidget.sortItems(0)

    def unselectPeaks(self, event):
        modifierPressed = QApplication.keyboardModifiers()
        if modifierPressed  == Qt.ControlModifier and event._button == Qt.LeftButton:
            if self.p1.sceneBoundingRect().contains(event._scenePos):
                mousePoint = self.p1.vb.mapSceneToView(event._scenePos)
                x, y = self.data[:, 0], self.data[:, 1]
                x_point, y_point = mousePoint.x(), mousePoint.y()
                indx = min(np.searchsorted(x, x_point), len(x) - 1)
                peak_index = np.argmax(y[indx - 100:indx + 100])
                peak_index = np.arange(len(x))[indx - 100:indx + 100][peak_index]
                if str(peak_index) in self.hidden_peaks.keys():
                    self.hidden_peaks[str(peak_index)]['plot'].clear()
                    #self.hidden_peaks[str(peak_index)]['marker'].clear()
                    del self.hidden_peaks[str(peak_index)]
                if str(peak_index) in self.selected_peaks.keys():
                    self.selected_peaks[str(peak_index)]['plot'].clear()
                    #self.hidden_peaks[str(peak_index)]['marker'].clear()
                    del self.selected_peaks[str(peak_index)]
                matching_items = self.tableWidget.findItems(str(x[peak_index]), Qt.MatchContains)[0].row()
                self.tableWidget.removeRow(matching_items)
                self.tableWidget.sortItems(0)

    def manual_recalibrate_save(self):
        msg_box = QMessageBox()
        msg_box.setText('Are you satisfied with the current calibreation? Would you like to save it?.')
        msg_box.setWindowTitle("MessageBox")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg_box.exec_()
        detected_peaks = []
        corrected_peaks = []
        if retval == QMessageBox.Yes:
            file_path = os.path.join(self.data_dictionary[self.file_name]['file_path'], self.file_name)
            number_of_rows = self.tableWidget.rowCount()
            for i in range(number_of_rows):
                detected_peaks.append(float(self.tableWidget.item(i, 0).text()))
                corrected_peaks.append(float(self.tableWidget.item(i, 1).text()))
            detected_peaks = np.array(detected_peaks)
            corrected_peaks = np.array(corrected_peaks)
            self.data_dictionary[self.file_name]['recalibrated_data'] = manual_recalibration(self.data, detected_peaks, corrected_peaks)
            with open(file_path, 'r') as raw:
                text = raw.readlines()[0:20]
                dir_name = QFileDialog.getExistingDirectory(self, 'Select Folder')
                baseline_corrected_file_name = os.path.join(dir_name, self.file_name[:-4] + '_manual_recalibration.txt')
                np.savetxt(baseline_corrected_file_name, self.data_dictionary[self.file_name]['recalibrated_data'],
                           fmt='%.8f', header=''.join(text)[:-1], comments='', delimiter='\t')
            self.c.append(self.p1.plot(self.data_dictionary[self.file_name]['recalibrated_data'], pen='b'))
        else:
            pass

    def clear(self):
        number_of_rows = self.tableWidget.rowCount()
        for i in range(number_of_rows):
            self.tableWidget.removeRow(0)
        while self.hidden_peaks:
            try:
                self.hidden_peaks[list(self.hidden_peaks.keys())[0]]['plot'].clear()
                del self.hidden_peaks[list(self.hidden_peaks.keys())[0]]
            except:
                continue
        while self.selected_peaks:
            try:
                self.selected_peaks[list(self.selected_peaks.keys())[0]]['plot'].clear()
                del self.selected_peaks[list(self.selected_peaks.keys())[0]]
            except:
                continue


    def mouseMoved(self, evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            x_point, y_point = mousePoint.x(), mousePoint.y()
            indx = min(np.searchsorted(self.data[:, 0], x_point), len(self.data[:, 0]) - 1)
            x_point = self.data[:, 0][indx]
            y_point = self.data[:, 1][indx]
            text = "mass: {:.2f}, intensity: {:.2f}".format(x_point, y_point)
            self.annot.setText(text)
            self.annot.setPos(mousePoint.x(), mousePoint.y())
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())
