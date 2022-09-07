import numpy as np
import pyqtgraph as pg
from detectPeaks import detectPeaks
pg.setConfigOption('background', 'w')
from PyQt5.QtWidgets import *
from PyQt5 import QtGui
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from analyse_ui import Ui_Analyse


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

class Analyse_Window(QWidget, Ui_Analyse):
    def __init__(self, file_name, data_dictionary, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.file_name = file_name
        self.setWindowTitle(self.file_name)
        self.data_dictionary = data_dictionary
        self.p1 = self.graphicsView.addPlot(ignoreBounds=True)
        self.p1.setLogMode(False, True)
        self.data = self.data_dictionary[file_name]['original_data']
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setHorizontalHeaderLabels(["Peak mass", "Peak intensity"])
        self.detected_peaks_plot = pg.ScatterPlotItem()
        self.cluster_plot = pg.ScatterPlotItem()
        self.detected_peaks, self.detected_peaks_indices = self.detect_and_plot_peaks()

        self.c = []
        self.hidden_peaks = {}
        self.selected_peaks = {}
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
        self.pushButton.clicked.connect(lambda: self.clear())
        self.pushButton_2.clicked.connect(lambda: self.detect_and_plot_peaks())
        self.pushButton_3.clicked.connect(lambda: self.plot_detected_water_clusters())

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
                self.hidden_peaks[str(peak_index)]['plot'] = pg.PlotDataItem(x[peak_index-20:peak_index+20], y[peak_index-20:peak_index+20], pen=(228, 228, 255))
                self.p1.addItem(self.hidden_peaks[str(peak_index)]['plot'], ignoreBounds=True)

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
                self.selected_peaks[str(peak_index)]['plot'] = pg.PlotDataItem(x[peak_index - 20:peak_index + 20],
                                                                          y[peak_index - 20:peak_index + 20],
                                                                          pen=(255,0,0))
                peak_pos = [
                    {'pos': np.array([x[peak_index], np.log10(y[peak_index])]), 'size': 8, 'pen': 'b', 'brush': 'b',
                     'symbol': 'x'}]
                label = [
                    {'pos': np.array([x[peak_index], np.log10(y[peak_index]* 1.3)]), 'size': 30, 'pen': 'r', 'brush': 'r', 'symbol': self.custom_symbol("{:.2f}".format(x[peak_index]))}]
                self.selected_peaks[str(peak_index)]['peak_pos'] = pg.ScatterPlotItem(peak_pos)
                self.selected_peaks[str(peak_index)]['label'] = pg.ScatterPlotItem(label)
                self.p1.addItem(self.selected_peaks[str(peak_index)]['plot'], ignoreBounds=True)
                self.p1.addItem(self.selected_peaks[str(peak_index)]['peak_pos'], ignoreBounds=True)
                self.p1.addItem(self.selected_peaks[str(peak_index)]['label'], ignoreBounds=True)
                rowPosition = self.tableWidget.rowCount()
                self.tableWidget.insertRow(rowPosition)
                self.tableWidget.setItem(rowPosition, 0, QCustomTableWidgetItem(x[peak_index]))
                self.tableWidget.setItem(rowPosition, 1, QCustomTableWidgetItem(y[peak_index]))
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
                    self.p1.removeItem(self.hidden_peaks[str(peak_index)]['plot'])
                if str(peak_index) in self.selected_peaks.keys():
                    self.p1.removeItem(self.selected_peaks[str(peak_index)]['plot'])
                    self.p1.removeItem(self.selected_peaks[str(peak_index)]['label'])
                    self.p1.removeItem(self.selected_peaks[str(peak_index)]['peak_pos'])
                matching_items = self.tableWidget.findItems(str(x[peak_index]), Qt.MatchContains)[0].row()
                self.tableWidget.removeRow(matching_items)
                self.tableWidget.sortItems(0)


    def mouseMoved(self, evt):
        pos = evt[0]  ## using signal proxy turns original arguments into a tuple
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            x_point, y_point = mousePoint.x(), mousePoint.y()
            indx = min(np.searchsorted(self.data[:, 0], x_point), len(self.data[:, 0]) - 1)
            x_point = self.data[:, 0][indx]
            y_point = self.data[:, 1][indx]
            # label.setText("<span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y1=%0.1f</span>" % (x_point, y_point))
            text = "mass: {:.2f}, intensity: {:.2f}".format(x_point, y_point)
            self.annot.setText(text)
            self.annot.setPos(mousePoint.x(), mousePoint.y())
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

    def plot_detected_water_clusters(self):
        selected = self.tableWidget.selectedItems()
        if self.cluster_plot in self.p1.listDataItems():
            self.p1.removeItem(self.cluster_plot)
        self.cluster_plot = pg.ScatterPlotItem()
        cluster_indexes = []
        if selected:
            for item in selected:
                cluster_indexes += self.detect_water_clusters(float(item.text()))
            cluster_indexes = np.unique(cluster_indexes)
            cluster_pos = [
                {'pos': np.array([self.detected_peaks[i][0], np.log10(self.detected_peaks[i][1])]), 'size': 8, 'pen': 'g', 'brush': 'g',
                 'symbol': 'x'} for i in cluster_indexes]
            self.cluster_plot.addPoints(cluster_pos)
            cluster_label_pos = [
                {'pos': np.array([self.detected_peaks[i][0], np.log10(self.detected_peaks[i][1] * 1.3)]), 'size': 30, 'pen': 'g',
                 'brush': 'g',
                 'symbol': self.custom_symbol("{:.2f}".format(self.detected_peaks[i][0]))} for i in cluster_indexes]
            self.cluster_plot.addPoints(cluster_label_pos)
            self.p1.addItem(self.cluster_plot, ignoreBounds=True)
            return


    def detect_water_clusters(self, selected_peak):
        selected_peak_index = np.where(self.detected_peaks == selected_peak)[0][0]
        cluster = [selected_peak_index]
        for peak in np.flip(self.detected_peaks[:, 0][:int(selected_peak_index)]):
            if peak - 0.5 < self.detected_peaks[selected_peak_index][0] - 18 < peak + 0.5:
                selected_peak_index = np.where(self.detected_peaks == peak)[0][0]
                if peak not in cluster:
                    cluster.append(selected_peak_index)
        for peak in self.detected_peaks[:, 0][int(selected_peak_index):]:
            if peak - 0.5 < self.detected_peaks[selected_peak_index][0] + 18 < peak + 0.5:
                selected_peak_index = np.where(self.detected_peaks == peak)[0][0]
                if peak not in cluster:
                    cluster.append(selected_peak_index)
        cluster.sort()
        return cluster


    def custom_symbol(self, symbol: str, font: QFont = QtGui.QFont("San Serif")):
        """Create custom symbol with font"""
        # We just want one character here, comment out otherwise
        # assert len(symbol) == 1
        pg_symbol = QtGui.QPainterPath()
        pg_symbol.addText(0, 0, font, symbol)
        # Scale symbol
        br = pg_symbol.boundingRect()
        scale = min(1. / br.width(), 1. / br.height())
        tr = QtGui.QTransform()
        tr.scale(scale, scale)
        tr.rotate(90)
        tr.translate(-br.x() - br.width() / 2., -br.y() - br.height() / 2.)
        return tr.map(pg_symbol)

    def detect_and_plot_peaks(self):
        try:
            self.clear()
            self.detected_peaks_plot = pg.ScatterPlotItem()
        except:
            pass
        if "Peaks" not in self.data_dictionary[self.file_name].keys():
            self.data_dictionary[self.file_name]["Peaks"] = detectPeaks(self.data)
        detected_peaks, detected_peaks_indices, _ = self.data_dictionary[self.file_name]["Peaks"]
        peak_pos = [
            {'pos': np.array([self.data[i][0], np.log10(self.data[i][1])]), 'size': 8, 'pen': 'b', 'brush': 'b',
             'symbol': 'x'} for i in detected_peaks_indices]
        self.detected_peaks_plot.addPoints(peak_pos)
        peak_label_pos = [
            {'pos': np.array([self.data[i][0], np.log10(self.data[i][1] * 1.3)]), 'size': 30, 'pen': 'r', 'brush': 'r',
             'symbol': self.custom_symbol("{:.2f}".format(self.data[i][0]))} for i in detected_peaks_indices]
        self.detected_peaks_plot.addPoints(peak_label_pos)
        for i in range(len(detected_peaks)):
            rowPosition = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowPosition)
            self.tableWidget.setItem(rowPosition, 0, QCustomTableWidgetItem(detected_peaks[rowPosition][0]))
            self.tableWidget.setItem(rowPosition, 1, QCustomTableWidgetItem(detected_peaks[rowPosition][1]))
        self.p1.addItem(self.detected_peaks_plot, ignoreBounds=True)
        return detected_peaks, detected_peaks_indices

    def clear(self):
        if self.cluster_plot in self.p1.listDataItems():
            self.p1.removeItem(self.cluster_plot)
        if self.detected_peaks_plot in self.p1.listDataItems():
            self.p1.removeItem(self.detected_peaks_plot)
        number_of_rows = self.tableWidget.rowCount()
        for i in range(number_of_rows):
            self.tableWidget.removeRow(0)

        for k in self.hidden_peaks.keys():
            self.p1.removeItem(self.hidden_peaks[k]["plot"])

        for k in self.selected_peaks.keys():
            self.p1.removeItem(self.selected_peaks[k]["plot"])
            self.p1.removeItem(self.selected_peaks[k]["peak_pos"])
            self.p1.removeItem(self.selected_peaks[k]["label"])

