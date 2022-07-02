"""
a python code to save the position of all motors to a file
"""

root = "/net/mx340hs/data/anfinrud_1908/Logbook/Beamline_snapshot/"

__version__ = "0.0.1"


from datetime import datetime
import wx
# white beam slits (at 28 m)
from persistent_property import persistent_property


class Save_To_File(object):
    root = persistent_property('root', "/net/mx340hs/data/anfinrud_1908/Logbook/Beamline_snapshot/")
    comment = persistent_property('comment', "Please write your comments here.")
    def __init__(self):
        self.name = 'save_beamline_state'

        self.lst = []

        self.lst.append(['white beam slits (at 28 m) Slit1H','14IDA:Slit1Hsize'])
        self.lst.append(['white beam slits (at 28 m) Slit1V','14IDA:Slit1Vsize'])

        # Heat-load chopper
        self.lst.append(['Heat-load chopper HLC','14IDA:m5'])

        # mir1Th = motor("14IDC:mir1Th",name="mir1Th")
        # MirrorV = motor("14IDA:DAC1_4",name="MirrorV",readback="VAL")
        # mir1bender = motor("14IDC:m6",name="mir1bender")
        #
        # mir2X1 = motor("14IDC:m12",name="mir2X1") # H mirror X1-upstream
        # mir2X2 = motor("14IDC:m13",name="mir2X2") # H mirror X1-downstream
        # mir2Th = tilt(mir2X1,mir2X2,distance=1.045,name="mir2Th",unit="mrad")
        # MirrorH = mir2Th
        # mir2bender = motor("14IDC:m14",name="mir2bender")
        #
        # # Motors in ID14-B end station
        #
        # # Table horizontal pseudo motor.
        # TableX = motor("14IDB:table1",name="TableX",command="X",readback="EX")
        # # Table vertical pseudo motor.
        # TableY = motor("14IDB:table1",name="TableY",command="Y",readback="EY")

        # JJ1 slits (upstream)
        self.lst.append(['JJ1 slits s1vg','14IDC:m37'])
        self.lst.append(['JJ1 slits s1vo','14IDC:m38'])
        self.lst.append(['JJ1 slits s1hg','14IDC:m39'])
        self.lst.append(['JJ1 slits s1ho','14IDC:m40'])

        # High-speed X-ray Chopper
        self.lst.append(['High-speed X-ray Chopper ChopX','14IDB:m1'])
        self.lst.append(['High-speed X-ray Chopper ChopY','14IDB:m2'])


        # JJ2 slits (downstream)
        self.lst.append(['JJ2 slits (downstream) shg','14IDB:m25'])
        self.lst.append(['JJ2 slits (downstream) sho','14IDB:m26'])
        self.lst.append(['JJ2 slits (downstream) svg','14IDB:m27'])
        self.lst.append(['JJ2 slits (downstream) svo','14IDB:m28'])


        # KB mirror
        self.lst.append(['KB mirror KB_Vpitch','14IDC:pm4'])
        self.lst.append(['KB mirror KB_Vheight','14IDC:pm3'])
        self.lst.append(['KB mirror KB_Vcurvature','14IDC:pm1'])
        self.lst.append(['KB mirror KB_Vstripe','14IDC:m15'])
        self.lst.append(['KB mirror KB_Hpitch','14IDC:pm8'])
        self.lst.append(['KB mirror KB_Hheight','14IDC:pm7'])
        self.lst.append(['KB mirror KB_Hcurvature','14IDC:pm5'])
        self.lst.append(['KB mirror KB_Hstripe','14IDC:m44'])


        # Collimator
        self.lst.append(['Collimator CollX','14IDB:m35'])
        self.lst.append(['Collimator CollY','14IDB:m36'])

    def kill(self):
        del self

    def get_filename(self):
        import time
        from datetime import datetime
        string = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(int(time.time())))
        filename = str(string) + '_beamline_snapshot.log'
        return filename

    def get_snapshot(self,lst):
        from numpy import concatenate
        from CA import caget
        new_lst = []
        for item in lst:
            new_lst.append([item[0],item[1],caget(item[1]+'.RBV')])
        return new_lst

    def get_header(self):
        header = '#This is a header for this file. \n'
        return header

    def save_to_file(self,root,filename, lst, comment):
        import os
        from time import time
        from datetime import datetime
        if not os.path.exists(root):
            os.mkdir(root)
        with open(root+filename,"w") as file:
            file.write(self.get_header())
            file.write("Time: "+str(datetime.fromtimestamp(time()))+"\n")
            file.write("Comment: "+comment+"\n")
            file.write("###HEADER END###\n" )
            for item in lst:
                file.write(str(item) + '\n')

    def test_save(self):
        self.save_to_file(self.root,self.get_filename(),self.get_snapshot(lst), comment = 'this data was collected after all original alignment was done.')





