
import Tkinter
basedataset = 'U:/Fracking Pads/trialtrainingrasters'

import Image
import ImageTk
import numpy

im=Image.open(basedataset + '/' + 'LC80490212015211LGN00_4.tif')
root=Tkinter.Tk()
imtk=ImageTk.PhotoImage(im, root)
Tkinter.Label(root, image=imtk).pack()
