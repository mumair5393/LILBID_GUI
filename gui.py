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
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
from detectPeaks import detectPeaks
from automated_recalibration import automated_recal
from baseline_correction import baseline_correction
import csv
matplotlib.rcParams['savefig.dpi'] = 300

# --- classes ---

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
        self.box.pack(side = tk.TOP, fill = tk.BOTH)
        self.temp_file = None
        
        # load data button
        self.load_button = tk.Button(self.parent, text='LOAD DATA', command=self.load)
        self.load_button.pack()
        
        self.open_file = tk.Button(self.parent, text='OPEN FILE', command=self.open_file)
        self.open_file.pack()
        
        self.baseline_correct_all = tk.Button(self.parent, text='BASELINE CORRECT ALL', command=self.baseline_correct_all)
        self.baseline_correct_all.pack()
        
        self.baseline_correct_recalibrate_all = tk.Button(self.parent, text='BASELINE CORRECT & RE-CALIBRATE ALL', command=self.baseline_correct_recalibrate_all)
        self.baseline_correct_recalibrate_all.pack()
        
    def load(self):
        file_names = askopenfilenames(filetypes=[('TXT', '*.txt',)],)
        self.files = list(file_names)
        self.box.delete(0,tk.END)
        self.data_dictionary.clear()
        for idx in self.files:
            file_name = os.path.basename(idx)
            self.box.insert(tk.END, file_name)
            self.data_dictionary[file_name] = {}
            self.data_dictionary[file_name]['original_data']=np.loadtxt(idx)
            self.data_dictionary[file_name]['file_path']=os.path.dirname(idx)
        self.box.pack()
        
    def open_file(self):
        if self.box.size() == 0:
            messagebox.showinfo(title='Message Box', message='Load data first')
            self.load()
        else:
            selected=self.box.curselection()
            if len(selected) == 0:
                print('Select the file to open')
                msgbox = messagebox.askokcancel (title='Message Box', message='Select the file to open',icon = 'warning')
            else:
                top = tk.Toplevel()
                file_name= self.box.get(selected[0])
                top.title(file_name)
                file_path = os.path.join(self.data_dictionary[file_name]['file_path'],file_name)


                text = TextScrollCombo(top)
                with open(file_path, 'r') as raw_text_file:
                    raw_text_matter = raw_text_file.read()
                text.txt.insert(tk.END,raw_text_matter)
                text.pack(fill="both", expand=True)
                text.config(width=600, height=300)

                text.txt.config(state='disabled')

                style = ttk.Style()
                style.theme_use('clam')

                close = tk.Button(top, text="CLOSE", command = top.destroy)
                close.pack()

                plot = tk.Menubutton(top, text="PLOT")
                plot_menu = tk.Menu(plot)
                plot.config(menu=plot_menu)
                plot.pack()

                btnList = ['Original', 'Re-calibrated', 'Baseline Corrected & Re-calibrated', 'All']
                for btn in btnList:
                    plot_menu.add_command(label=btn, command = lambda btn=btn: self.button_clicked(btn, file_name))

                single_bc = tk.Button(top, text="BASELINE CORRECT", command = lambda: self.baseline_correct_save(file_name))
                single_bc.pack()
                single_bc_recal = tk.Button(top, text="BASELINE CORRECT & RE-CALIBRATE", command = lambda: self.baseline_correct_recalibrate_save(file_name))
                single_bc_recal.pack()

        
    def button_clicked(self,btn, file_name):
        new=tk.Toplevel()
        new.title(file_name)
        if btn == 'Original':
            x, y = self.data_dictionary[file_name]['original_data'][:,0],self.data_dictionary[file_name]['original_data'][:,1]
            fig = Figure(dpi=300)
            a = fig.add_subplot(111)
            a.set_title(btn, fontsize=6)
            a.set_ylabel("intensity [a.u.]", fontsize=4)
            a.set_xlabel(u"mass [\u03bc]", fontsize=4)
            a.set_yscale('log')
            a.tick_params(axis='both', which='both', labelsize=4)
            a.plot(x,y,'black', linewidth=0.5)
            
        elif btn == 'Re-calibrated':
            if 'recalibrated_data' not in self.data_dictionary[file_name]:
                self.baseline_correct_recalibrate(file_name)
            
            x_r, y_r = self.data_dictionary[file_name]['recalibrated_data'][:,0],self.data_dictionary[file_name]['recalibrated_data'][:,1]
            fig = Figure(dpi=300)
            a = fig.add_subplot(111)
            a.set_title(btn, fontsize=6)
            a.set_ylabel("intensity [a.u.]", fontsize=4)
            a.set_xlabel(u"mass [\u03bc]", fontsize=4)
            a.set_yscale('log')
            a.tick_params(axis='both', which='both', labelsize=4)
            a.plot(x_r,y_r,'black', linewidth=0.5)
            
        elif btn == 'Baseline Corrected & Re-calibrated':
            if 'recalibrated_data' not in self.data_dictionary[file_name]:
                self.baseline_correct_recalibrate(file_name)
                
            x_b, y_b = self.data_dictionary[file_name]['baseline_corrected_data'][:,0],self.data_dictionary[file_name]['baseline_corrected_data'][:,1]
            x_r, y_r = self.data_dictionary[file_name]['recalibrated_data'][:,0],self.data_dictionary[file_name]['recalibrated_data'][:,1]
            fig = Figure(dpi=300)
            a = fig.add_subplot(111)
            a.set_title(btn, fontsize=6)
            a.set_ylabel("intensity [a.u.]", fontsize=4)
            a.set_xlabel(u"mass [\u03bc]", fontsize=4)
            a.set_yscale('log')
            a.tick_params(axis='both', which='both', labelsize=4)
            a.plot(x_b,y_b,'black', linewidth=0.5, label='baseline corrected')
            a.plot(x_r,y_r,'red', linewidth=0.5, label='baseline corrected & Re-calibrated')
            a.legend(prop={'size': 4})
        
        
        elif btn == 'All':
            if 'baseline_corrected_data' not in self.data_dictionary[file_name]:
                self.baseline_correct(file_name)
            
            if 'recalibrated_data' not in self.data_dictionary[file_name]:
                self.baseline_correct_recalibrate(file_name)
            
            x, y = self.data_dictionary[file_name]['original_data'][:,0],self.data_dictionary[file_name]['original_data'][:,1]
            x_b, y_b = self.data_dictionary[file_name]['baseline_corrected_data'][:,0],self.data_dictionary[file_name]['baseline_corrected_data'][:,1]
            x_r, y_r = self.data_dictionary[file_name]['recalibrated_data'][:,0],self.data_dictionary[file_name]['recalibrated_data'][:,1]
            fig = Figure(dpi=300)
            a = fig.add_subplot(311)
            a.set_title('Original', fontsize=4)
            a.set_ylabel("intensity [a.u.]", fontsize=3)
            a.set_xlabel(u"mass [\u03bc]", fontsize=3)
            a.set_yscale('log')
            a.tick_params(axis='both', which='both', labelsize=3)
            a.plot(x,y,'black', linewidth=0.5)
            b = fig.add_subplot(312)
            b.set_title("Baseline corrected and Re-calibrated", fontsize=4)
            b.set_ylabel("intensity [a.u.]", fontsize=3)
            b.set_xlabel(u"mass [\u03bc]", fontsize=3)
            b.set_yscale('log')
            b.tick_params(axis='both', which='both', labelsize=3)
            b.plot(x_r,y_r,'black', linewidth=0.5)
            c = fig.add_subplot(313)
            c.set_title("Comparison", fontsize=4)
            c.set_ylabel("intensity [a.u.]", fontsize=3)
            c.set_xlabel(u"mass [\u03bc]", fontsize=3)
            c.set_yscale('log')
            c.tick_params(axis='both', which='both', labelsize=3)
            c.plot(x,y,'black', linewidth=0.5, label='original')
            c.plot(x_r,y_r,'red', linewidth=0.5, label='re-calibrated')
            c.legend(prop={'size': 3})
            fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=new)  # A tk.DrawingArea.
        canvas.draw()
        #canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        toolbar = NavigationToolbar2Tk(canvas, new)
        toolbar.update()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        
    def baseline_correct_all(self):
        dir_name = askdirectory()
        for idx in self.files:
            with open(idx, 'r') as raw:
                text=raw.readlines()[0:20]
            file_name = os.path.basename(idx)
            self.data_dictionary[file_name]['baseline_corrected_data']=baseline_correction(self.data_dictionary[file_name]['original_data'])
            baseline_corrected_file_name = os.path.join(dir_name,file_name[:-4]+'_baseline_corrected.txt')
            np.savetxt(baseline_corrected_file_name, self.data_dictionary[file_name]['baseline_corrected_data'], fmt='%.8f', header=''.join(text)[:-1], comments='', delimiter='\t')
        messagebox.showinfo(title='Message Box', message='Baseline correction successful')
        
    # check function::
    def baseline_correct_recalibrate_all(self):
        dir_name = askdirectory()
        recheck_files = []
        for idx in self.files:
            with open(idx, 'r') as raw:
                text=raw.readlines()[0:20]
            file_name = os.path.basename(idx)
            print(file_name)
            self.data_dictionary[file_name]['baseline_corrected_data']=baseline_correction(self.data_dictionary[file_name]['original_data'])
            self.data_dictionary[file_name]['recalibrated_data'], self.data_dictionary[file_name]['manual_check']=automated_recal(file_name,self.data_dictionary[file_name]['baseline_corrected_data'])
            if self.data_dictionary[file_name]['manual_check']:
                recheck_files.append(file_name)
            recalibrated_file_name = os.path.join(dir_name,file_name[:-4]+'_recalibrated.txt')
            np.savetxt(recalibrated_file_name, self.data_dictionary[file_name]['recalibrated_data'], fmt='%.8f', header=''.join(text)[:-1], comments='', delimiter='\t')
        messagebox.showinfo(title='Message Box', message='Recalibration successful')
        messagebox.showinfo(title='Message Box', message='Manually check the recalibration for the following files:\n'+ '\n'.join(recheck_files))

        
    def baseline_correct_save(self, file_name):
        msgbox = messagebox.askokcancel (title='Message Box', message='Do you want to save the baseline corrected data?',icon = 'warning')
        if 'baseline_corrected_data' not in self.data_dictionary[file_name]:
            self.baseline_correct(file_name)
        file_path = os.path.join(self.data_dictionary[file_name]['file_path'],file_name) 
        if msgbox:
            with open(file_path, 'r') as raw:
                text=raw.readlines()[0:20]
            dir_name = askdirectory()
            baseline_corrected_file_name = os.path.join(dir_name,file_name[:-4]+'_baseline_corrected.txt')
            np.savetxt(baseline_corrected_file_name, self.data_dictionary[file_name]['baseline_corrected_data'], fmt='%.8f', header=''.join(text)[:-1], comments='', delimiter='\t')
        
    def baseline_correct_recalibrate_save(self, file_name):
        msgbox = messagebox.askokcancel (title='Message Box', message='Do you want to save the baseline corrected and re-calibrated data?',icon = 'warning')
        if 'recalibrated_data' not in self.data_dictionary[file_name]:
            self.baseline_correct_recalibrate(file_name)
        file_path = os.path.join(self.data_dictionary[file_name]['file_path'],file_name)
        if msgbox:
            with open(file_path, 'r') as raw:
                text=raw.readlines()[0:20]
            dir_name = askdirectory()
            recalibrated_file_name = os.path.join(dir_name,file_name[:-4]+'_recalibrated.txt')
            np.savetxt(recalibrated_file_name, self.data_dictionary[file_name]['recalibrated_data'], fmt='%.8f', header=''.join(text)[:-1], comments='', delimiter='\t')

    def baseline_correct_recalibrate(self, file_name):
        self.data_dictionary[file_name]['baseline_corrected_data']=baseline_correction(self.data_dictionary[file_name]['original_data'])
        self.data_dictionary[file_name]['recalibrated_data'], self.data_dictionary[file_name]['manual_check']=automated_recal(file_name,self.data_dictionary[file_name]['baseline_corrected_data'])
        if self.data_dictionary[file_name]['manual_check']:
            messagebox.showinfo(title='Message Box', message='Manually check the recalibration for '+ file_name)
    def baseline_correct(self, file_name):
        self.data_dictionary[file_name]['baseline_corrected_data']=baseline_correction(self.data_dictionary[file_name]['original_data'])
        
    
# --- main ---

if __name__ == '__main__':
    root = tk.Tk()
    top = MyWindow(root)
    root.mainloop()
