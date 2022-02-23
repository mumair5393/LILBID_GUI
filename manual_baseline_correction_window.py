import numpy as np
import os
from baseline_correction import airPLS
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
from PyQt5.QtWidgets import *
from manual_baseline_correction_ui import Ui_Manual_Baseline_Correction


class Slider(QWidget):
    def __init__(self, minimum, maximum, parent=None):
        super(Slider, self).__init__(parent=parent)
        self.verticalLayout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QHBoxLayout()
        spacerItem = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Vertical)
        self.horizontalLayout.addWidget(self.slider)
        spacerItem1 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.resize(self.sizeHint())
        self.slider.setValue(minimum)
        self.slider.setMinimum(minimum)
        self.slider.setMaximum(maximum)
        self.minimum = minimum
        self.maximum = maximum
        self.slider.valueChanged.connect(self.setLabelValue)
        self.x = self.slider.value()
        self.setLabelValue(self.slider.value())

    def setLabelValue(self, value):
        self.x = self.slider.value()
        self.label.setText("{0:.4g}".format(self.x))


class Manual_Baseline_Correction_Window(QWidget, Ui_Manual_Baseline_Correction):
    def __init__(self, file_name, data_dictionary, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.file_name = file_name
        self.setWindowTitle(self.file_name)
        self.data_dictionary = data_dictionary
        self.data = self.data_dictionary[file_name]['original_data']
        self.c = []
        self.horizontalSlider.setMinimum(1)
        self.horizontalSlider.setMaximum(50)
        self.horizontalSlider_2.setMinimum(1)
        self.horizontalSlider_2.setMaximum(5)
        self.horizontalSlider_3.setMinimum(1)
        self.horizontalSlider_3.setMaximum(1000)
        self.graphicsView.setLogMode(False, True)
        self.c.append(self.graphicsView.plot(self.data))
        self.horizontalSlider.valueChanged.connect(self.manual_baseline_correct)
        self.horizontalSlider_2.valueChanged.connect(self.manual_baseline_correct)
        self.horizontalSlider_3.valueChanged.connect(self.manual_baseline_correct)
        self.pushButton.clicked.connect(lambda: self.manual_baseline_correct_save())
        self.manual_baseline_correct()

    def manual_baseline_correct(self):
        if len(self.c) >= 2:
            self.c[-1].clear()
            del self.c[-1]
        self.baseline = airPLS(self.data[:, 1], self.horizontalSlider_3.value(), self.horizontalSlider_2.value(), self.horizontalSlider.value())
        self.c.append(self.graphicsView.plot(self.data[:, 0], self.baseline, pen='r'))

    def manual_baseline_correct_save(self):
        msg_box = QMessageBox()
        msg_box.setText('Are you satisfied with the current baseline correction? Would you like to save it?.')
        msg_box.setWindowTitle("MessageBox")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg_box.exec_()
        if retval == QMessageBox.Yes:
            file_path = os.path.join(self.data_dictionary[self.file_name]['file_path'], self.file_name)
            corrected = self.data[:, 1] - self.baseline
            corrected[np.where(corrected < 0)] = 0.000001
            corrected = corrected + 0.007
            baseline_corrected_data = np.hstack([self.data[:, 0].reshape(-1, 1), corrected.reshape(-1, 1)])
            self.data_dictionary[self.file_name]['baseline_corrected_data'] = baseline_corrected_data
            with open(file_path, 'r') as raw:
                text = raw.readlines()[0:20]
                dir_name = QFileDialog.getExistingDirectory(self, 'Select Folder')
                baseline_corrected_file_name = os.path.join(dir_name, self.file_name[:-4] + '_manual_baseline_corrected.txt')
                np.savetxt(baseline_corrected_file_name, self.data_dictionary[self.file_name]['baseline_corrected_data'],
                           fmt='%.8f', header=''.join(text)[:-1], comments='', delimiter='\t')

            window = pg.plot(self.data_dictionary[self.file_name]['baseline_corrected_data'], pen='k')
            window.setLogMode(False, True)
            window.setGeometry(100, 100, 870, 720)
            window.setWindowTitle(self.file_name)
        else:
            pass