import wx


class Notespad(wx.Frame):

    UNTITLED = 'Untitled'  #
    WILDCARD = 'Text Documents (*.txt)|*.txt|Python Documents (*.py)|*.py'  #

    def __init__(self, *args, **kwargs):
        #----------------------------------------------------------- Attributes
        self.file_directory = None  #
        self.file_name = self.UNTITLED  #
        self.title_string = '{}{} - NotesPad'  #

        #---------------------------------------------------------- Frame Setup
        super(Notespad, self).__init__(*args, **kwargs)
        self.CreateStatusBar()

        #----------------------------------------------------------- Frame Menu
        menubar = wx.MenuBar()
        self.SetMenuBar(menubar)

        file_menu = wx.Menu()
        menu_open = file_menu.Append(wx.ID_OPEN, '&Open',
                                     'Open an existing document')

        menu_new = file_menu.Append(wx.ID_NEW, '&New',
                                    'Creates a new document')  #
        menu_save = file_menu.Append(wx.ID_SAVE, '&Save',
                                     'Saves the active document')  #
        menu_saveas = file_menu.Append(wx.ID_SAVEAS, 'Save &As',
                                'Saves the active document with a new name')  #

        file_menu.AppendSeparator()
        menu_exit = file_menu.Append(-1, 'Exit', 'Exit the Application')
        menubar.Append(file_menu, '&File')

        #--------------------------------------------------- Panel And Controls
        panel = wx.Panel(self)
        self.txt_ctrl = wx.TextCtrl(panel, style=wx.TE_MULTILINE)

        #------------------------------------------------------- Sizer Creation
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(panel, 1, wx.EXPAND)

        p_sizer = wx.BoxSizer(wx.VERTICAL)
        p_sizer.Add(self.txt_ctrl, 1, wx.EXPAND)

        #------------------------------------------------------- Setting Sizers
        panel.SetSizer(p_sizer)
        self.SetSizer(sizer)
        self.Layout()

        #---------------------------------------------------------- Event Binds
        self.Bind(wx.EVT_MENU, self.on_menu_exit, menu_exit)
        self.Bind(wx.EVT_MENU, self.on_menu_open, menu_open)

        self.Bind(wx.EVT_MENU, self.on_menu_new, menu_new)  #
        self.Bind(wx.EVT_MENU, self.on_menu_save, menu_save)  #
        self.Bind(wx.EVT_MENU, self.on_menu_saveas, menu_saveas)  #

        #-------------------------------------------------------- Initial State
        self.set_title()  #

    #----------------------------------------------------------- Event Handlers
    def on_menu_exit(self, event):
        self.Close()
        event.Skip()

    def on_menu_open(self, event):
        self.file_open()
        event.Skip()

    def on_menu_new(self, event):  #
        self.file_new()  #
        event.Skip()  #

    def on_menu_save(self, event):  #
        self.file_save()  #
        event.Skip()  #

    def on_menu_saveas(self, event):  #
        self.file_saveas()  #
        event.Skip()  #

    #------------------------------------------------------------------ Actions
    def file_open(self):
        with wx.FileDialog(self, message='Open', wildcard=self.WILDCARD,
                           style=wx.OPEN) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self.file_directory = dlg.GetDirectory()  #
                self.file_name = dlg.GetFilename()  #
                self.file_load()  #

    def file_load(self):  #
        full_path = '/'.join((self.file_directory, self.file_name))  #
        self.txt_ctrl.LoadFile(full_path)  #
        self.set_title()  #

    def file_new(self):  #
        self.file_directory = None  #
        self.file_name = self.UNTITLED  #
        self.txt_ctrl.Clear()  #
        self.set_title()  #

    def file_saveas(self):  #
        with wx.FileDialog(self, message='Save as', wildcard=self.WILDCARD,
                           style=wx.SAVE) as dlg:  #
            if dlg.ShowModal() == wx.ID_OK:  #
                self.file_directory = dlg.GetDirectory()  #
                self.file_name = dlg.GetFilename()  #
                self.file_save()  #

    def file_save(self):  #
        if self.file_name == self.UNTITLED:  #
            self.file_saveas()  #
        else:  #
            full_path = '/'.join((self.file_directory, self.file_name))  #
            self.txt_ctrl.SaveFile(full_path)  #
            self.set_title()  #

    def set_title(self):  #
        is_modified = '*' if self.txt_ctrl.IsModified() else ''  #
        self.SetTitle(self.title_string.format(is_modified, self.file_name))  #


if __name__ == '__main__':
    wx_app = wx.App(False)
    frame = Notespad(None)
    frame.Show()
    wx_app.MainLoop()
