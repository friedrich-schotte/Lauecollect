"""
Generate a graphical logfile in PDF format,
containing charts, graphs and images using matplotlib

Usage:
import glogging as g
g.filename = directory+"/debug.pdf"
g.debug("matrix",X,"max 2D auto-correlation")
g.debug("images",V.reshape((N,w,h)),"positive base")

Author: Friedrich Schotte
Date created: 4/7/2017
Date last modified: 4/11/2017
"""
__version__ = "1.0"
import logging

filename = ""
level = "DEBUG" # DEBUG,INFO,WARN,ERROR

def debug(name,object,comment=""):
    """Add chart(s) to graphical debug log file.
    name: images,matrix"""
    if filename and level in ["DEBUG"]: log(name,object,comment)

def info(name,object,comment=""):
    """Add chart(s) to graphical debug log file.
    name: images,matrix"""
    if filename and level in ["DEBUG","INFO"]: log(name,object,comment)

def warn(name,object,comment=""):
    """Add chart(s) to graphical debug log file.
    name: images,matrix"""
    if filename and level in ["DEBUG","INFO","WARN"]:
        log(name,object,comment)

def error(name,object,comment=""):
    """Add chart(s) to graphical debug log file.
    name: images,matrix"""
    if filename and level in ["DEBUG","INFO","WARN","ERROR"]:
        log(name,object,comment)

def log(name,object,comment=""):
    """Add chart(s) to graphical debug log file.
    name: images,matrix"""
    if name == "images":   log_images(object,comment)
    elif name == "image":  log_image(object,comment)
    elif name == "matrix": log_matrix(object,comment)
    else: error("log: unkown keyword %r" % name)

def log_images(images,comment=""):
    import matplotlib; matplotlib.use("PDF",warn=False) # Turn off Tcl/Tk GUI.
    from matplotlib.backends.backend_pdf import PdfPages
    from pylab import figure,imshow,plot,title,grid,xlabel,ylabel,xlim,ylim,\
        xticks,yticks,legend,gca,rc,cm,colorbar,annotate,subplot,close,\
        tight_layout,loglog
    from numpy import clip,amin,amax,average,sum
    from matplotlib.colors import ListedColormap
    from tempfile import mkstemp
    from os import fdopen,unlink
    import glogging
    logging.info("Plotting images %s..." % comment)
    fd,filename = mkstemp(); fdopen(fd).close() # get rid of fd
    PDF_file = PdfPages(filename)
    
    for (i,image) in enumerate(images):
        fig = figure(figsize=(5,5))
        title("%s %d" % (comment,i))
        Imin,Imax = 0.02*amin(image),0.02*amax(image)
        imshow(clip(image,Imin,Imax).T,cmap=cm.gray,interpolation='nearest')
        colorbar()
        PDF_file.savefig(fig)
    PDF_file.close()
    close("all")
    PDF_append(glogging.filename,filename)
    unlink(filename)
    logging.info("Plotting done.")

def log_image(image,comment=""):
    import matplotlib; matplotlib.use("PDF",warn=False) # Turn off Tcl/Tk GUI.
    from matplotlib.backends.backend_pdf import PdfPages
    from pylab import figure,imshow,plot,title,grid,xlabel,ylabel,xlim,ylim,\
        xticks,yticks,legend,gca,rc,cm,colorbar,annotate,subplot,close,\
        tight_layout,loglog
    from numpy import clip,amin,amax,average,sum
    from matplotlib.colors import ListedColormap
    from tempfile import mkstemp
    from os import fdopen,unlink
    import glogging
    logging.info("Plotting image %s..." % comment)
    fd,filename = mkstemp(); fdopen(fd).close() # get rid of fd
    PDF_file = PdfPages(filename)
    
    fig = figure(figsize=(5,5))
    title("%s" % comment)
    Imin,Imax = 0.02*amin(image),0.02*amax(image)
    imshow(clip(image,Imin,Imax).T,cmap=cm.gray,interpolation='nearest')
    colorbar()
    PDF_file.savefig(fig)
    PDF_file.close()
    close("all")
    PDF_append(glogging.filename,filename)
    unlink(filename)
    logging.info("Plotting done.")

def log_matrix(matrix,comment=""):
    """X: 2D array
    """
    import matplotlib; matplotlib.use("PDF",warn=False) # Turn off Tcl/Tk GUI.
    from matplotlib.backends.backend_pdf import PdfPages
    from pylab import figure,imshow,plot,title,grid,xlabel,ylabel,xlim,ylim,\
        xticks,yticks,legend,gca,rc,cm,colorbar,annotate,subplot,close,\
        tight_layout,loglog
    from numpy import clip,amin,amax,average,sum
    from matplotlib.colors import ListedColormap
    from tempfile import mkstemp
    from os import fdopen,unlink
    import glogging
    logging.info("Plotting matrix %s..." % comment)
    fd,filename = mkstemp(); fdopen(fd).close() # get rid of fd
    PDF_file = PdfPages(filename)
    fig = figure(figsize=(5,5))
    title(comment)
    vmin,vmax = 0.2*amin(matrix),0.2*amax(matrix)
    imshow(clip(matrix,vmin,vmax).T,cmap=cm.gray,interpolation='nearest')
    colorbar()
    PDF_file.savefig(fig)
    PDF_file.close()
    close("all")
    PDF_append(glogging.filename,filename)
    unlink(filename)
    logging.info("Plotting done.")

def PDF_append(existing_filename,new_filename):
    from pyPdf import PdfFileReader,PdfFileWriter
    from os.path import exists
    from shutil import copy
    from os import unlink

    if exists(existing_filename):
        output = PdfFileWriter()

        tempfile = existing_filename+".tmp"
        copy(existing_filename,tempfile)
        existing_file = PdfFileReader(file(tempfile,"rb"))
        for i in range(0,existing_file.numPages):
            output.addPage(existing_file.getPage(i))

        new_file = PdfFileReader(file(new_filename,"rb"))
        for i in range(0,new_file.numPages):
            output.addPage(new_file.getPage(i))

        output.write(file(existing_filename,"wb"))
        unlink(tempfile)
    else: copy(new_filename,existing_filename)
