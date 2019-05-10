"""Beam Profile Display window
Author: Friedrich Schotte, Feb 26, 2016 - Sep 28, 2017
"""
import wx
from profile import xy_projections,FWHM,CFWHM,xvals,yvals
from logging import debug,info,warn,error

__version__ = "1.1.2" # optional arguments

class BeamProfile(wx.Panel):
    """Beam Profile Display window"""
    name = "BeamProfile"
    attributes = [
        "image",
        "x_ROI_center",
        "y_ROI_center",
        "ROI_width",
        "saturation_level",
        "x_nominal",
        "y_nominal",
    ]
    from numimage import numimage; from numpy import uint16
    
    def __init__(self,parent,title="Beam Profile",object=None,
        refresh_period=1.0,size=(300,300),*args,**kwargs):
        """title: string
        object: has attributes "image","x_ROI_center",...
        """
        wx.Window.__init__(self,parent,size=size,*args,**kwargs)
        self.title = title
        self.object = object
        self.refresh_period = refresh_period

        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE,self.OnResize)

        # Refresh
        from numpy import nan,uint16
        from numimage import numimage
        self.values = dict([(n,nan) for n in self.attributes])
        self.values["image"] = numimage((0,0),dtype=uint16,pixelsize=0.080)
        self.old_values = {}
        
        from threading import Thread
        self.refresh_thread = Thread(target=self.refresh_background,
            name=self.name+".refresh")
        self.refreshing = False

        from wx.lib.newevent import NewEvent
        self.EVT_THREAD = NewEvent()[1]
        self.Bind(self.EVT_THREAD,self.OnUpdate)
        self.thread = Thread(target=self.keep_updated,name=self.name)
        self.thread.start()

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time,sleep
        while True:
            try:
                t0 = time()
                while time() < t0+self.refresh_period: sleep(0.1)
                if self.Shown:
                    self.update_data()
                    if self.data_changed: 
                        event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
                        # call OnUpdate in GUI thread
                        wx.PostEvent(self.EventHandler,event)
            except wx.PyDeadObjectError: break

    def refresh(self):
        """Force update"""
        from threading import Thread
        if not self.refreshing and self.Shown:
            self.refresh_thread = Thread(target=self.refresh_background,
                name=self.name+".refresh")
            self.refreshing = True
            self.refresh_thread.start()
        else: debug("beam profile: already refreshing")

    def refresh_background(self):
        """Force update"""
        self.update_data()
        if self.data_changed: 
            event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
            wx.PostEvent(self.EventHandler,event) # call OnUpdate in GUI thread
            debug("beam profile: redraw triggered")
        self.refreshing = False

    def update_data(self):
        """Retreive status information"""
        self.old_values = dict(self.values) # make a copy
        for n in self.attributes: self.values[n] = getattr(self.object,n)
        ##from numpy import copy
        ##self.old_values = dict((n,copy(self.values[n])) for n in self.values) 
        ##for n in self.attributes:
        ##    self.values[n] = copy(getattr(self.object,n))
        ##debug("beam profile: update completed")

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        ##changed = (self.values != self.old_values)
        if sorted(self.values.keys()) != sorted(self.old_values.keys()):
            debug("beam profile: %r != %r" % (self.values.keys(),self.old_values.keys()))
            changed = True
        else:
            changed = False
            for a in self.values:
                item_changed = not nan_equal(self.values[a],self.old_values[a])
                debug("beam profile: %r: changed: %r" % (a,item_changed))
                changed = changed or item_changed
        debug("beam profile: data changed: %r" % changed)
        return changed

    def OnUpdate(self,event=None):
        """Periodically refresh the displayed settings."""
        self.Refresh() # triggers "OnPaint" call

    def OnPaint(self,event):
        """Called by WX whenever the contents of the window
        needs re-rendering. E.g. when the window is brought to front,
        uncovered, restored from minimized state."""
        debug("OnPaint")
        
        from numpy import rint,array,minimum,uint8,ndarray,isnan,nan

        dc = wx.PaintDC(self)
        ##self.PrepareDC(dc)

        image = self.values["image"]
        debug("beam profile: image %r" % (image.shape,))
        pixelsize = image.pixelsize
        # Clip to ROI (region of interest)
        cx,cy = self.values["x_ROI_center"],self.values["y_ROI_center"]
        w = h = self.values["ROI_width"]
        W,H = self.ClientSize
        if W > H: w = h/H*W
        if W < H: h = w/W*H
        ROI = xmin,xmax,ymin,ymax = cx-w/2,cx+w/2,cy-h/2,cy+h/2
        ixmin,ixmax,iymin,iymax = rint(array(ROI)/pixelsize).astype(int)
        ROI = xmin,xmax,ymin,ymax = array([ixmin,ixmax,iymin,iymax])*pixelsize
        w,h = xmax-xmin,ymax-ymin
        image_ROI = image[ixmin:ixmax,iymin:iymax]
        
        # Compress the dynamic range from 0...saturation_level to 0...256.
        scale = 255./max(self.values["saturation_level"],1)
        image = minimum(image_ROI*scale,255).astype(uint8)

        # Convert from gray scale to  RGB format if needed.        
        if image.ndim < 3:
            w,h = image.shape[-2:]
            RGB = ndarray((3,w,h),uint8,order="F")
            RGB[0],RGB[1],RGB[2] = image,image,image
            image = RGB

        # Mark overloaded pixels.
        overload_level = 65535
        mask_color = (255,0,0)
        mask_opacity = 1.0
        mask = image_ROI >= overload_level
        R,G,B = image
        r,g,b = mask_color
        x = mask_opacity
        R[mask] = (1-x)*R[mask]+x*r
        G[mask] = (1-x)*G[mask]+x*g
        B[mask] = (1-x)*B[mask]+x*b
        ##image = array([R,G,B]) # needed?

        # Convert image from numpy to WX image format.
        w,h = image.shape[-2:]
        image = wx.ImageFromData(w,h,image)

        # Scale the image to fit into the window.
        W,H = self.ClientSize
            
        if len(self.values["image"]) > 0:
            ##scalefactor = min(float(W)/max(w,1),float(H)/max(h,1))
            ##W = rint(w*scalefactor); H = rint(h*scalefactor)
            image = image.Scale(W,H)
            dc.DrawBitmap (wx.BitmapFromImage(image),0,0)

        # Draw the FWHM with dimensions box around the beam center,
        # horizontal and vertcal beam projections or sections on the left and
        # bottom edge of the image
        cx,cy = self.values["x_ROI_center"],self.values["y_ROI_center"]
        d = self.values["ROI_width"]
        ROI = cx-d/2,cx+d/2,cy-d/2,cy+d/2
        ROI = rint(array(ROI)/pixelsize)*pixelsize
        ROI_xmin,ROI_xmax,ROI_ymin,ROI_ymax = ROI
        xprofile,yprofile = xy_projections(self.values["image"],(cx,cy),d)

        xscale = float(W)/max(w,1)/pixelsize; xoffset = -xmin*xscale
        yscale = float(H)/max(h,1)/pixelsize; yoffset = (-ymin)*yscale

        # Draw a crosshair marking the nominal beam center.
        crosshair_color = wx.Colour(0,190,0)
        dc.SetPen(wx.Pen(crosshair_color,1))
        l = 0.2 # crosshair size in mm
        x = self.values["x_nominal"]*xscale+xoffset
        y = self.values["y_nominal"]*yscale+yoffset
        rx,ry = l/2*xscale,l/2*yscale
        dc.DrawLines([(x-rx,y),(x+rx,y)])
        dc.DrawLines([(x,y-ry),(x,y+ry)])
        
        # Draw horizontal profile at the bottom edge of the image.
        profile_color = wx.Colour(255,0,255)
        dc.SetPen (wx.Pen(profile_color,1))
        x = xvals(xprofile); I = yvals(xprofile)
        Imax = max(I) if len(I)>0 else nan
        if Imax == 0: Imax = 1
        Iscale = -0.35*(ROI_ymax-ROI_ymin)*xscale/Imax
        Ioffset = ROI_ymax*yscale+yoffset
        lines = []
        for i in range(0,len(x)-1):
            if not isnan(I[i]) and not isnan(I[i+1]):
                p1 = x[i]  *xscale+xoffset, I[i]  *Iscale+Ioffset
                p2 = x[i+1]*xscale+xoffset, I[i+1]*Iscale+Ioffset
                lines += [(p1[0],p1[1],p2[0],p2[1])]
        dc.DrawLineList(lines)
    
        # Draw vertical profile at the left edge of the image.
        profile_color = wx.Colour(255,0,255)
        dc.SetPen(wx.Pen(profile_color,1))
        y = xvals(yprofile); I = yvals(yprofile)
        Imax = max(I) if len(I)>0 else nan
        if Imax == 0: Imax = 1
        Iscale = 0.35*(ROI_xmax-ROI_xmin)*xscale/Imax
        Ioffset = ROI_xmin*xscale+xoffset
        lines = []
        for i in range(0,len(y)-1):
            if not isnan(I[i]) and not isnan(I[i+1]):
                p1 = I[i]  *Iscale+Ioffset, y[i]  *yscale+yoffset
                p2 = I[i+1]*Iscale+Ioffset, y[i+1]*yscale+yoffset
                lines += [(p1[0],p1[1],p2[0],p2[1])]
        dc.DrawLineList(lines)

        # Draw a box around the ROI.
        center_color = wx.Colour(128,128,255)
        dc.SetPen(wx.Pen(profile_color,1))
        x1,y1 = ROI_xmin*xscale+xoffset,ROI_ymin*yscale+yoffset
        x2,y2 = ROI_xmax*xscale+xoffset-1,ROI_ymax*yscale+yoffset-1
        lines = [(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)]
        dc.DrawLines (lines)

        # Draw a box around center of the beam, with the size of the FWHM.
        FWHM_color = wx.Colour(255,0,0)
        dc.SetPen (wx.Pen(FWHM_color,1))
        width,height = FWHM(xprofile),FWHM(yprofile)
        cx,cy = CFWHM(xprofile),CFWHM(yprofile)

        x1,y1 = (cx-width/2)*xscale+xoffset,(cy-height/2)*yscale+yoffset
        x2,y2 = (cx+width/2)*xscale+xoffset,(cy+height/2)*yscale+yoffset
        lines = [(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)]
        dc.DrawLines(lines)

        # Draw a vertical and horizontal line throught the center.
        center_color = wx.Colour(128,128,255)
        dc.SetPen (wx.Pen(center_color,1))
        dc.DrawLines ([(cx*xscale+xoffset,H),(cx*xscale+xoffset,0)])
        dc.DrawLines ([(0,cy*yscale+yoffset),(W,cy*yscale+yoffset)])

        # Annotate the lines.
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetPointSize(10)
        dc.SetFont(font)
        dc.SetTextForeground(center_color)

        dx = cx - self.values["x_nominal"]
        if abs(dx) < 1: label = "%+.0f um" % (dx*1000)
        else: label = "%+.3f mm" % dx
        x,y = cx*xscale+xoffset,0.875*H
        tw,th = dc.GetTextExtent(label)
        dc.DrawRotatedText (label,toint(x+2),toint(y-th/2),0)

        dy = cy - self.values["y_nominal"]
        if abs(dy) < 1: label = "%+.0f um" % (dy*1000)
        else: label = "%+.3f mm" % dy
        x,y = 0.175*W,cy*yscale+yoffset
        tw,th = dc.GetTextExtent(label)
        dc.DrawRotatedText (label,toint(x-th/2),toint(y+2),-90)        

    def OnResize(self,event):
        self.Refresh()
        event.Skip() # call default handler

def toint(x):
    """Convert to integer without rasing exceptions"""
    from numpy import rint
    x = rint(x)
    try: x = int(x)
    except: x = 0
    return x

def nan_equal(a,b):
    """Are to array equal? a and b may contain NaNs"""
    import numpy
    try: numpy.testing.assert_equal(a,b)
    except AssertionError: return False
    return True
