import wx
import wx.adv
import numpy as np
import wget
from datetime import timedelta, datetime
from PIL import Image
from io import BytesIO
import sys
import os
import requests
from multiprocessing import Process
import multiprocessing
import glob
#pyinstaller command:
#pyinstaller --icon=Earth.ico --onefile --add-data="Earth.png;./" --windowed HimawariDownloaderGUI.py

def download_helper(link):
    url, path = link
    print('link', link, 'url', url, 'path', path)
    filename = wget.download(url, path)


class HimawariDownloader():
    def __init__(self):
        self.filepath = os.getcwd() + '/'
        self.base_url = 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/{1}d/550/{0:%Y/%m/%d/%H%M%S}_{2}_{3}.png'
        self.band_url = 'http://himawari8-dl.nict.go.jp/himawari8/img/FULL_24h/B{4:02d}/{1}d/550/{0:%Y/%m/%d/%H%M%S}_{2}_{3}.png'
        self.temp_thumbnail = 'temp-Him8-thumb'
        sessiontime=datetime.now()
        self.temp_thumbnail_name = 'thumbnail_{0:%Y-%m-%d_%H%M%S}'.format(sessiontime)
        self.Result_folder = 'Result-Him8_{0:%Y-%m-%d_%H%M%S}'.format(sessiontime)
        self.Band=0
        self.createFolder(self.Result_folder)
        self.timestep = 10

    def SetBand(self,band):
        self.Band=band

    def SetStartDate(self, year, month, day, hour, minutes):
        self.start_date = datetime(year, month, day, hour, minutes, 0)

    def createFolder(self, dirName):
        if not os.path.exists(self.filepath + dirName):
            os.mkdir(self.filepath + dirName)


    def resultFolder(self):
        return self.filepath + self.Result_folder

    def LoadThumbnail(self):
        with requests.Session() as session:
            #print(self.band_url.format(self.start_date, 1, 0, 0, self.Band))
            #im=BytesIO(session.get(self.band_url.format(self.start_date, 1, 0, 0, self.Band)).content)
            #print(im)



            if self.Band:
                img = Image.new('RGBA', (550, 550), (0, 0, 0, 0))
                # text_img.paste(bg, (0, 0))
                # Image.frombytes('LA', (550,550), data
                img = Image.open(
                    BytesIO(session.get(self.band_url.format(self.start_date, 1, 0, 0, self.Band)).content))
                #img_data.show()
                #print(img_data)
                #img_data.draft("L", (550, 550))
                #print(img_data)
                #img.paste(img_data.split()[0], (0, 0), mask=img_data.split()[1])
                #print(img_data.split()[0])
            else:
                img = Image.open(BytesIO(session.get(self.base_url.format(self.start_date, 1, 0, 0)).content))
            # print(img)
            return img

    def StartDownload(self, frames, startframe, resolution, from_x=0, number_x=1, from_y=0, number_y=1):
        info_file = open(self.filepath + self.Result_folder+"/ImageInfos.txt", "a+")
        info_file.write("# This file contains the time information of all images. First column is the image name, the second column is the date and time in the format YYYY-MM-DD-HHMMSS.")
        info_file.close()
        for it in range(startframe - 1, frames):
            if not self.__download(self.start_date + timedelta(minutes=self.timestep * it), resolution, it + 1, self.Result_folder,
                                   from_x, number_x, from_y, number_y):
                return False
            info_file = open(self.filepath + self.Result_folder+"/ImageInfos.txt", "a+")
            info_file.write("\n{0}\t{1:%Y-%m-%d-%H%M%S}".format(it + 1,self.start_date + timedelta(minutes=self.timestep * it)))
            info_file.close()

        return True

    def __download(self, time, resolution, name, destination, from_x=0, number_x=1, from_y=0, number_y=1):
        tiles_x = np.arange(number_x) + from_x
        tiles_y = np.arange(number_y) + from_y
        with requests.Session() as session:
            if self.Band:
                images = [
                    [Image.open(BytesIO(session.get(self.band_url.format(time, resolution, x, y, self.Band)).content))
                     for x in tiles_x] for y in tiles_y]
            else:
                images = [
                    [Image.open(BytesIO(session.get(self.base_url.format(time, resolution, x, y)).content))
                     for x in tiles_x] for y in tiles_y]
            self.__mergeImages(images, name, destination, tiles_x, tiles_y)
        return True


    def __mergeImages(self, images, name, destination, tiles_x=np.array([0]), tiles_y=np.array([0])):
        total_width = 550 * tiles_x.size
        max_height = 550 * tiles_y.size

        new_im = Image.new('RGBA', (total_width, max_height))
        for x in np.arange(tiles_x.size):
            x_offset = x * 550
            for y in np.arange(tiles_y.size):
                y_offset = y * 550
                new_im.paste(images[y][x], (x_offset, y_offset))
        if isinstance(name, int):
            new_im.save(self.filepath + destination + '/{0:04d}.png'.format(name))
        else:
            new_im.save(self.filepath + destination + '/{0}.png'.format(name))


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetClientSize((600, 700))
        self.datepicker_ctrl_1 = wx.adv.DatePickerCtrl(self, wx.ID_ANY)
        self.choice_Hour = wx.Choice(self, wx.ID_ANY,
                                     choices=["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12",
                                           "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23"])
        self.choice_Minutes = wx.Choice(self, wx.ID_ANY, choices=["00", "10", "20", "30", "40", "50"])
        self.button_UpdateImage = wx.Button(self, wx.ID_ANY, "Update Image")
        self.choice_Tiles = wx.Choice(self, wx.ID_ANY, choices=["1x1", "2x2", "4x4", "8x8", "16x16", "20x20"])
        self.choice_Bands = wx.Choice(self, wx.ID_ANY, choices=['RGB', '00.47µm BLUE', '00.51µm GREEN', '00.64µm RED',
                                                                '00.86µm Near-IR', '01.60µm Near-IR', '02.30µm Near-IR',
                                                                '03.90µm Short-IR', '06.20µm Mid-IR', '06.90µm Mid-IR',
                                                                '07.30µm Mid-IR', '08.60µm Far-IR', '09.60µm Far-IR',
                                                                '10.40µm Far-IR', '11.20µm Far-IR', '12.40µm Far-IR',
                                                                '13.30µm Far-IR'])
        self.spin_ctrl_Frames = wx.SpinCtrl(self, wx.ID_ANY, "100", min=1, max=9999)
        self.spin_ctrl_StartFrame = wx.SpinCtrl(self, wx.ID_ANY, "1", min=1, max=9999)
        self.button_Download = wx.Button(self, wx.ID_ANY, "Download")
        self.choice_time_step = wx.Choice(self, wx.ID_ANY, choices=["10m", "30m", "1h", "3h", "6h", "12h", "24h"])
        self.timer = wx.Timer(self)
        self.thumbnail=None
        icon = wx.Icon()
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        elif __file__:
            application_path = os.path.dirname(__file__)
        icon.CopyFromBitmap(wx.Bitmap(application_path+'/Earth.png', wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.allItems = [self.choice_time_step, self.choice_Bands, self.datepicker_ctrl_1, self.choice_Hour, self.choice_Minutes, self.button_UpdateImage, self.choice_Tiles, self.spin_ctrl_Frames, self.spin_ctrl_StartFrame, self.button_Download]
        self.HimawariDownloader = HimawariDownloader()
        self.thumbnail = ''
        self.downloading = False
        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_TIMER, self.update, self.timer)

        self.Bind(wx.EVT_CHOICE, self.choice_Timestep, self.choice_time_step)
        self.Bind(wx.EVT_CHOICE, self.BandChanged, self.choice_Bands)
        self.Bind(wx.adv.EVT_DATE_CHANGED, self.DateChanged, self.datepicker_ctrl_1)
        self.Bind(wx.EVT_CHOICE, self.HourChanged, self.choice_Hour)
        self.Bind(wx.EVT_CHOICE, self.MinutesChanged, self.choice_Minutes)
        self.Bind(wx.EVT_BUTTON, self.UpdateImage, self.button_UpdateImage)
        self.Bind(wx.EVT_CHOICE, self.ResolutionChanged, self.choice_Tiles)
        self.Bind(wx.EVT_BUTTON, self.DownloadStart, self.button_Download)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def __set_properties(self):
        self.SetTitle("frame")
        self.choice_time_step.SetSelection(0)
        self.choice_Hour.SetSelection(2)
        self.choice_Bands.SetSelection(0)
        self.choice_Minutes.SetSelection(0)
        self.button_UpdateImage.SetMinSize((-1, 23))
        self.choice_Tiles.SetSelection(5)
        self.datepicker_ctrl_1.SetValue(wx.DateTime.Today().Add(wx.DateSpan(days=-1)))
        self.isPressed = False
        self.tile_number = 20
        self.startPos = wx.Point(0, 0)
        self.endPos = self.startPos
        self.Tiles2Pixel()
        self.Bind(wx.EVT_MOTION, self.ImageCtrl_OnMouseMove)
        self.Bind(wx.EVT_LEFT_DOWN, self.ImageCtrl_OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.ImageCtrl_OnMouseUp)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.setStartDate()

    def __do_layout(self):
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)#middle sizer
        sizer_5 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)

        #fist sizer
        sizer_3.Add(self.datepicker_ctrl_1, 0, wx.ALIGN_CENTER | wx.ALL, 4)
        sizer_3.Add(self.choice_Hour, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.LEFT | wx.TOP, 4)
        label_2 = wx.StaticText(self, wx.ID_ANY, ":")
        sizer_3.Add(label_2, 0, wx.ALIGN_CENTER, 0)
        sizer_3.Add(self.choice_Minutes, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT | wx.TOP, 4)
        sizer_3.Add(self.choice_Bands, 0, wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM | wx.RIGHT | wx.TOP, 4)
        sizer_3.Add(self.button_UpdateImage, 0, wx.ALIGN_CENTER | wx.ALL, 4)
        self.label_2_1 = wx.StaticText(self, wx.ID_ANY, "Output resolution: 0x0")
        #second sizer
        sizer_1.Add(self.choice_Tiles, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        sizer_1.Add(self.label_2_1, 0, wx.ALIGN_CENTER, 0)
        #third sizer
        sizer_4.Add(wx.StaticText(self, wx.ID_ANY, "Timestep:"),0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        sizer_4.Add(self.choice_time_step, 0, wx.ALIGN_CENTER | wx.ALL, 4)
        label_3 = wx.StaticText(self, wx.ID_ANY, "Number of Frames:")
        sizer_4.Add(label_3, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        sizer_4.Add(self.spin_ctrl_Frames, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        label_4 = wx.StaticText(self, wx.ID_ANY, "Start at Frame:")
        sizer_4.Add(label_4, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        sizer_4.Add(self.spin_ctrl_StartFrame, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)

        sizer_2.Add(sizer_3, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
        sizer_2.Add(sizer_1, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
        sizer_2.Add(sizer_4, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 0)
        #forth sizer
        self.empty_box = sizer_2.Add((550, 550), 0, wx.ALIGN_CENTER | wx.ALL, 0)
        sizer_5.Add(self.button_Download, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 4)
        self.loadingBar = wx.Gauge(self, id=wx.ID_ANY, size=(400, 23))
        sizer_5.Add(self.loadingBar, 0, wx.ALIGN_CENTER, 0)  # Ladebalken
        self.label_5 = wx.StaticText(self, wx.ID_ANY, "0.0%")
        sizer_5.Add(self.label_5, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT | wx.ALL, 4)


        sizer_2.Add(sizer_5, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_2)
        self.Layout()
        self.UpdateImage(None)
        self.drawRectangle()

    def setStartDate(self):
        self.HimawariDownloader.SetStartDate(self.datepicker_ctrl_1.GetValue().GetYear(),
                                             self.datepicker_ctrl_1.GetValue().GetMonth() + 1,
                                             self.datepicker_ctrl_1.GetValue().GetDay(),
                                             self.choice_Hour.GetSelection(),
                                             self.choice_Minutes.GetSelection() * 10)
        self.HimawariDownloader.SetBand(self.choice_Bands.GetSelection())

    def BandChanged(self, event):
        self.choice_Tiles.Clear()
        if self.choice_Bands.GetSelection():
            self.choice_Tiles.AppendItems(["1x1", "2x2", "4x4", "8x8", "10x10"])
        else:
            self.choice_Tiles.AppendItems(["1x1", "2x2", "4x4", "8x8", "16x16", "20x20"])
        self.choice_Tiles.SetSelection(self.choice_Tiles.GetCount()-1)
        self.ResolutionChanged(None)
        event.Skip()

    def choice_Timestep(self, event):
        #["10m", "30m", "1h", "3h", "6h", "12h", "24h"]
        possible_choices=[10, 30, 60, 180, 360, 720, 1440]
        self.HimawariDownloader.timestep = possible_choices[self.choice_time_step.GetSelection()]

    def DateChanged(self, event):  # wxGlade: MyFrame.<event_handler>
        # print("Event handler 'DateChanged' not implemented!")
        event.Skip()

    def HourChanged(self, event):  # wxGlade: MyFrame.<event_handler>
        # print("Event handler 'HourChanged' not implemented!")
        event.Skip()

    def MinutesChanged(self, event):  # wxGlade: MyFrame.<event_handler>
        # print("Event handler 'MinutesChanged' not implemented!")
        event.Skip()

    def UpdateImage(self, event):  # wxGlade: MyFrame.<event_handler>
        if self.downloading:
            return
        self.setStartDate()
        self.thumbnail=self.HimawariDownloader.LoadThumbnail()
        # print(self.thumbnail)
        if not self.thumbnail is None:
            self.drawRectangle()

    def ResolutionChanged(self, event):  # wxGlade: MyFrame.<event_handler>
        choice = self.choice_Tiles#event.GetEventObject()
        if choice.GetCount() == 6:
            possible_values = [1, 2, 4, 8, 16, 20]
        else:
            possible_values = [1, 2, 4, 8, 10]
        self.tile_number = possible_values[choice.GetCurrentSelection()]
        self.drawRectangle()

    def DownloadStart(self, event):
        if self.downloading:
            return
        for item in self.allItems:
            item.Disable()
        self.downloading = True
        tile_x1, tile_y1, tile_x2, tile_y2 = self.GetTiles()
        self.p = Process(target=self.HimawariDownloader.StartDownload,
                         args=(self.spin_ctrl_Frames.GetValue(), self.spin_ctrl_StartFrame.GetValue(), self.tile_number,
                               tile_x1, tile_x2 - tile_x1 + 1, tile_y1, tile_y2 - tile_y1 + 1), )
        self.p.daemon=True
        self.p.start()
        self.timer.Start(1000)

    def BoundariesTiles(self, tile_number):
        return np.max([0, np.min([self.tile_number - 1, tile_number])])

    def GetTiles(self):
        tile_x1 = int(np.floor(np.min([self.startPos.x, self.endPos.x]) * self.tile_number / 550))
        tile_x2 = int(np.floor(np.max([self.startPos.x, self.endPos.x]) * self.tile_number / 550))
        tile_y1 = int(np.floor(np.min([self.startPos.y, self.endPos.y]) * self.tile_number / 550))
        tile_y2 = int(np.floor(np.max([self.startPos.y, self.endPos.y]) * self.tile_number / 550))
        return [self.BoundariesTiles(tile_x1), self.BoundariesTiles(tile_y1), self.BoundariesTiles(tile_x2),
                self.BoundariesTiles(tile_y2)]

    def Tiles2Pixel(self):
        tile_x1, tile_y1, tile_x2, tile_y2 = self.GetTiles()
        self.startPix = wx.Point(int(round(tile_x1 / self.tile_number * 550)),
                                 int(round(tile_y1 / self.tile_number * 550)))
        self.endPix = wx.Point(int(round((tile_x2 + 1) / self.tile_number * 550)),
                               int(round((tile_y2 + 1) / self.tile_number * 550)))

    def OnPaint(self, event):
        if self.thumbnail is None:
            return
        image = wx.Image(550, 550)
        image.SetData(self.thumbnail.convert("RGB").tobytes())
        image.SetAlpha(self.thumbnail.convert("RGBA").tobytes()[3::4])

        ## use the wx.Image or convert it to wx.Bitmap
        #bitmap = wx.BitmapFromImage(image)

        #bitmap=self.thumbnail.
        dc = wx.MemoryDC(wx.Bitmap(550,550))
        #    image.ConvertToBitmap())#wx.Bitmap(bitmap,550, 550, 8))
        dc.DrawBitmap(image.ConvertToBitmap(),0,0)
        dc.SetPen(wx.Pen('#f00000', 1, wx.SOLID))
        dc.SetBrush(wx.Brush("black", wx.TRANSPARENT))
        dc.DrawRectangle(self.startPix.x, self.startPix.y, self.endPix.x - self.startPix.x,
                         self.endPix.y - self.startPix.y)
        wx.PaintDC(self).Blit(self.empty_box.GetPosition().x, self.empty_box.GetPosition().y, 550, 550, dc, 0, 0)
        dc.SelectObject(wx.NullBitmap)

    def ImageCtrl_OnMouseMove(self, event):
        if self.isPressed:
            ctrl_pos = event.GetPosition() - self.empty_box.GetPosition()
            self.endPos = ctrl_pos
            self.drawRectangle()

    def ImageCtrl_OnMouseDown(self, event):
        self.isPressed = True
        ctrl_pos = event.GetPosition() - self.empty_box.GetPosition()
        self.startPos = ctrl_pos
        self.endPos = self.startPos
        self.drawRectangle()

    def ImageCtrl_OnMouseUp(self, event):
        self.isPressed = False
        ctrl_pos = event.GetPosition() - self.empty_box.GetPosition()
        self.endPos = ctrl_pos
        self.drawRectangle()

    def drawRectangle(self):
        if self.downloading:
            return
        self.Tiles2Pixel()
        tile_x1, tile_y1, tile_x2, tile_y2 = self.GetTiles()
        self.label_2_1.SetLabel(
            'Output resolution: {0}x{1}, Tiles ({2}|{3})-({4}|{5})'.format((tile_x2 - tile_x1 + 1) * 550, (tile_y2 - tile_y1 + 1) * 550,tile_x1, tile_y1, tile_x2, tile_y2))
        self.Refresh(eraseBackground=False)
        self.Update()

    def OnClose(self, event):
        if not len(os.listdir(self.HimawariDownloader.resultFolder())):
            os.rmdir(self.HimawariDownloader.resultFolder())
        event.Skip()

    def OnResize(self,event):
        self.Refresh(eraseBackground=True)
        event.Skip()

    def update(self, event):
        self.updateProgressBar()

    def updateProgressBar(self):
        self.loadingBar.SetRange(self.spin_ctrl_Frames.GetValue())
        #self.loadingBar.SetValue(len(os.listdir(self.HimawariDownloader.resultFolder())))
        self.loadingBar.SetValue(len(glob.glob(self.HimawariDownloader.resultFolder()+'/*.png')))
        self.label_5.SetLabel('{0:.1f}%'.format(100 * len(glob.glob(self.HimawariDownloader.resultFolder()+'/*.png')) / self.spin_ctrl_Frames.GetValue()))


# end of class MainFraim

class MyApp(wx.App):
    def OnInit(self):
        wx.CAPTION = True
        self.frame = MyFrame(None, wx.ID_ANY, '')
        self.SetTopWindow(self.frame)
        self.frame.Centre()
        self.frame.SetTitle('Himawari 8 Downloader - made by G4ME-TIME')
        self.frame.Show()

        return True


# end of class MyApp

if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = MyApp(0)
    app.MainLoop()
