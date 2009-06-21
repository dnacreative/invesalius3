#--------------------------------------------------------------------------
# Software:     InVesalius - Software de Reconstrucao 3D de Imagens Medicas
# Copyright:    (C) 2001  Centro de Pesquisas Renato Archer
# Homepage:     http://www.softwarepublico.gov.br
# Contact:      invesalius@cti.gov.br
# License:      GNU - GPL 2 (LICENSE.txt/LICENCA.txt)
#--------------------------------------------------------------------------
#    Este programa e software livre; voce pode redistribui-lo e/ou
#    modifica-lo sob os termos da Licenca Publica Geral GNU, conforme
#    publicada pela Free Software Foundation; de acordo com a versao 2
#    da Licenca.
#
#    Este programa eh distribuido na expectativa de ser util, mas SEM
#    QUALQUER GARANTIA; sem mesmo a garantia implicita de
#    COMERCIALIZACAO ou de ADEQUACAO A QUALQUER PROPOSITO EM
#    PARTICULAR. Consulte a Licenca Publica Geral GNU para obter mais
#    detalhes.
#--------------------------------------------------------------------------
import sys

import wx
import wx.aui
import wx.lib.pubsub as ps
import math

import default_tasks as tasks
import default_viewers as viewers


[ID_NEW, ID_OPEN, ID_FULLSCREEN] = [wx.NewId() for number in range(3)]

class Frame(wx.Frame):
    def __init__(self, prnt):
        wx.Frame.__init__(self, id=-1, name='', parent=prnt,
              pos=wx.Point(0, 0),
              size=wx.Size(1024, 768), #size = wx.DisplaySize(),
              style=wx.DEFAULT_FRAME_STYLE, title='InVesalius 3.0')
        self.Center(wx.BOTH)
        self.SetIcon(wx.Icon("../icons/invesalius.ico", wx.BITMAP_TYPE_ICO))

        # Set menus, status and task bar
        self.SetMenuBar(MenuBar(self))
        self.SetStatusBar(StatusBar(self))

        # TEST: Check what happens in each OS when starting widget bellow
        # win32:  Show icon at "Notification Area" on "Task Bar"
        # darwin: Show icon on Dock
        # linux2: ? - TODO: find what it does
        #TaskBarIcon(self)

        # Create aui manager and insert content in it
        self.__init_aui()

        # Initialize bind to pubsub events
        self.__bind_events()


    def __bind_events(self):
        ps.Publisher().subscribe(self.ShowContentPanel, 'Show content panel')
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def __init_aui(self):

        # Tell aui_manager to manage this frame
        aui_manager = wx.aui.AuiManager()
        aui_manager.SetManagedWindow(self)

        # Add panels to manager
        aui_manager.AddPane(tasks.Panel(self), wx.aui.AuiPaneInfo().
                          Name("Tasks").CaptionVisible(False))
                          # TEST: Check if above works well in all supported OS
                          # or if we nwwd to insert information bellow
                          #Caption("Task panel").CaptionVisible(False)).
                          #CloseButton(False).Floatable(False).
                          #Layer(1).Left().MaximizeButton(False).Name("Task").
                          #Position(0))

        aui_manager.AddPane(viewers.Panel(self), wx.aui.AuiPaneInfo().
                          Caption("Data panel").CaptionVisible(False).
                          Centre().CloseButton(False).Floatable(False).
                          Hide().Layer(1).MaximizeButton(True).Name("Data").
                          Position(1))


        # Add toolbars to manager

        aui_manager.AddPane(ObjectToolBar(self), wx.aui.AuiPaneInfo().
                          Name("General Features Toolbar").
                          ToolbarPane().Top().Floatable(False).
                          LeftDockable(False).RightDockable(False))

        #aui_manager.AddPane(LayoutToolBar(self), wx.aui.AuiPaneInfo().
        #                  Name("Layout Toolbar").
        #                  ToolbarPane().Top().Floatable(False).
        #                  LeftDockable(False).RightDockable(False))

        aui_manager.AddPane(ProjectToolBar(self), wx.aui.AuiPaneInfo().
                          Name("Project Toolbar").
                          ToolbarPane().Top().Floatable(False).
                          LeftDockable(False).RightDockable(False))


        aui_manager.Update()

        self.perspective_all = aui_manager.SavePerspective()

        self.aui_manager = aui_manager


    def ShowContentPanel(self, evt_pubsub):
        aui_manager = self.aui_manager
        aui_manager.GetPane("Data").Show(1)
        aui_manager.Update()

    def OnSize(self, evt):
       ps.Publisher().sendMessage(('ProgressBar Reposition'))
       evt.Skip()


    #def OnClose(self):
    #    # TODO: implement this, based on wx.Demo
    #    pass
