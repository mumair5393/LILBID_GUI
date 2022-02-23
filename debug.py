import sys
import os
import numpy as np
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
from analyse_window import Analyse_Window
from baseline_correction import baseline_correction
from automated_recalibration import automated_recal
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from plot_window import Plot_All_Graphs
from manual_baseline_correction_window import Manual_Baseline_Correction_Window
from manual_recal_window import Manual_Recalibration_Window
from file_window_ui import Ui_FileWindow

class File_Window(QWidget, Ui_FileWindow):
    def __init__(self, file_name, data_dictionary, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.file_name = file_name
        self.data_dictionary = data_dictionary
        file_path = os.path.join(self.data_dictionary[file_name]['file_path'], file_name)
        with open(file_path, 'r') as raw_text_file:
            raw_text_matter = raw_text_file.read()
        self.setWindowTitle(self.file_name)
        #self.textEdit.insertPlainText(raw_text_matter)
        #self.textEdit.setReadOnly(True)
        self.pushButton.clicked.connect(lambda: self.plot_graphs_func())
        self.pushButton_2.clicked.connect(lambda: self.baseline_correct_save_func(self.file_name))
        self.pushButton_3.clicked.connect(lambda: self.baseline_correct_recalibrate_save_func(self.file_name))
        self.pushButton_4.clicked.connect(lambda: self.analyse_spectrum_func())
        self.pushButton_5.clicked.connect(lambda: self.manual_recalibration_func())
        self.pushButton_6.clicked.connect(lambda: self.manual_baseline_correction_func())

    def plot_graphs_func(self):
        if 'recalibrated_data' not in self.data_dictionary[self.file_name]:
            self.baseline_correct_recalibrate_func(self.file_name)
        self.plot_graphs_window = Plot_All_Graphs(self.file_name, self.data_dictionary)
        self.plot_graphs_window.show()

    def manual_recalibration_func(self):
        self.manual_recalibration_window = Manual_Recalibration_Window(self.file_name, self.data_dictionary)
        self.manual_recalibration_window.show()

    def manual_baseline_correction_func(self):
        self.manual_baseline_correction_window = Manual_Baseline_Correction_Window(self.file_name, self.data_dictionary)
        self.manual_baseline_correction_window.show()

    def analyse_spectrum_func(self):
        self.analyse_spectrum_window = Analyse_Window(self.file_name, self.data_dictionary)
        self.analyse_spectrum_window.show()


    def baseline_correct_save_func(self, file_name):
        msg_box = QMessageBox()
        msg_box.setText('Do you want to save the baseline corrected data?')
        msg_box.setWindowTitle("MessageBox")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg_box.exec_()
        if 'baseline_corrected_data' not in self.data_dictionary[file_name]:
            self.baseline_correct_func(file_name)
        file_path = os.path.join(self.data_dictionary[file_name]['file_path'], file_name)
        if retval == QMessageBox.Yes:
            with open(file_path, 'r') as raw:
                text = raw.readlines()[0:20]
            dir_name = QFileDialog.getExistingDirectory(self, 'Select Folder')
            baseline_corrected_file_name = os.path.join(dir_name, file_name[:-4] + '_baseline_corrected.txt')
            np.savetxt(baseline_corrected_file_name, self.data_dictionary[file_name]['baseline_corrected_data'],
                       fmt='%.8f', header=''.join(text)[:-1], comments='', delimiter='\t')
        else:
            pass

    def baseline_correct_recalibrate_save_func(self, file_name):
        msg_box = QMessageBox()
        msg_box.setText('Do you want to save the baseline corrected and re-calibrated data?')
        msg_box.setWindowTitle("MessageBox")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        retval = msg_box.exec_()
        if 'recalibrated_data' not in self.data_dictionary[file_name]:
            self.baseline_correct_recalibrate_func(file_name)
        file_path = os.path.join(self.data_dictionary[file_name]['file_path'], file_name)
        if retval == QMessageBox.Yes:
            with open(file_path, 'r') as raw:
                text = raw.readlines()[0:20]
            dir_name = QFileDialog.getExistingDirectory(self, 'Select Folder')
            recalibrated_file_name = os.path.join(dir_name, file_name[:-4] + '_recalibrated.txt')
            np.savetxt(recalibrated_file_name, self.data_dictionary[file_name]['recalibrated_data'], fmt='%.8f',
                       header=''.join(text)[:-1], comments='', delimiter='\t')

        else:
            pass

    def baseline_correct_recalibrate_func(self, file_name):
        self.data_dictionary[file_name]['baseline_corrected_data'] = baseline_correction(
            self.data_dictionary[file_name]['original_data'])
        self.data_dictionary[file_name]['recalibrated_data'], self.data_dictionary[file_name][
            'manual_check'] = automated_recal(file_name, self.data_dictionary[file_name]['baseline_corrected_data'])
        if self.data_dictionary[file_name]['manual_check']:
            msg_box = QMessageBox()
            msg_box.setText('Manually check the recalibration for ' + file_name)
            msg_box.setWindowTitle("Information MessageBox")
            msg_box.setStandardButtons(QMessageBox.Ok)
            retval = msg_box.exec_()

    def baseline_correct_func(self, file_name):
        self.data_dictionary[file_name]['baseline_corrected_data'] = baseline_correction(
            self.data_dictionary[file_name]['original_data'])


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(870)
        self.setFixedHeight(720)
        self.data_dictionary = {}
        self.baseline_corrected_data = {}
        self.setWindowTitle("LILBID Analysis")
        self.temp_file = None

        # Create a QHBoxLayout instance
        layout = QVBoxLayout()
        self.list_widget = QListWidget()

        self.load_button = QPushButton("LOAD DATA ")
        self.load_button.clicked.connect(lambda: self.load())

        self.open_file = QPushButton("OPEN FILE")
        self.open_file.clicked.connect(lambda: self.open_file_func())

        self.baseline_correct_all = QPushButton("BASELINE CORRECT ALL")
        self.baseline_correct_all.clicked.connect(lambda: self.baseline_correct_all_func())

        self.baseline_correct_recalibrate_all = QPushButton("BASELINE CORRECT && RE-CALIBRATE ALL")
        self.baseline_correct_recalibrate_all.clicked.connect(lambda: self.baseline_correct_recalibrate_all_func())

        # Add widgets to the layout
        layout.addWidget(self.list_widget)
        layout.addWidget(self.load_button)
        layout.addWidget(self.open_file, 1)
        layout.addWidget(self.baseline_correct_all, 2)
        layout.addWidget(self.baseline_correct_recalibrate_all, 3)
        # Set the layout on the application's window
        self.setLayout(layout)

    def load(self):
        file_names = QFileDialog.getOpenFileNames(self, 'Open a file',
                                                  './',
                                                  'Text Files (*.txt)')
        self.files = file_names[0]
        self.list_widget.clear()
        self.data_dictionary.clear()
        for idx in self.files:
            file_name = os.path.basename(idx)
            self.list_widget.addItem(file_name)
            self.data_dictionary[file_name] = {}
            self.data_dictionary[file_name]['original_data'] = np.loadtxt(idx)
            self.data_dictionary[file_name]['file_path'] = os.path.dirname(idx)

    def open_file_func(self):
        if self.list_widget.count() == 0:
            msg_box = QMessageBox()
            msg_box.setText('Load data first')
            msg_box.setWindowTitle("Information MessageBox")
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            retval = msg_box.exec_()
            self.load()
        else:
            selected = self.list_widget.selectedItems()
            if len(selected) == 0:
                print('Select the file to open')
                msg_box = QMessageBox()
                msg_box.setText('Select the file to open')
                msg_box.setWindowTitle("Information MessageBox")
                msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                retval = msg_box.exec_()

            else:
                file_name = selected[0].text()
                print(file_name)
                self.file_window = File_Window(file_name, self.data_dictionary)
                self.file_window.show()

    def baseline_correct_all_func(self):
        dir_name = QFileDialog.getExistingDirectory(self, 'Select Folder')
        for idx in self.files:
            with open(idx, 'r') as raw:
                text = raw.readlines()[0:20]
            file_name = os.path.basename(idx)
            self.data_dictionary[file_name]['baseline_corrected_data'] = baseline_correction(
                self.data_dictionary[file_name]['original_data'])
            baseline_corrected_file_name = os.path.join(dir_name, file_name[:-4] + '_baseline_corrected.txt')
            np.savetxt(baseline_corrected_file_name, self.data_dictionary[file_name]['baseline_corrected_data'],
                       fmt='%.8f', header=''.join(text)[:-1], comments='', delimiter='\t')
        msg_box = QMessageBox()
        msg_box.setText('Baseline correction successful')
        msg_box.setWindowTitle("Information MessageBox")
        msg_box.setStandardButtons(QMessageBox.Ok)
        retval = msg_box.exec_()

    # check function::
    def baseline_correct_recalibrate_all_func(self):
        dir_name = QFileDialog.getExistingDirectory(self, 'Select Folder')
        recheck_files = []
        for idx in self.files:
            with open(idx, 'r') as raw:
                text = raw.readlines()[0:20]
            file_name = os.path.basename(idx)
            print(file_name)
            self.data_dictionary[file_name]['baseline_corrected_data'] = baseline_correction(
                self.data_dictionary[file_name]['original_data'])
            self.data_dictionary[file_name]['recalibrated_data'], self.data_dictionary[file_name][
                'manual_check'] = automated_recal(file_name, self.data_dictionary[file_name]['baseline_corrected_data'])
            if self.data_dictionary[file_name]['manual_check']:
                recheck_files.append(file_name)
            recalibrated_file_name = os.path.join(dir_name, file_name[:-4] + '_recalibrated.txt')
            np.savetxt(recalibrated_file_name, self.data_dictionary[file_name]['recalibrated_data'], fmt='%.8f',
                       header=''.join(text)[:-1], comments='', delimiter='\t')
        msg_box = QMessageBox()
        msg_box.setText('Recalibration successful')
        msg_box.setWindowTitle("Information MessageBox")
        msg_box.setStandardButtons(QMessageBox.Ok)
        retval = msg_box.exec_()
        if recheck_files:
            msg_box = QMessageBox()
            msg_box.setText('Manually check the recalibration for the following files:\n' + '\n'.join(
                recheck_files))
            msg_box.setWindowTitle("Information MessageBox")
            msg_box.setStandardButtons(QMessageBox.Ok)
            retval = msg_box.exec_()


if __name__ == "__main__":
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec_())
