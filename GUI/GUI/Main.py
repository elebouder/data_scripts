from Tkinter import *
from PIL import Image, ImageTk
import query_handler as qh

""" Short GUI script for classification of training sites.  The GUI assigns one of three classes to
each site <Yes, No, Don't Know>.  The sites themselves are stored in a file db, currently
U:/Fracking Pads/trialtrainingrasters.

Every raster clip in said db is named with the following convention:
<sceneID>_<site number within that scene>_<class>.tif.  Class numbers are assigned as:
Not Yet Classified: 5
Is not a Site: 0
Is a Site: 1
Don't Know what class: 2

With every class assignment made, both the raster name in the file db and a PostgreSQL server with raster info
is updated with the new class assignment.  Assignment is handled by query_handler.py

Upon initialization, program searches filedb and generates array of raster names that haven't yet been assigned. This is
stored in the class variable 'array' and the image that gets displayed is always array[0].  When a new image needs to
be shown, the first elem in array is popped and array[0] now refers to a new raster ds.

NOTE: There is currently a bug in the code regarding canvas.bbox() in Main.py in App.display_nextIMG().  It is currently
stable and does not affect GUI function.  Do not attempt to fix until the issues with Canvas update are resolved."""

# TODO alter array[0] and array.pop system to array iteration sys, to keep reference to already classified sites
# TODO with new array sys add ability to go back and reassign site from GUI

class App(Frame):

    array = []
    path = 'U:/Fracking Pads/Training Data/Unclassified'
    path2 = 'U:/Fracking Pads/Training Data/Classified'
    array_index = 0
    imcanvas = None
    num_classed = 0
    num_tbclassed = 0
    last_assignment = 5

    # Initialize parent frame, buttons, some class fields

    def __init__(self, master=None):
        Frame.__init__(self, master)

        self.bind("<Return>", self.imgdisplay)
        self.pack()

        self.ybutton = Button(self)
        self.ybutton['text'] = 'Yes'
        self.ybutton['background'] = 'green'
        self.ybutton.bind("<Button-1>", self.bind_assignY)
        self.ybutton.pack(side='left', padx=10, ipadx=10, ipady=5, anchor=S)

        self.nbutton = Button(self)
        self.nbutton['text'] = 'No'
        self.nbutton['background'] = 'red'
        self.nbutton.bind("<Button-1>", self.bind_assignN)
        self.nbutton.pack(side='right', padx=10, ipadx=10, ipady=5, anchor=S)

        self.unkwnbutton = Button(self)
        self.unkwnbutton['text'] = "Don't know"
        self.unkwnbutton['background'] = 'yellow'
        self.unkwnbutton.bind("<Button-1>", self.bind_assignDK)
        self.unkwnbutton.pack(side='bottom', pady=10, ipadx=10, ipady=5, anchor=N)


        self.initbutton = Button(self)
        self.initbutton['text'] = 'Confirm Choice'
        self.initbutton['background'] = 'black'
        self.initbutton['foreground'] = 'white'
        self.initbutton.bind("<Button-1>", self.imgdisplay)
        self.initbutton.pack(side='top', anchor=S)


        self.array = qh.list_tbClassified(self.path)
        self.num_tbclassed = self.array.__len__()
        self.imtk = None
        self.imagerep = None
        #self.create_childWin()

    # Not currently in use: child window thru TopLevel that displays classification progress.  Needs to be initialized
    # in App.__init__() at final line

    """def create_childWin(self):
        t = Toplevel(self)
        t.wm_title("Progress Tracker")
        l = Label(t, text="Classed: %s, tbClassed: %s" % (self.num_classed, self.num_tbclassed))
        l.pack(fill="both", expand=True, padx=50, pady=30)"""

    # Handles assignment of class when Yes button is clicked

    def bind_assignY(self, event):
        imgname = self.array[self.array_index]
        qh.assignClass2SQL(imgname, 1)
        qh.assignClass2file(self.path, self.path2, imgname, 1, self.last_assignment)
        self.last_assignment = 1

    # Handles assignment of class when No button is clicked

    def bind_assignN(self, event):
        imgname = self.array[self.array_index]
        qh.assignClass2SQL(imgname, 0)
        qh.assignClass2file(self.path, self.path2, imgname, 0, self.last_assignment)
        self.last_assignment = 0

    # Handles assignment of class when Don't Know button is clicked

    def bind_assignDK(self, event):
        imgname = self.array[self.array_index]
        qh.assignClass2SQL(imgname, 2)
        qh.assignClass2file(self.path, self.path2, imgname, 2, self.last_assignment)
        self.last_assignment = 2

    """ App.imgdisplay() handles creation and calls to update the image canvas.  Is called every time the
    black Confirm Choice button is clicked.

    -Updates class fields num_classed and num_tbclassed that keep track of
    how many assignments have been made/are left in the file db.  If more than one has been made, generates call to
    display_nextIMG to update the contents of the image canvas"""

    def imgdisplay(self, event):
        if self.num_classed > 0:
            self.display_nextIMG()
        imgname = self.array[self.array_index]
        self.displayIMG(imgname)
        self.imcanvas = Canvas(self, width=700, height=700)
        self.imcanvas.pack()
        self.imagerep = self.imcanvas.create_image(400, 400, anchor=CENTER, image=self.imtk)
        self.num_classed += 1
        self.num_tbclassed -= 1

    """display_nextIMG is called from imgdisplay.  Handles the update of the image displayed in the widget canvas once
    a class assignment has been confirmed by the user.  Updates num_classed and num_tbclassed.

    Involves a call to displayIMG with a pathname from array[0] to open that raster and convert to tk-friendly form.

    NOTE: There is currently a bug in the self.imcanvas.bbox line that could be fixed by passing self.imagerep as an arg.
    However, this bug is stable and does not affect processing, while suppressing another bug that fails to update the image
    canvase appropriately.  NEEDS TO BE FIXED"""

    #TODO fix image canvas update bug

    def display_nextIMG(self):
        self.array_index += 1
        imgname = self.array[self.array_index]
        self.displayIMG(imgname)
        self.imcanvas.itemconfig(self.imagerep, image=self.imtk)
        bounds = self.imcanvas.bbox()  # returns a tuple like (x1, y1, x2, y2)
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        print width, height
        self.num_classed += 1
        self.num_tbclassed -= 1

    # Opens raster in file db and converts to tk-friendly format, assigns to class field imtk

    def displayIMG(self, imgname):
        im = Image.open(self.path + '/' + imgname)
        im = im.point(lambda p: p * 1)
        im = im.resize((700, 700))
        self.imtk = ImageTk.PhotoImage(im, self)




def main():

    traintool = App()
    traintool.master.title("Assign Class")
    traintool.master.minsize(1000, 800)
    traintool.master.maxsize(1200, 1000)
    traintool.mainloop()




if __name__ == '__main__':
    main()

