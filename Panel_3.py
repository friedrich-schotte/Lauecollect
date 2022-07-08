#!/usr/bin/env python
"""Graphical User Interface
Author: Friedrich Schotte
Date created: 2008-11-23
Date last modified: 2022-04-01
Revision comment: Fixed: Issue:
    format(value, "#08b")
    ValueError: Unknown format code 'b' for object of type 'float'
"""
__version__ = "3.3.5"

from logging import debug, warning, error
from traceback import format_exc

import wx

from SI_format import to_SI_format, from_SI_format
from handler import handler
from reference import reference


class Application_Menu_Item:
    def __init__(self, label, application):
        self.label = label
        self.application = application


class Application_Button:
    def __init__(self, label, application):
        self.label = label
        self.application = application


class BasePanel(wx.Frame):
    from persistent_property import persistent_property
    from monitored_value_property import monitored_value_property
    from collections import OrderedDict

    CustomView = persistent_property("CustomView", [])
    views = OrderedDict([("Standard", "StandardView"), ("Custom", "CustomView")])
    view = persistent_property("view", "Standard")

    title = monitored_value_property(default_value="Base Panel")
    name = "BasePanel"
    parameters = []
    standard_view = []
    application_menu_items = []
    application_buttons = []
    subname = True
    label_width = 150
    width = 120
    live = False
    icon = None

    def __init__(
            self,
            parent=None,
            name=None,
            title=None,
            parameters=None,
            standard_view=None,
            application_menu_items=None,
            application_buttons=None,
            subname=None,
            label_width=None,
            width=None,
            icon=None,
            *common_args,
            **common_kwargs,
    ):
        wx.Frame.__init__(self, parent=parent)

        if name is not None:
            self.name = name
        if title is not None:
            self.title = title
        if parameters is not None:
            self.parameters = parameters
        if standard_view is not None:
            self.standard_view = standard_view
        if application_menu_items is not None:
            self.application_menu_items = application_menu_items
        if application_buttons is not None:
            self.application_buttons = application_buttons
        if subname is not None:
            self.subname = subname
        if label_width is not None:
            self.label_width = label_width
        if width is not None:
            self.width = width
        if icon is not None:
            self.icon = icon

        self.Title = "Loading..."
        self.StandardView = self.standard_view

        if self.subname and hasattr(parent, "name"):
            self.name = parent.name + "." + self.name
        if not self.CustomView:
            self.CustomView = standard_view

        # Icon
        from Icon import SetIcon
        SetIcon(self, self.icon)

        # Controls
        self.panel = wx.Panel(self)
        self.controls = []
        for args, kwargs in self.parameters:
            args += common_args
            kwargs.update(common_kwargs)
            kwargs["label_width"] = self.label_width
            kwargs["width"] = self.width
            self.controls += [PropertyPanel(self.panel, *args, **kwargs)]

        style = wx.BU_EXACTFIT
        self.Application_Buttons = []
        for i, button in enumerate(self.application_buttons):
            Button = wx.Button(self.panel, label=button.label, style=style, id=i)
            self.Application_Buttons += [Button]

        # Menus
        menuBar = wx.MenuBar()
        # Edit
        menu = wx.Menu()
        menu.Append(wx.ID_CUT, "Cu&t\tCtrl+X", "selection to clipboard")
        menu.Append(wx.ID_COPY, "&Copy\tCtrl+C", "selection to clipboard")
        menu.Append(wx.ID_PASTE, "&Paste\tCtrl+V", "clipboard to selection")
        menu.Append(wx.ID_DELETE, "&Delete\tDel", "clear selection")
        menu.Append(wx.ID_SELECTALL, "Select &All\tCtrl+A")
        menuBar.Append(menu, "&Edit")
        # View
        self.ViewMenu = wx.Menu()
        for i in range(0, len(self.views)):
            self.ViewMenu.AppendCheckItem(10 + i, list(self.views.keys())[i])
        self.ViewMenu.AppendSeparator()
        for i in range(0, len(self.controls)):
            self.ViewMenu.AppendCheckItem(100 + i, self.controls[i].title)
        menuBar.Append(self.ViewMenu, "&View")
        # More
        if len(self.application_menu_items) > 0:
            menu = wx.Menu()
            for i, menu_item in enumerate(self.application_menu_items):
                menu.Append(300 + i, menu_item.label)
            menuBar.Append(menu, "&More")
        # Help
        menu = wx.Menu()
        menu.Append(wx.ID_ABOUT, "About...", "Show version number")
        menuBar.Append(menu, "&Help")
        self.SetMenuBar(menuBar)

        # Callbacks
        for i in range(0, len(self.views)):
            self.Bind(wx.EVT_MENU, self.OnSelectView, id=10 + i)
        for i in range(0, len(self.controls)):
            self.Bind(wx.EVT_MENU, self.OnView, id=100 + i)
        self.Bind(wx.EVT_MENU_OPEN, self.OnMenuOpen)
        # self.ViewMenu.Bind(wx.EVT_MENU_OPEN,self.OnViewMenuOpen)
        for i in range(0, len(self.application_menu_items)):
            self.Bind(wx.EVT_MENU, self.OnApplicationMenuItem, id=300 + i)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        for Button in self.Application_Buttons:
            self.Bind(wx.EVT_BUTTON, self.OnApplicationButton, Button)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Layout
        layout = wx.BoxSizer(wx.VERTICAL)
        flag = wx.ALL | wx.EXPAND
        for c in self.controls:
            layout.Add(c, flag=flag, border=0, proportion=1)
        for c in self.controls:
            c.Shown = c.title in self.view

        # Leave a 5-pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(layout, flag=flag, border=5, proportion=1)

        buttons_group = wx.BoxSizer(wx.HORIZONTAL)
        for Button in self.Application_Buttons:
            buttons_group.AddSpacer(1)
            buttons_group.Add(Button)
        box.Add(buttons_group, flag=wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, border=5)

        self.panel.Sizer = box
        self.panel.Fit()
        self.Fit()

        # Initialization
        if self.view not in self.views:
            self.view = list(self.views.keys())[0]
        self.View = getattr(self, self.views[self.view])

        self.Show()
        self.update()
        self.monitoring = True

    from run_async import run_async

    @run_async
    def update(self):
        wx.CallAfter(self.SetTitle, self.title)

    @property
    def monitoring(self):
        return handler(self.handle_change) in self.monitors

    @monitoring.setter
    def monitoring(self, enable):
        if enable:
            self.monitors.add(handler(self.handle_change))
        else:
            self.monitors.monitors.remove(handler(self.handle_change))

    @property
    def monitors(self):
        return reference(self, "title").monitors

    def handle_change(self, event):
        wx.CallAfter(self.SetTitle, event.value)

    def OnResize(self, event):
        self.panel.Fit()
        event.Skip()  # call default handler

    def get_View(self):
        """Which control to show? List of strings"""
        return [c.title for c in self.controls if c.Shown]

    def set_View(self, value):
        for c in self.controls:
            c.Shown = c.title in value
        self.panel.Sizer.Fit(self)

    View = property(get_View, set_View)

    def OnMenuOpen(self, event):
        # debug("Menu opened: %r" % event.EventObject)
        if event.EventObject == self.ViewMenu:
            self.OnViewMenuOpen(event)

    def OnViewMenuOpen(self, _event):
        """Handle "View" menu display"""
        # debug("View menu opened")
        for i in range(0, len(self.views)):
            self.ViewMenu.Check(10 + i, list(self.views.keys())[i] == self.view)
        for i in range(0, len(self.controls)):
            self.ViewMenu.Check(100 + i, self.controls[i].Shown)
            self.ViewMenu.Enable(100 + i, self.view != "Standard")

    def OnSelectView(self, event):
        """Called if one of the items of the "View" menu is selected"""
        n = event.Id - 10
        self.view = list(self.views.keys())[n]
        self.View = getattr(self, list(self.views.values())[n])

    def OnView(self, event):
        """Called if one of the items of the "View" menu is selected"""
        n = event.Id - 100
        self.controls[n].Shown = not self.controls[n].Shown
        self.panel.Sizer.Fit(self)
        view = [c.title for c in self.controls if c.Shown]
        setattr(self, self.views[self.view], view)

    def OnApplicationMenuItem(self, event):
        n = event.Id - 300
        if 0 <= n < len(self.application_menu_items):
            menu_item = self.application_menu_items[n]
            menu_item.application.start()

    def OnAbout(self, _event):
        """Show version info"""
        from About import About
        About(self)

    def OnApplicationButton(self, event):
        # debug("Button %r pressed" % event.Id)
        n = event.Id
        if 0 <= n < len(self.application_buttons):
            button = self.application_buttons[n]
            button.application.start()

    def OnClose(self, _event):
        """Called when the windows's close button is clicked"""
        self.Show(False)
        # for control in self.controls: control.Destroy()
        # self.Destroy() # might crash under Windows
        wx.CallLater(1000, self.Destroy)


