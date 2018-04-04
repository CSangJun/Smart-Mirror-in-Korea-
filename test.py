from tkinter import *
import time
from contextlib import contextmanager

time_format = 12

class clock:
	    def __init__(self, parent, *args, **kwargs):
 	    	Frame.__init__(self, parent, bg='black')
        
        	self.time1 = ''
        	self.timeLbl = Label(self, font=('Helvetica', large_text_size), fg="white", bg="black")
        	self.timeLbl.pack(side=TOP, anchor=E)
	        
        	self.day_of_week1 = ''
        	self.dayOWLbl = Label(self, text=self.day_of_week1, font=('Helvetica', small_text_size), fg="white", bg="black")
        	self.dayOWLbl.pack(side=TOP, anchor=E)
	        
        	self.date1 = ''
        	self.dateLbl = Label(self, text=self.date1, font=('Helvetica', small_text_size), fg="white", bg="black")
        	self.dateLbl.pack(side=TOP, anchor=E)
        	self.tick()
        def tick(self):
        	with setlocale():
        		if time_format == 12:
        			time2 = time.strftime('%I:%M %p')
        		else:
        			time2 = time.strftime('%H:%M')

        			

class mainWindow:
	def __init__(self):
		self.tk = Tk()
		self.tk.configure(background='black')
		self.topFrame = Frame(self.tk, background='black')
		self.topFrame.pack(side=TOP, fill = BOTH, expand = YES)

		self.clock = clock(self.topFrame);
		self.clock.pack(side=RIGHT, anchor=N, padx=100, pady=60)