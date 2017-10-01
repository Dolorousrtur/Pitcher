from tkinter import Tk, Label, Entry, Button, PhotoImage, Canvas, mainloop, W
from PIL import ImageTk, Image
from speechprocessing import SttFactory, SttProcessor, RateMeasure, WordsCounter
from threading import Thread
from time import sleep, time
from process_json import Position, JsonReader

class MyGUI:
  def __init__(self):

      color = '#EDF0DA'

      self.__mainWindow = Tk()
      self.__mainWindow.configure(background=color)
      self.__mainWindow.geometry("550x450+500+300")
      self.__mainWindow.title("Pitcher")
      self.ratelabel = Label(self.__mainWindow, text = "", font="arial 11", background=color)
      self.ratelabel.place(x=165, y=390)

      self.countlabel = Label(self.__mainWindow, text = "w1: 2\nw2:3", font="arial 11", background=color)
      self.countlabel.place(x=360, y=70)

      self.rate = 0.0
      self.word_dict={'%hesitation': 0}
      self.last_frown = 0.0

      self.entrylabel = Label(self.__mainWindow, text="Enter words to count:", font="arial 11", background=color)
      self.entrylabel.place(x=20, y=10)


      self.crunchstring = "like, well, how do you say, you know, so, actually, i mean, basically"
      self.crunchentry = Entry(self.__mainWindow, width=30, background=color)
      self.crunchentry.insert(0, self.crunchstring)
      self.crunchentry.place(x=180, y=10)

      self.sratefrom = 80
      self.srateto = 240

      self.speechratelabel_from = Label(self.__mainWindow, text="Restrain speechrate from:", font="arial 11", background=color)
      self.speechratelabel_from.place(x=20, y=30)

      self.fromentry = Entry(self.__mainWindow, width=3, background=color)
      self.fromentry.insert(0, self.sratefrom)
      self.fromentry.place(x=200, y=30)

      self.speechratelabel_to = Label(self.__mainWindow, text="to:", font="arial 11", background=color)
      self.speechratelabel_to.place(x=230, y=30)

      self.toentry = Entry(self.__mainWindow, width=3, background=color)
      self.toentry.insert(0, self.srateto)
      self.toentry.place(x=250, y=30)

      self.canvas = Canvas(self.__mainWindow, width=330, height=330, background=color)
      self.canvas.place(x=10, y=60)
      imgood = Image.open('normal.png')
      imgood = imgood.resize((330, 330), Image.ANTIALIAS)
      self.imtkgood = ImageTk.PhotoImage(imgood)
      imbad = Image.open('irritated.png')
      imbad = imbad.resize((330, 330), Image.ANTIALIAS)
      self.imtkbad = ImageTk.PhotoImage(imbad)
      self.canvas.create_image(0, 0, image=self.imtkgood, anchor='nw')

      print(self.imtkgood.height())

      self.warninglabel = Label(self.__mainWindow, text="", font="arial 16", fg='red', background=color)
      self.warninglabel.place(x=230, y=410)

      self.lastwarn_text = ""
      self.lastwarn_ts = -5


      def upd_rate():
          self.ratelabel.config(text='Rate of speech: {0} words/min'.format(self.rate))


      def upd_counts():
          lines = ["{0}: {1}".format(w, self.word_dict[w]) for w in self.word_dict]
          text = '\n'.join(lines)
          self.countlabel.config(text=text)

      def upd_img():
          self.canvas.delete('all')
          if time() - self.lastwarn_ts < 1.5:
              self.canvas.create_image(0, 0, image=self.imtkbad, anchor='nw')
          else:
              self.canvas.create_image(0, 0, image=self.imtkgood, anchor='nw')

      def upd_warn():
          if time() - self.lastwarn_ts < 1.5:
              self.warninglabel.config(text=self.lastwarn_text)
          else:
              self.warninglabel.config(text="")

      def update():
          upd_rate()
          upd_counts()
          upd_img()
          upd_warn()
          self.__mainWindow.after(5, update)

      self.__mainWindow.after(5, update)

      def start_processing_audio():
          username = '0e6c2c4e-a491-4931-b380-b8a3b7b9c57f'
          password = 'r2NotzG5j4tY'

          def ratecallback(rate):
              if rate != 0.0:
                  if rate > self.srateto:
                      self.lastwarn_text = "Slow down!"
                      self.lastwarn_ts = time()
                  elif rate < self.sratefrom:
                      self.lastwarn_text = "Speed up!"
                      self.lastwarn_ts = time()
              self.rate=rate

          def countercallback(word_dict):
              self.word_dict = word_dict



          def crunchdetected_callback(word):
              if word == '%hesitation':
                word = 'HESITATION'
              else:
                  word = '"{0}"'.format(word)
              self.lastwarn_text = '{0} detected!'.format(word)
              self.lastwarn_ts = time()



          # crunch_string = self.crunchentry.get()
          crunch_string = self.crunchstring
          crunch_words = crunch_string.split(',')
          crunch_words = [w.strip() for w in crunch_words]
          # crunch_words.append('%hesitation')
          print(crunch_words)
          counter = WordsCounter(['%HESITATION'] + crunch_words, list_callback=countercallback, increment_callback=crunchdetected_callback)
          rm = RateMeasure(ratecallback)

          callbacks = [rm.process, counter.process]

          # self.rc = SttProcessor(username, password, callbacks=callbacks, wavfile='demo.wav')
          self.rc = SttProcessor(username, password, callbacks=callbacks)
          self.rc.start_recording()
          print("Button pressed")


          ratecallback(15.0)

      def start_processing_video():

          def openpose_cb(pos):
              print('openpose')
              if pos == Position.ROTATED:
                  self.lastwarn_text = "Turn back!"
                  self.lastwarn_ts = time()
              elif pos == Position.CLOSED:
                  self.lastwarn_text = "Closed pose!"
                  self.lastwarn_ts = time()
              elif pos == Position.POCKETS:
                  self.lastwarn_text = "Hands in pockets!"
                  self.lastwarn_ts = time()
              elif pos == Position.TOUCHING:
                  self.lastwarn_text = "Bad pose!"
                  self.lastwarn_ts = time()

          rdr = JsonReader('./output', callback=openpose_cb)
          rdr.startProcessing()

      def onStart():
          self.crunchstring = self.crunchentry.get()
          self.sratefrom = int(self.fromentry.get())
          self.srateto = int(self.toentry.get())
          t_audio = Thread(target=start_processing_audio)
          t_audio.start()
          # t_video = Thread(target=start_processing_video)
          # t_video.start()





      self.button = Button(self.__mainWindow, text="Start", command=onStart, font='arial 14', background=color)
      self.button.place(x=430, y=15)

      mainloop()

  def depositCallBack(self,event):
    self.labelText = 'change the value'
    print(self.labelText)


if __name__ == '__main__':
	myGUI = MyGUI()
