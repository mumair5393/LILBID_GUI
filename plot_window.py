import pyqtgraph as pg
pg.setConfigOption('background', 'w')
from PyQt5.QtWidgets import *
from plot_ui import Ui_Plot

class Plot_All_Graphs(QWidget, Ui_Plot):
    def __init__(self, file_name, data_dictionary, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.file_name = file_name
        self.setWindowTitle(self.file_name)
        self.data_dictionary = data_dictionary
        self.data = self.data_dictionary[file_name]['original_data']
        self.bc_recal_data = self.data_dictionary[file_name]['recalibrated_data']

        self.p1 = self.plotting(self.graphicsView, type="Original")
        self.p2 = self.plotting(self.graphicsView_2, type="Re-calibrated")
        self.p3 = self.plotting(self.graphicsView_3, type="Both")


    def plotting(self, graphicsview, type="Original"):
        c = []
        p1 = graphicsview.addPlot(ignoreBounds=True)
        p1.setLogMode(False, True)
        if type == "Original":
            c.append(p1.plot(self.data, pen='k'))
        elif type == "Re-calibrated":
            c.append(p1.plot(self.bc_recal_data, pen='k'))
        elif type == "Both":
            c.append(p1.plot(self.data, pen='k'))
            c.append(p1.plot(self.bc_recal_data, pen='r'))
        return p1