class PropertyPanel(wx.Panel):
    """A subunit for 'BasePanel'"""
    from run_async import run_async

    title = ""
    object = None
    name = ""
    type = ""
    choices_value = None
    choices_reference = None
    format = ""
    read_only = False
    digits = None
    unit = ""
    label_width = 180
    width = 120

    def __init__(
            self,
            parent=None,
            title=None,
            obj=None,
            name=None,
            type=None,
            choices=None,
            choices_value=None,
            choices_reference=None,
            format=None,
            read_only=None,
            digits=None,
            width=None,
            unit=None,
            label_width=None,
    ):
        """title: descriptive label
        name: property name of obj
        """
        wx.Panel.__init__(self, parent)
        if title is not None:
            self.title = title
        if obj is not None:
            self.object = obj
        if name is not None:
            self.name = name
        if type is not None:
            self.type = type
        if choices is not None:
            self.choices_value = choices
        if choices_value is not None:
            self.choices_value = choices
        if choices_reference is not None:
            self.choices_reference = choices_reference
        if format is not None:
            self.format = format
        if read_only is not None:
            self.read_only = read_only
        if digits is not None:
            self.format = "%%.%df" % digits
        if width is not None:
            self.width = width
        if unit is not None:
            self.unit = unit
        if label_width is not None:
            self.label_width = label_width

        self.changing = False

        # Controls
        style = wx.TE_PROCESS_ENTER
        if self.has_choices:
            if not self.read_only:
                from EditableControls import ComboBox
                self.Current = ComboBox(self, size=(self.width, -1), style=style)
            if self.read_only:
                self.Current = wx.TextCtrl(self, size=(self.width, -1), style=wx.TE_READONLY)
        if not self.has_choices:
            if not self.read_only:
                from EditableControls import TextCtrl
                self.Current = TextCtrl(self, size=(self.width, -1), style=style)
            if self.read_only:
                self.Current = wx.TextCtrl(self, size=(self.width, -1), style=wx.TE_READONLY)
        # Callbacks
        self.Bind(wx.EVT_TEXT_ENTER, self.OnChange, self.Current)
        self.Bind(wx.EVT_COMBOBOX, self.OnChange, self.Current)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

        # Layout
        layout = wx.BoxSizer()
        # av = wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND
        if self.title:
            label = wx.StaticText(self, label=self.title + ":", size=(label_width, -1))
            layout.Add(label, flag=e)
        layout.Add(self.Current, flag=e, proportion=1)
        self.SetSizer(layout)
        self.Fit()

    def __repr__(self):
        return f"{type(self).__name__}({self.reference})"

    def IsShown(self):
        return wx.Panel.IsShown(self)

    def Show(self, show: bool = True):
        wx.Panel.Show(self, show)
        self.monitoring = show

    Shown = property(IsShown, Show)

    def OnDestroy(self, event):
        event.Skip()
        self.monitoring = False

    def get_monitoring(self):
        return self.change_handler in self.reference.monitors

    def set_monitoring(self, value):
        if value != self.monitoring:
            if bool(value) is True:
                self.start_monitoring()
            if bool(value) is False:
                debug(f"Unsubscribing from {self.reference}")
                self.reference.monitors.remove(self.change_handler)

    monitoring = property(get_monitoring, set_monitoring)

    @run_async
    def start_monitoring(self):
        value = self.reference.value
        debug(f"{self.reference} = {value}")

        str_value = self.formatted_text(value)
        choices = self.formatted_choices(self.choices)
        wx.CallAfter(self.set_value, str_value, choices)

        debug(f"Subscribing to {self.reference}")
        self.reference.monitors.add(self.change_handler)

    @property
    def reference(self):
        from reference import reference
        return reference(self.object, self.name)

    @property
    def change_handler(self):
        from handler import handler
        event_handler = handler(self.handle_change)
        return event_handler

    def handle_change(self, event=None):
        if event and event.reference != self.reference:
            warning(f"Subscribed to {self.reference}, but got update for {event.reference}")

        if event and event.reference == self.reference:
            value = event.value
        else:
            value = getattr(self.object, self.name)

        # debug(f"{self.reference} = {repr(value):.60s}".replace("\n",""))

        str_value = self.formatted_text(value)
        choices = self.formatted_choices(self.choices)

        wx.CallAfter(self.set_value, str_value, choices)

    def set_value(self, str_value, choices):
        """Update the displayed value in the indicator"""
        debug(f"{self}.Current.Value -> {str_value!r}...")

        if "" not in choices:
            choices = choices + [""]
        self.Current.Items = choices
        self.Current.Value = str_value

        debug(f"{self}.Current.Value = {str_value!r}.")

    def formatted_text(self, value):
        """Value as text"""
        from numpy import isnan
        if value is None:
            text = ""
        elif is_numeric(value) and isnan(value):
            text = "-"
        elif self.type.startswith("time") or self.type.startswith("frequency"):
            from time_string import time_string
            precision = self.type.split(".")[-1][0]
            try:
                precision = int(precision)
            except (ValueError, TypeError):
                precision = 3
            if self.type.startswith("time"):
                def my_format(x):
                    return time_string(x, precision)
            else:
                def my_format(x):
                    from div import div
                    return to_SI_format(div(1,x), precision) + "Hz"
            text = my_format(value)
        elif self.type == "date":
            from date_time import date_time
            text = date_time(value)
        elif self.type == "binary":
            text = "%g (%s)" % (value, format(int(value), "#08b"))
        elif self.type == "bool":
            text = "True" if value else "False"
        elif self.type == "int":
            try:
                text = "%d" % value
            except (ValueError, TypeError, ArithmeticError) as x:
                debug(f"{self.object}.{self.name}: '%d' % {value!r}: {x}")
                text = ""
        elif self.type == "float":
            format_str = self.format if self.format else "%g"
            try:
                text = format_str % value
            except (ValueError, TypeError, ArithmeticError) as x:
                debug(f"{self.object}.{self.name}: {format_str!r} % {value!r}: {x}")
                text = ""
        elif self.type == "str":
            text = str(value)
        elif self.type == "list":
            text = ",".join([str(x) for x in value])
        elif "/" in self.type:  # list of names
            choices = self.type.split("/")
            try:
                text = choices[int(value)]
            except Exception as x:
                debug("%r: type %r, value %r: %s" %
                      (self.name, self.type, value, x))
                text = str(value)
        elif self.type.startswith("{"):  # string representation of dictionary
            try:
                mapping_dict = eval(self.type)
                text = mapping_dict[value]
            except Exception as x:
                warning(f"{self.type}: {x}")
                text = str(value)
        else:
            if self.type:
                warning(f"unknown type {self.type!r}")
            if is_numeric(value) and isnan(value):
                text = ""
            elif type(value) == str:
                text = value
            elif type(value) == bool:
                text = "On" if value else "Off"
            elif self.format:
                try:
                    text = self.format % value
                except (ValueError, TypeError, ArithmeticError):
                    text = ""
            else:
                text = str(value)

        if self.unit and text not in ["", "-"]:
            text += " " + self.unit
        # debug(f"{self}: {value} formatted as {text!r}")
        return text

    def formatted_choices(self, choices):
        """Choices as text"""
        if self.type.startswith("time") or self.type.startswith("frequency"):
            from numpy import asarray, concatenate, arange, unique
            from time_string import time_string
            precision = self.type.split(".")[-1][0]
            try:
                precision = int(precision)
            except (ValueError, TypeError):
                precision = 3
            if self.type.startswith("time"):
                def my_format(x):
                    return time_string(x, precision)
            else:
                def my_format(x):
                    from div import div
                    return to_SI_format(div(1,x), precision) + "Hz"
            choices = asarray(choices)
            if len(choices) == 0:
                choices = concatenate(([0], 10 ** (arange(-11, 1, 0.25))))
            if "delay" in self.name and hasattr(self.object, "next_delay"):
                choices = unique([self.object.next_delay(t) for t in choices])
            choices = [my_format(t) for t in choices]
        elif self.type == "date":
            pass
        elif self.type == "binary":
            pass
        elif self.type == "bool":
            choices = ["True", "False"]
        elif self.type == "int":
            choices = [str(choice) for choice in choices]
            if len(choices) == 0:
                choices = ["0"]
        elif self.type == "float":
            format_str = self.format if self.format else "%g"
            formatted_choices = []
            for value in choices:
                try:
                    text = format_str % value
                except (ValueError, TypeError, ArithmeticError) as x:
                    debug(f"{self.object}.{self.name}: {format_str!r} % {value!r}: {x}")
                else:
                    formatted_choices.append(text)
            choices = formatted_choices
        elif "/" in self.type:  # list of names
            choices = self.type.split("/")
        elif self.type.startswith("{"):  # string representation of dictionary
            try:
                mapping_dict = eval(self.type)
                if not choices:
                    choices = list(mapping_dict.values())
            except Exception as x:
                warning(f"{self.type}: {x}")

        choices = [str(x) for x in choices]

        if self.unit:
            formatted_choices = []
            for text in choices:
                if text not in ["", "-"]:
                    text += " " + self.unit
                formatted_choices.append(text)
            choices = formatted_choices
        return choices

    @property
    def choices(self):
        if self.choices_value is not None:
            choices = self.choices_value
        elif self.choices_reference is not None:
            choices = self.choices_reference.value
        elif "/" in self.type:  # list of names
            choices = self.type.split("/")
        elif self.type.startswith("{"):  # dictionary
            try:
                mapping_dict = eval(self.type)
                choices = list(mapping_dict.values())
            except Exception as x:
                warning(f"{self.type}: {x}")
                choices = []
        elif self.type == "bool":
            choices = [True, False]
        elif self.type == "int":
            choices = [0]
        else:
            choices = []
        return choices

    @property
    def has_choices(self):
        if self.choices_value is not None:
            has_choices = True
        elif self.choices_reference is not None:
            has_choices = True
        elif "/" in self.type:  # list of names
            has_choices = True
        elif self.type == "bool":
            has_choices = True
        elif self.type == "int":
            has_choices = True
        elif self.type.startswith("{"):  # string representation of dictionary
            has_choices = True
        else:
            has_choices = False
        return has_choices

    def OnChange(self, _event):
        from numpy import nan  # needed for "eval"
        text = str(self.Current.Value)
        text = text.replace(self.unit, "")
        text = text.rstrip()  # ignore trailing blanks
        if self.type.startswith("time") or self.type.startswith("frequency"):
            if not self.type.startswith("frequency"):
                from time_string import seconds
                value = seconds(text)
            else:
                from div import div
                value = div(1, from_SI_format(text.replace("Hz", "")))
        elif self.type == "binary":
            # If both decimal and binary values are given,
            # use the value that has been modified as the nwe value.
            if "(0b" in text:
                i = text.index("(0b")
                text1, text2 = text[0:i], text[i:]
                try:
                    value1, value2 = int(eval(text1)), int(eval(text2))
                except Exception as msg:
                    debug("%r" % msg)
                    return
                old_value = getattr(self.object, self.name)
                value = value1 if value1 != old_value else value2
            else:
                try:
                    value = int(eval(text))
                except Exception:
                    return
        elif self.type == "bool":
            value = (text == "True")
        elif self.type == "int":
            if text == "":
                value = nan
            else:
                try:
                    value = int(eval(text))
                except Exception:
                    return
        elif self.type == "float":
            if text == "":
                value = nan
            else:
                try:
                    value = float(eval(text))
                except Exception:
                    return
        elif "/" in self.type:  # list of choices
            choices = self.type.split("/")
            try:
                value = choices.index(text)
            except Exception:
                try:
                    value = eval(text)
                except Exception:
                    return
        elif self.type.startswith("{"):  # string representation of dictionary
            try:
                mapping_dict = eval(self.type)
                inv_map = {v: k for k, v in mapping_dict.items()}
                value = inv_map[text]
            except Exception as x:
                warning(f"{self.type}: {x}")
                return
        else:
            old_value = getattr(self.object, self.name)
            if type(old_value) == str:
                value = text
            elif type(old_value) == bool:
                value = (text == "True")
            else:
                try:
                    value = eval(text)
                except Exception:
                    return

        from threading import Thread
        if not self.changing:
            thread = Thread(target=self.change, args=(value,))
            thread.daemon = True
            self.changing = True
            thread.start()

    def change(self, value):
        """If the control has changed apply the change to the object is
        is controlling."""
        try:
            debug("Starting %r.%s = %r..." % (self.object, self.name, value))
            try:
                setattr(self.object, self.name, value)
            except Exception:
                error(format_exc())
            debug("Finished %r.%s = %r" % (self.object, self.name, value))
            self.changing = False
        except RuntimeError:
            pass


def is_numeric(value):
    try:
        value+0
    except Exception:
        is_numeric = False
    else:
        is_numeric = True
    return is_numeric


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s, line %(lineno)d: %(funcName)s: %(message)s"
    from redirect import redirect

    redirect("Control_Panel", format=msg_format)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = BasePanel()
    app.MainLoop()