class Frame(wx.Frame):

    title = "Save Beamline motor positions"
    def __init__(self):

        wx.Frame.__init__(self, None, wx.ID_ANY, title=self.title, style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        self.panel=wx.Panel(self, -1)
        self.Bind(wx.EVT_CLOSE, self.OnQuit)

        file_item = {}
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        file_item[0] = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        self.Bind(wx.EVT_MENU, self.OnQuit, file_item[0])

        menubar.Append(fileMenu, '&File')
        #menubar.Append(aboutMenu, '&About')

        self.SetMenuBar(menubar)

        self.initGUI()
        self.SetBackgroundColour(wx.Colour(255,255,255))
        self.Centre()
        self.Show()

    def OnQuit(self,event):
        self.Destroy()
        save_to_file.kill()
        del self


    def OnSnapshot(self,event):
        lst = save_to_file.lst
        root = save_to_file.root
        comment = self.fields[b'comment'].GetValue() #save_to_file.comment
        save_to_file.comment = comment
        save_to_file.save_to_file(root,save_to_file.get_filename(),save_to_file.get_snapshot(lst), comment)


    def OnComment(self,event):
        string = event.GetString()
        save_to_file.comment = string

    def OnRoot(self,event):
        import os
        string = event.GetString()
        save_to_file.root = string
        if os.path.exists(string):
            self.fields[b'root'].SetBackgroundColour(wx.Colour(255, 255, 255))
        else:
            self.fields[b'root'].SetBackgroundColour(wx.Colour(200, 200, 0))

    def initGUI(self):
        self.xs_font = 10
        self.s_font = 12
        self.m_font = 16
        self.l_font = 24
        self.xl_font = 32
        self.xl_font = 60
        self.wx_xs_font = wx_xs_font=wx.Font(self.xs_font,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        self.wx_s_font = wx_s_font=wx.Font(self.s_font,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        self.wx_m_font = wx_m_font=wx.Font(self.m_font,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        self.wx_l_font = wx_l_font=wx.Font(self.l_font,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        self.wx_xl_font = wx_xl_font=wx.Font(self.xl_font,wx.DEFAULT,wx.NORMAL,wx.NORMAL)
        self.wx_xxl_font = wx_xxl_font=wx.Font(self.xl_font,wx.DEFAULT,wx.NORMAL,wx.NORMAL)

        sizer = wx.GridBagSizer(hgap = 5, vgap = 5)
        self.labels ={}
        self.fields = {}
        self.sizer = {}
        self.top_sizer = wx.BoxSizer(wx.VERTICAL)



        self.labels[b'root'] = wx.StaticText(self.panel, label= "root directory")
        self.fields[b'root']  = wx.TextCtrl(self.panel,-1,style = wx.TE_PROCESS_ENTER, size = (400,-1), value = save_to_file.root)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnRoot, self.fields[b'root'])
        self.fields[b'root'].SetFont(self.wx_s_font)
        self.labels[b'root'].SetFont(self.wx_m_font)
        self.sizer[b'root'] = wx.BoxSizer(wx.VERTICAL)
        self.sizer[b'root'].Add(self.labels[b'root'],  0)
        self.sizer[b'root'].Add(self.fields[b'root'],  0)

        self.labels[b'comment'] = wx.StaticText(self.panel, label= "comments:")
        self.fields[b'comment']  = wx.TextCtrl(self.panel,-1,style = wx.TE_PROCESS_ENTER|wx.TE_MULTILINE|wx.TE_NO_VSCROLL|wx.BORDER_NONE, size = (400,100), value = save_to_file.comment)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnComment, self.fields[b'comment'])
        self.fields[b'comment'].SetFont(self.wx_s_font)
        self.labels[b'comment'].SetFont(self.wx_m_font)
        self.sizer[b'comment'] = wx.BoxSizer(wx.VERTICAL)
        self.sizer[b'comment'].Add(self.labels[b'comment'],  0)
        self.sizer[b'comment'].Add(self.fields[b'comment'],  0)

        self.snapshot  = wx.Button(self.panel, label="Take Beamline Snapshot", size = (150,-1))
        self.snapshot.Bind(wx.EVT_BUTTON, self.OnSnapshot)
        self.sizer[b'snapshot'] = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer[b'snapshot'].Add(self.snapshot,  0)



        self.Center()
        self.Show()

        self.top_sizer.Add(self.sizer[b'root'] ,0)
        self.top_sizer.Add(self.sizer[b'comment'] ,0)
        self.top_sizer.Add(self.sizer[b'snapshot'] ,0)

        self.panel.SetSizer(self.top_sizer)
        self.top_sizer.Fit(self)
        self.Layout()
        self.panel.Layout()
        self.panel.Fit()
        self.Fit()

if __name__ == "__main__":
    save_to_file = Save_To_File()

    app = wx.App()
    frame = Frame()
    frame.initGUI()
    frame.Show()
    app.MainLoop()
