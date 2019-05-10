"""
The script is to post-analyze sample alignment scans acquired by Lauecollect
It creates a PDF file with charts fo the scans in collection order.
The first reference image, collected the the X-ray beam going through the
center of the crystal which is used to define the spots position,
is marked as a green dot. The edge position calculated from the scan is
marked as a red dashed line.

Friedrich Schotte, 6 Oct 2011
"""
__version__ = "1.0.2"

scan_dir = "//Femto/C/Data/2011.10/Test/old_test6/alignment"
# Output: scan_dir+"/profiles.pdf"

from table import table
scans = table(scan_dir+"/phi,z,x,y,offset.txt")

import matplotlib; matplotlib.use("PDF",warn=False)
from matplotlib.backends.backend_pdf import PdfPages
PDF_file = PdfPages(scan_dir+"/profiles.pdf")

PHI = []; Z = []; OFFSET = []; FOM = []; EDGE = []
for i in range(0,len(scans)):
    filename = scan_dir+"/profile_phi=%.3f_z=%.3f.txt" % (scans.phi[i],scans.z[i])
    from os.path import exists
    from logging import warn
    if not exists(filename): warn("%s: not found" % filename); continue
    scan = table(filename)
    PHI += [scans.phi[i]]; Z += [scans.z[i]]; EDGE += [scans.offset[i]]
    offset = scan.offset if "offset" in scan.columns else scan["0"]
    fom = scan.FOM if "FOM" in scan.columns else scan["1"]
    OFFSET += [offset]; FOM += [fom]

from pylab import figure,plot,title,xlim,ylim,grid,legend,xlabel,ylabel,\
    gca,arange,array,scatter

fig = figure()
title("Phi and GonZ where scan were done")
scatter(Z,PHI,marker="o",c=range(0,len(PHI)))
xlabel("GonZ [mm]")
ylabel("Phi [deg]")
grid()
xmin,xmax = min(Z),max(Z)
ymin,ymax = min(PHI),max(PHI)
xmin,xmax = xmin-0.05*(xmax-xmin),xmax+0.05*(xmax-xmin)
ymin,ymax = ymin-0.05*(ymax-ymin),ymax+0.05*(ymax-ymin)
xlim(xmin=xmin,xmax=xmax)
ylim(ymin=ymin,ymax=ymax)
PDF_file.savefig(fig)

xmin,xmax = min(min(x) for x in OFFSET),max(max(x) for x in OFFSET)
ymin,ymax = min(min(y) for y in FOM),max(max(y) for y in FOM)

xmin,xmax = xmin-0.05*(xmax-xmin),xmax+0.05*(xmax-xmin)
ymin,ymax = ymin-0.05*(ymax-ymin),ymax+0.05*(ymax-ymin)

for i in range(0,len(FOM)):
    fig = figure()
    title("Scan %d of %d: phi=%.3f z=%.3f" % (i+1,len(FOM),PHI[i],Z[i]))
    plot([OFFSET[i][0],OFFSET[i][0]],[ymin,ymax],"--",color="black")
    plot([OFFSET[i][0]],[FOM[i][0]],"o",color="green",mec="green")
    plot(OFFSET[i][1:],FOM[i][1:],"-o",color="blue")
    plot([EDGE[i],EDGE[i]],[ymin,ymax],"--",color="red")
    legend(["center","reference","scan","edge"],frameon=False,numpoints=1)
    xlim(xmin=xmin,xmax=xmax)
    ylim(ymin=ymin,ymax=ymax)
    grid()
    xlabel("offset [mm]")
    ylabel("FOM [counts]")
    PDF_file.savefig(fig)
PDF_file.close()
