import numpy as np
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt


class Analyse_Window(QWidget):
    def __init__(self, file_name, data_dictionary):
        super().__init__()
        self.file_name = file_name
        self.setWindowTitle(self.file_name)
        self.data_dictionary = data_dictionary
        self.data = self.data_dictionary[file_name]['original_data']
        self.c = []
        self.hidden_peaks = {}
        self.selected_peaks = {}
        self.horizontalLayout = QHBoxLayout(self)

        self.win = pg.GraphicsLayoutWidget(show=True)
        self.p1 = self.win.addPlot(ignoreBounds=True)
        self.p1.setLogMode(False, True)
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.annot = pg.TextItem(color='w', fill='k')
        self.p1.addItem(self.annot, ignoreBounds=True)
        self.p1.addItem(self.vLine, ignoreBounds=True)
        self.p1.addItem(self.hLine, ignoreBounds=True)
        self.horizontalLayout.addWidget(self.win)


        self.c.append(self.p1.plot(self.data, pen='k'))
        self.p1.scene().sigMouseClicked.connect(self.hidePeaks)
        self.p1.scene().sigMouseClicked.connect(self.selectPeaks)
        self.p1.scene().sigMouseClicked.connect(self.unselectPeaks)
        self.proxy = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

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
                self.selected_peaks[str(peak_index)]['marker'] = pg.PlotDataItem([x[peak_index]],[y[peak_index]],pen=(150,0,255), symbol ='x')
                peak_annot=pg.TextItem()
                peak_annot.setText("{:.2f}".format(x[peak_index]))
                peak_annot.setColor('b')
                peak_annot.setPos(x_point, y_point)
                self.selected_peaks[str(peak_index)]['label'] = peak_annot
                self.p1.addItem(self.selected_peaks[str(peak_index)]['plot'], ignoreBounds=True)
                self.p1.addItem(self.selected_peaks[str(peak_index)]['marker'], ignoreBounds=True)
                self.p1.addItem(self.selected_peaks[str(peak_index)]['label'], ignoreBounds=True)

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
                    self.p1.removeItem(self.selected_peaks[str(peak_index)]['marker'])
                    self.p1.removeItem(self.selected_peaks[str(peak_index)]['label'])


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