# ------------------------------------------------------------------------------
# TODO: what will appear on ivMenuBar?
# Menu items ID's, necessary to bind events on them


class MenuBar(wx.MenuBar):
    def __init__(self, parent=None):
        wx.MenuBar.__init__(self)

        self.parent = parent

        self.__init_items()
        self.__bind_events()

    def __init_items(self):

        file_menu = wx.Menu()
        file_menu.Append(ID_NEW, "New")
        file_menu.Append(ID_OPEN, "Open")
        file_menu.Append(wx.ID_EXIT, "Exit")

        view_menu = wx.Menu()
        view_menu.Append(ID_FULLSCREEN, "Fullscreen")

        tools_menu = wx.Menu()

        options_menu = wx.Menu()

        help_menu = wx.Menu()

        # TODO: Check what is necessary under MacOS to show Groo and not Python
        # first menu item... Didn't manage to solve it up to now, the 3 lines
        # bellow are a frustated test, based on wxPython Demo
        # TODO: Google about this
        test_menu = wx.Menu()
        test_item = test_menu.Append(-1, '&About Groo', 'Groo RULES!!!')
        wx.App.SetMacAboutMenuItemId(test_item.GetId())

        self.Append(file_menu, "File")
        self.Append(view_menu, "View")
        self.Append(tools_menu, "Tools")
        self.Append(options_menu, "Options")
        self.Append(help_menu, "Help")

    def __bind_events(self):
        # TODO: in future, possibly when wxPython 2.9 is available,
        # events should be binded directly from wx.Menu / wx.MenuBar
        # message "Binding events of wx.MenuBar" on [wxpython-users]
        # mail list in Oct 20 2008
        self.parent.Bind(wx.EVT_MENU, self.OnNew, id=ID_NEW)
        self.parent.Bind(wx.EVT_MENU, self.OnOpen, id=ID_OPEN)

    def OnNew(self, event):
        print "New"
        ps.Publisher().sendMessage(('NEW PROJECT'))
        event.Skip()

    def OnOpen(self, event):
        print "Open"
        event.Skip()

# ------------------------------------------------------------------------------
class ProgressBar(wx.Gauge):

   def __init__(self, parent):
      wx.Gauge.__init__(self, parent, -1, 100)
      self.parent = parent
      self.Reposition()
      self.__bind_events()

   def __bind_events(self):
      ps.Publisher().subscribe(self.Reposition, 'ProgressBar Reposition')
      
   def UpdateValue(self, value):
      #value = int(math.ceil(evt_pubsub.data[0]))
      self.SetValue(int(value))

      if (value >= 99):
         self.SetValue(0)

      self.Refresh()
      self.Update()

   def Reposition(self, evt_pubsub = None):
      rect = self.Parent.GetFieldRect(2)
      self.SetPosition((rect.x + 2, rect.y + 2))
      self.SetSize((rect.width - 4, rect.height - 4))

# ------------------------------------------------------------------------------
class StatusBar(wx.StatusBar):
    def __init__(self, parent):
        wx.StatusBar.__init__(self, parent, -1)
        self.SetFieldsCount(3)
        self.SetStatusWidths([-2,-2,-1])
        self.SetStatusText("Ready", 0)
        self.SetStatusText("Welcome to InVesalius 3.0", 1)
        self.SetStatusText("", 2)
        
        self.progress_bar = ProgressBar(self)
        
        self.__bind_events()
        
    def __bind_events(self):
        ps.Publisher().subscribe(self.UpdateStatus, 'Update status in GUI')
        ps.Publisher().subscribe(self.UpdateStatusLabel,
                                 'Update status text in GUI')
        
    def UpdateStatus(self, pubsub_evt):
        value, label = pubsub_evt.data
        self.progress_bar.UpdateValue(value)
        self.SetStatusText(label, 0)
        
    def UpdateStatusLabel(self, pubsub_evt):
        label = pubsub_evt.data
        self.SetStatusText(label, 0)
        

# ------------------------------------------------------------------------------

class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self, parent=None):
        wx.TaskBarIcon.__init__(self)
        self.frame = parent

        icon = wx.Icon("../icons/invesalius.ico", wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon, "InVesalius")
        self.imgidx = 1

        # bind some events
        self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnTaskBarActive)

    def OnTaskBarActivate(self):
        pass

# ------------------------------------------------------------------------------

