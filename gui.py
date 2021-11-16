import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilenames
from tkinter.filedialog import asksaveasfilename
from tkinter.filedialog import askdirectory
from tkinter import messagebox
import pandas as pd
import os
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('TkAgg')
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
from detectPeaks import detectPeaks
from automated_recalibration import automated_recal
from baseline_correction import baseline_correction
import csv

matplotlib.rcParams['savefig.dpi'] = 300


# --- classes ---
class SnaptoCursor:
    """
    Like Cursor but the crosshair snaps to the nearest x, y point.
    For simplicity, this assumes that *x* is sorted.
    """

    def __init__(self, ax, x, y, segments, linecolors, canvas):
        self.ax = ax
        self.x = x
        self.y = y
        self.canvas = canvas
        self.segments = segments
        self.linecolors = linecolors
        # text location in axes coords
        self.annot = ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                                 bbox=dict(boxstyle='round', fc='w', ec='k', lw=1))

    def mouse_move(self, event):
        if not event.inaxes:
            return
        x, y = event.xdata, event.ydata
        print(self.annot.xy)
        self.annot.xy = (x, y)
        text = "mass: {:.2f}, intensity: {:.2f}".format(x, y)
        self.annot.set_text(text)
        # self.annot.set_visible(True)
        self.canvas.draw()

    def on_click(self, event):
        if event.dblclick:
            if event.button == 1:
                x, y = event.xdata, event.ydata
                print(x, y)
                indx = min(np.searchsorted(self.x, x), len(self.x) - 1)
                self.linecolors[indx - 25:indx + 25] = ['lightgray' for i in self.linecolors[indx - 25:indx + 25]]
                self.lc = LineCollection(self.segments, colors=self.linecolors)
                self.ax.add_collection(self.lc)
                self.canvas.draw()

        else:
            if event.button == 3:
                x, y = event.xdata, event.ydata
                print(x, y)
                indx = min(np.searchsorted(self.x, x), len(self.x) - 1)
                self.linecolors[indx - 20:indx + 20] = ['red' for i in self.linecolors[indx - 20:indx + 20]]
                self.lc = LineCollection(self.segments, colors=self.linecolors)
                self.ax.add_collection(self.lc)
                self.canvas.draw()


class TextScrollCombo(ttk.Frame):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ensure a consistent GUI size
        self.grid_propagate(False)
        # implement stretchability
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # create a Text widget
        self.txt = tk.Text(self)
        self.txt.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # create a Scrollbar and associate it with txt
        scrollb = ttk.Scrollbar(self, command=self.txt.yview)
        scrollb.grid(row=0, column=1, sticky='nsew')
        self.txt['yscrollcommand'] = scrollb.set


class MyWindow:
    def __init__(self, parent):
        self.parent = parent
        self.data_dictionary = {}
        self.baseline_corrected_data = {}
        parent.title('LILBID Analysis')
        parent.geometry("750x250")
        self.box = tk.Listbox(self.parent)
        self.box.pack(side=tk.TOP, fill=tk.BOTH)
        self.temp_file = None

        # load data button
        self.load_button = tk.Button(self.parent, text='LOAD DATA', command=self.load)
        self.load_button.pack()

        self.open_file = tk.Button(self.parent, text='OPEN FILE', command=self.open_file)
        self.open_file.pack()

        self.baseline_correct_all = tk.Button(self.parent, text='BASELINE CORRECT ALL',
                                              command=self.baseline_correct_all)
        self.baseline_correct_all.pack()

        self.baseline_correct_recalibrate_all = tk.Button(self.parent, text='BASELINE CORRECT & RE-CALIBRATE ALL',
                                                          command=self.baseline_correct_recalibrate_all)
        self.baseline_correct_recalibrate_all.pack()

    def load(self):
        file_names = askopenfilenames(filetypes=[('TXT', '*.txt',)],
                                      initialdir='/home/umair/PycharmProjects/mass_spectro/5M_NaCl')
        self.files = list(file_names)
        self.box.delete(0, tk.END)
        self.data_dictionary.clear()
        for idx in self.files:
            file_name = os.path.basename(idx)
            self.box.insert(tk.END, file_name)
            self.data_dictionary[file_name] = {}
            self.data_dictionary[file_name]['original_data'] = np.loadtxt(idx)
            self.data_dictionary[file_name]['file_path'] = os.path.dirname(idx)
        self.box.pack()

    def open_file(self):
        if self.box.size() == 0:
            messagebox.showinfo(title='Message Box', message='Load data first')
            self.load()
        else:
            selected = self.box.curselection()
            if len(selected) == 0:
                print('Select the file to open')
                msgbox = messagebox.askokcancel(title='Message Box', message='Select the file to open', icon='warning')
            else:
                top = tk.Toplevel()
                file_name = self.box.get(selected[0])
                top.title(file_name)
                file_path = os.path.join(self.data_dictionary[file_name]['file_path'], file_name)

                text = TextScrollCombo(top)
                with open(file_path, 'r') as raw_text_file:
                    raw_text_matter = raw_text_file.read()
                text.txt.insert(tk.END, raw_text_matter)
                text.pack(fill="both", expand=True)
                text.config(width=600, height=300)

                text.txt.config(state='disabled')

                style = ttk.Style()
                style.theme_use('clam')

                close = tk.Button(top, text="CLOSE", command=top.destroy)
                close.pack()

                plot = tk.Menubutton(top, text="PLOT")
                plot_menu = tk.Menu(plot)
                plot.config(menu=plot_menu)
                plot.pack()

                btnList = ['Original', 'Re-calibrated', 'Baseline Corrected & Re-calibrated', 'All']
                for btn in btnList:
                    plot_menu.add_command(label=btn, command=lambda btn=btn: self.button_clicked(btn, file_name))

                single_bc = tk.Button(top, text="BASELINE CORRECT",
                                      command=lambda: self.baseline_correct_save(file_name))
                single_bc.pack()
                single_bc_recal = tk.Button(top, text="BASELINE CORRECT & RE-CALIBRATE",
                                            command=lambda: self.baseline_correct_recalibrate_save(file_name))
                single_bc_recal.pack()

                analyse_spectrum = tk.Button(top, text="ANALYSE", command=lambda: self.analyse_spectrum(file_name))
                analyse_spectrum.pack()

    def button_clicked(self, btn, file_name):
        new = tk.Toplevel()
        new.title(file_name)
        if btn == 'Original':
            x, y = self.data_dictionary[file_name]['original_data'][:, 0], self.data_dictionary[file_name][
                                                                               'original_data'][:, 1]
            fig = Figure(dpi=300)
            a = fig.add_subplot(111)
            a.set_title(btn, fontsize=6)
            a.set_ylabel("intensity [a.u.]", fontsize=4)
            a.set_xlabel(u"mass [\u03bc]", fontsize=4)
            a.set_yscale('log')
            a.tick_params(axis='both', which='both', labelsize=4)
            a.plot(x, y, 'black', linewidth=0.5)

        elif btn == 'Re-calibrated':
            if 'recalibrated_data' not in self.data_dictionary[file_name]:
                self.baseline_correct_recalibrate(file_name)

            x_r, y_r = self.data_dictionary[file_name]['recalibrated_data'][:, 0], self.data_dictionary[file_name][
                                                                                       'recalibrated_data'][:, 1]
            fig = Figure(dpi=300)
            a = fig.add_subplot(111)
            a.set_title(btn, fontsize=6)
            a.set_ylabel("intensity [a.u.]", fontsize=4)
            a.set_xlabel(u"mass [\u03bc]", fontsize=4)
            a.set_yscale('log')
            a.tick_params(axis='both', which='both', labelsize=4)
            a.plot(x_r, y_r, 'black', linewidth=0.5)

        elif btn == 'Baseline Corrected & Re-calibrated':
            if 'recalibrated_data' not in self.data_dictionary[file_name]:
                self.baseline_correct_recalibrate(file_name)

            x_b, y_b = self.data_dictionary[file_name]['baseline_corrected_data'][:, 0], \
                       self.data_dictionary[file_name]['baseline_corrected_data'][:, 1]
            x_r, y_r = self.data_dictionary[file_name]['recalibrated_data'][:, 0], self.data_dictionary[file_name][
                                                                                       'recalibrated_data'][:, 1]
            fig = Figure(dpi=300)
            a = fig.add_subplot(111)
            a.set_title(btn, fontsize=6)
            a.set_ylabel("intensity [a.u.]", fontsize=4)
            a.set_xlabel(u"mass [\u03bc]", fontsize=4)
            a.set_yscale('log')
            a.tick_params(axis='both', which='both', labelsize=4)
            a.plot(x_b, y_b, 'black', linewidth=0.5, label='baseline corrected')
            a.plot(x_r, y_r, 'red', linewidth=0.5, label='baseline corrected & Re-calibrated')
            a.legend(prop={'size': 4})


        elif btn == 'All':
            if 'baseline_corrected_data' not in self.data_dictionary[file_name]:
                self.baseline_correct(file_name)

            if 'recalibrated_data' not in self.data_dictionary[file_name]:
                self.baseline_correct_recalibrate(file_name)

            x, y = self.data_dictionary[file_name]['original_data'][:, 0], self.data_dictionary[file_name][
                                                                               'original_data'][:, 1]
            x_b, y_b = self.data_dictionary[file_name]['baseline_corrected_data'][:, 0], \
                       self.data_dictionary[file_name]['baseline_corrected_data'][:, 1]
            x_r, y_r = self.data_dictionary[file_name]['recalibrated_data'][:, 0], self.data_dictionary[file_name][
                                                                                       'recalibrated_data'][:, 1]
            fig = Figure(dpi=300)
            a = fig.add_subplot(311)
            a.set_title('Original', fontsize=4)
            a.set_ylabel("intensity [a.u.]", fontsize=3)
            a.set_xlabel(u"mass [\u03bc]", fontsize=3)
            a.set_yscale('log')
            a.tick_params(axis='both', which='both', labelsize=3)
            a.plot(x, y, 'black', linewidth=0.5)
            b = fig.add_subplot(312)
            b.set_title("Baseline corrected and Re-calibrated", fontsize=4)
            b.set_ylabel("intensity [a.u.]", fontsize=3)
            b.set_xlabel(u"mass [\u03bc]", fontsize=3)
            b.set_yscale('log')
            b.tick_params(axis='both', which='both', labelsize=3)
            b.plot(x_r, y_r, 'black', linewidth=0.5)
            c = fig.add_subplot(313)
            c.set_title("Comparison", fontsize=4)
            c.set_ylabel("intensity [a.u.]", fontsize=3)
            c.set_xlabel(u"mass [\u03bc]", fontsize=3)
            c.set_yscale('log')
            c.tick_params(axis='both', which='both', labelsize=3)
            c.plot(x, y, 'black', linewidth=0.5, label='original')
            c.plot(x_r, y_r, 'red', linewidth=0.5, label='re-calibrated')
            c.legend(prop={'size': 3})
            fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=new)  # A tk.DrawingArea.
        canvas.draw()
        # canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, new)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def baseline_correct_all(self):
        dir_name = askdirectory()
        for idx in self.files:
            with open(idx, 'r') as raw:
                text = raw.readlines()[0:20]
            file_name = os.path.basename(idx)
            self.data_dictionary[file_name]['baseline_corrected_data'] = baseline_correction(
                self.data_dictionary[file_name]['original_data'])
            baseline_corrected_file_name = os.path.join(dir_name, file_name[:-4] + '_baseline_corrected.txt')
            np.savetxt(baseline_corrected_file_name, self.data_dictionary[file_name]['baseline_corrected_data'],
                       fmt='%.8f', header=''.join(text)[:-1], comments='', delimiter='\t')
        messagebox.showinfo(title='Message Box', message='Baseline correction successful')

    # check function::
    def baseline_correct_recalibrate_all(self):
        dir_name = askdirectory()
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
        messagebox.showinfo(title='Message Box', message='Recalibration successful')
        if recheck_files:
            messagebox.showinfo(title='Message Box',
                                message='Manually check the recalibration for the following files:\n' + '\n'.join(
                                    recheck_files))

    def baseline_correct_save(self, file_name):
        msgbox = messagebox.askokcancel(title='Message Box', message='Do you want to save the baseline corrected data?',
                                        icon='warning')
        if 'baseline_corrected_data' not in self.data_dictionary[file_name]:
            self.baseline_correct(file_name)
        file_path = os.path.join(self.data_dictionary[file_name]['file_path'], file_name)
        if msgbox:
            with open(file_path, 'r') as raw:
                text = raw.readlines()[0:20]
            dir_name = askdirectory()
            baseline_corrected_file_name = os.path.join(dir_name, file_name[:-4] + '_baseline_corrected.txt')
            np.savetxt(baseline_corrected_file_name, self.data_dictionary[file_name]['baseline_corrected_data'],
                       fmt='%.8f', header=''.join(text)[:-1], comments='', delimiter='\t')

    def baseline_correct_recalibrate_save(self, file_name):
        msgbox = messagebox.askokcancel(title='Message Box',
                                        message='Do you want to save the baseline corrected and re-calibrated data?',
                                        icon='warning')
        if 'recalibrated_data' not in self.data_dictionary[file_name]:
            self.baseline_correct_recalibrate(file_name)
        file_path = os.path.join(self.data_dictionary[file_name]['file_path'], file_name)
        if msgbox:
            with open(file_path, 'r') as raw:
                text = raw.readlines()[0:20]
            dir_name = askdirectory()
            recalibrated_file_name = os.path.join(dir_name, file_name[:-4] + '_recalibrated.txt')
            np.savetxt(recalibrated_file_name, self.data_dictionary[file_name]['recalibrated_data'], fmt='%.8f',
                       header=''.join(text)[:-1], comments='', delimiter='\t')

    def baseline_correct_recalibrate(self, file_name):
        self.data_dictionary[file_name]['baseline_corrected_data'] = baseline_correction(
            self.data_dictionary[file_name]['original_data'])
        self.data_dictionary[file_name]['recalibrated_data'], self.data_dictionary[file_name][
            'manual_check'] = automated_recal(file_name, self.data_dictionary[file_name]['baseline_corrected_data'])
        if self.data_dictionary[file_name]['manual_check']:
            messagebox.showinfo(title='Message Box', message='Manually check the recalibration for ' + file_name)

    def baseline_correct(self, file_name):
        self.data_dictionary[file_name]['baseline_corrected_data'] = baseline_correction(
            self.data_dictionary[file_name]['original_data'])

    def analyse_spectrum(self, file_name):
        new = tk.Toplevel()
        new.title(file_name)
        new.geometry("720x500")
        x, y = self.data_dictionary[file_name]['original_data'][:, 0], self.data_dictionary[file_name]['original_data'][
                                                                       :, 1]
        fig = Figure(dpi=300)
        fig_subplot = fig.add_subplot(111)
        annot = fig_subplot.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points", size=4,
                                     bbox=dict(boxstyle='round', fc='w', ec='k', lw=1))

        fig_subplot.set_ylabel("intensity [a.u.]", fontsize=4)
        fig_subplot.set_xlabel(u"mass [\u03bc]", fontsize=4)
        fig_subplot.set_yscale('log')
        fig_subplot.tick_params(axis='both', which='both', labelsize=4)
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        linecolors = ['k'] * len(x)
        lc = LineCollection(segments, colors=linecolors, linewidths=0.5)
        fig_subplot.add_collection(lc)
        fig_subplot.set_xlim(x.min(), x.max())
        fig_subplot.set_ylim(y.min(), y.max() * 3)
        analysis_canvas = FigureCanvasTkAgg(fig, master=new)

        label_peaks_button = tk.Button(new, text='Label Peaks',
                                       command=lambda: self.label_peaks(file_name, fig_subplot, lc, analysis_canvas))
        label_peaks_button.pack()  # A tk.DrawingArea.

        reset_peaks_selection = tk.Button(new, text='Reset peaks selection',
                                          command=lambda: self.reset_canvas(linecolors, analysis_canvas, lc,
                                                                            fig_subplot))
        reset_peaks_selection.pack()

        snap_cursor = SnaptoCursor(fig_subplot, x, y, segments, linecolors, analysis_canvas)
        analysis_canvas.mpl_connect('motion_notify_event',
                                    lambda event: self.mouse_move(event, x, y, annot, analysis_canvas))
        """
        analysis_canvas.mpl_connect('button_press_event',
                                    lambda event: self.on_click(event, x, y, linecolors, analysis_canvas, lc,
                                                             fig_subplot))
        """
        toolbar = NavigationToolbar2Tk(analysis_canvas, new)
        toolbar.update()
        analysis_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def mouse_move(self, event, x, y, annot, canvas):
        if not event.inaxes:
            return
        x_point, y_point = event.xdata, event.ydata
        indx = min(np.searchsorted(x, x_point), len(x) - 1)
        x_point = x[indx]
        y_point = y[indx]
        annot.xy = (x_point, y_point)
        text = "mass: {:.2f}, intensity: {:.2f}".format(x_point, y_point)
        annot.set_text(text)
        # self.annot.set_visible(True)
        canvas.draw()

    def on_click(self, event, x, y, linecolors, canvas, lc, subplot):
        if event.dblclick:
            if event.button == 1:
                x_point, y_point = event.xdata, event.ydata
                indx = min(np.searchsorted(x, x_point), len(x) - 1)
                peak_index = np.argmax(y[indx - 100:indx + 100])
                peak_index = np.arange(len(x))[indx - 100:indx + 100][peak_index]
                linecolors[peak_index - 25:peak_index + 25] = ['lightgray' for i in
                                                               linecolors[peak_index - 25:peak_index + 25]]
                lc.set_color(linecolors)
                canvas.draw()

        else:
            if event.button == 3:
                x_point, y_point = event.xdata, event.ydata
                indx = min(np.searchsorted(x, x_point), len(x) - 1)
                peak_index = np.argmax(y[indx - 100:indx + 100])
                peak_index = np.arange(len(x))[indx - 100:indx + 100][peak_index]
                linecolors[peak_index - 25:peak_index + 25] = ['red' for i in
                                                               linecolors[peak_index - 25:peak_index + 25]]
                lc.set_color(linecolors)
                label = "{:.2f}".format(x[peak_index])
                subplot.plot(x[peak_index], y[peak_index], 'bx', linewidth=0.5, markersize=3)
                subplot.annotate(label,  # this is the text
                                 (x[peak_index], y[peak_index]),  # these are the coordinates to position the label
                                 textcoords="offset points",  # how to position the text
                                 xytext=(0, 5),  # distance from text to points (x,y)
                                 ha='center',
                                 fontsize=3, color='r', rotation=90)
                canvas.draw()
    """
    def reset_canvas(self, linecolors, canvas, lc, subplot):
        linecolors = ['k'] * len(linecolors)
        lc.set_color(linecolors)
        canvas.draw()
    """
    def detect_peaks(self, file_name):
        if 'recalibrated_data' not in self.data_dictionary[file_name]:
            self.baseline_correct_recalibrate(file_name)
        self.data_dictionary[file_name]['peaks'], _, _ = detectPeaks(
            self.data_dictionary[file_name]['recalibrated_data'])

    def label_peaks(self, file_name, fig_subplot, lc, canvas):
        if 'peaks' not in self.data_dictionary[file_name]:
            self.detect_peaks(file_name)
        x, y = self.data_dictionary[file_name]['recalibrated_data'][:, 0], self.data_dictionary[file_name][
                                                                               'recalibrated_data'][:, 1]
        points = np.array([x, y]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        lc.set_segments(segments)
        peak_data = self.data_dictionary[file_name]['peaks']
        fig_subplot.plot(peak_data[:, 0], peak_data[:, 1], 'bx', linewidth=0.5, markersize=3)
        fig_subplot.set_xlim(x.min(), x.max())
        fig_subplot.set_ylim(y.min(), y.max() * 3)
        for j, k in zip(peak_data[:, 0], peak_data[:, 1]):
            label = "{:.2f}".format(j)
            fig_subplot.annotate(label,  # this is the text
                                 (j, k),  # these are the coordinates to position the label
                                 textcoords="offset points",  # how to position the text
                                 xytext=(0, 5),  # distance from text to points (x,y)
                                 ha='center',
                                 fontsize=3, color='r',
                                 rotation=90)  # horizontal alignment can be left, right or center

        canvas.draw()


# --- main ---

if __name__ == '__main__':
    root = tk.Tk()
    top = MyWindow(root)
    root.mainloop()