class ProjectToolBar(wx.ToolBar):
    # TODO: what will appear in menubar?
    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize, wx.TB_FLAT|wx.TB_NODIVIDER)
        if sys.platform == 'darwin':
            self._size = 25
        else:
            self._size = 16
        self.SetToolBitmapSize(wx.Size(self._size,self._size))
        self.parent = parent
        self.__init_items()
        self.__bind_events()

    def __init_items(self):

        BMP_IMPORT = wx.Bitmap("../icons/file_import.png", wx.BITMAP_TYPE_PNG)
        BMP_EXPORT = wx.Bitmap("../icons/file_export.png", wx.BITMAP_TYPE_PNG)
        BMP_NET = wx.Bitmap("../icons/file_from_internet.png", wx.BITMAP_TYPE_PNG)
        BMP_SAVE = wx.Bitmap("../icons/file_save.png", wx.BITMAP_TYPE_PNG)
        
        if sys.platform != 'darwin':
            bmp_list = [BMP_IMPORT, BMP_EXPORT, BMP_NET, BMP_SAVE]
            for bmp in bmp_list:
                bmp.SetWidth(self._size)
                bmp.SetHeight(self._size)

        self.AddLabelTool(101, "Import medical image...", BMP_IMPORT)
        self.AddLabelTool(101, "Export data.", BMP_EXPORT)
        self.AddLabelTool(101, "Load medical image...", BMP_NET)
        self.AddLabelTool(101, "Save InVesalius project", BMP_SAVE)

        self.Realize()

    def __bind_events(self):
        pass
        
class ObjectToolBar(wx.ToolBar):
    # TODO: what will appear in menubar?
    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize, wx.TB_FLAT|wx.TB_NODIVIDER)
        if sys.platform == 'darwin':
            self._size = 25
        else:
            self._size = 16
        self.SetToolBitmapSize(wx.Size(self._size,self._size))
        
        self.parent = parent
        self.__init_items()
        self.__bind_events()

    def __init_items(self):

        #BMP_ROTATE = wx.Bitmap("../icons/tool_rotate.gif", wx.BITMAP_TYPE_GIF)
        #BMP_TRANSLATE = wx.Bitmap("../icons/tool_translate.gif", wx.BITMAP_TYPE_GIF)
        BMP_ZOOM = wx.Bitmap("../icons/tool_zoom.png", wx.BITMAP_TYPE_PNG)
        BMP_PHOTO = wx.Bitmap("../icons/tool_photo.png", wx.BITMAP_TYPE_PNG)
        BMP_PRINT = wx.Bitmap("../icons/tool_print.png", wx.BITMAP_TYPE_PNG)

        if sys.platform != 'darwin':
            bmp_list = [BMP_ZOOM, BMP_PHOTO, BMP_PRINT]
            for bmp in bmp_list:
                bmp.SetWidth(self._size)
                bmp.SetHeight(self._size)

        #self.AddLabelTool(101, "Rotate image", BMP_ROTATE)
        #self.AddLabelTool(101, "Translate image", BMP_TRANSLATE)        
        self.AddLabelTool(101, "Zoom image", BMP_ZOOM)
        self.AddLabelTool(101, "Take photo of screen", BMP_PHOTO)
        self.AddLabelTool(101, "Print screen", BMP_PRINT)

        self.Realize()

    def __bind_events(self):
        pass

class LayoutToolBar(wx.ToolBar):
    # TODO: what will appear in menubar?
    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent, -1, wx.DefaultPosition, wx.DefaultSize, wx.TB_FLAT|wx.TB_NODIVIDER)
        if sys.platform == 'darwin':
            self._size = 25
        else:
            self._size = 16
        self.SetToolBitmapSize(wx.Size(self._size,self._size))
        
        self.parent = parent
        self.__init_items()
        self.__bind_events()

    def __init_items(self):

        BMP_ROTATE = wx.Bitmap("../icons/layout_data_only.png", wx.BITMAP_TYPE_PNG)
        BMP_TRANSLATE = wx.Bitmap("../icons/layout_full.png", wx.BITMAP_TYPE_PNG)

        if sys.platform != 'darwin':
            bmp_list = [BMP_ROTATE, BMP_TRANSLATE]
            for bmp in bmp_list:
                bmp.SetWidth(self._size)
                bmp.SetHeight(self._size)
            
        #BMP_ZOOM = wx.Bitmap("../icons/tool_zoom.png", wx.BITMAP_TYPE_PNG)
        #BMP_PHOTO = wx.Bitmap("../icons/tool_photo.png", wx.BITMAP_TYPE_PNG)
        #BMP_PRINT = wx.Bitmap("../icons/tool_print.png", wx.BITMAP_TYPE_PNG)

        self.AddLabelTool(101, "Rotate image", BMP_ROTATE)
        self.AddLabelTool(101, "Translate image", BMP_TRANSLATE)        
        #self.AddLabelTool(101, "Zoom image", BMP_ZOOM)
        #self.AddLabelTool(101, "Take photo of screen", BMP_PHOTO)
        #self.AddLabelTool(101, "Print screen", BMP_PRINT)

        self.Realize()

    def __bind_events(self):
        pass