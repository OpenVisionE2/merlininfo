# -*- coding: utf-8 -*-
#
#  MerlinInfo E2
#
#  $Id$
#
#  Coded by DarkVolli (c) 2011-2012
#  Support: www.dreambox-tools.info
#
#
###################################
#
# Edited By RAED To All Images (Added Cams name info) 01-11-2015  (Works 100% on Clone Boxes)
# Update By RAED To All Images (Supported FULL HD Skins) 14-04-2017  (Works 100% on Clone Boxes)
#
###################################
#
#  This plugin is inspirated by Vali's plugin Sherlock
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.ServiceInfo import ServiceInfo, to_unsigned
from Screens.InfoBar import InfoBar, MoviePlayer
from Screens.HelpMenu import HelpableScreen
from Components.Sources.List import List
from Components.Harddisk import harddiskmanager
from Components.Sensors import sensors
from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap
from Components.ProgressBar import ProgressBar
from Components.config import config, getConfigListEntry, ConfigSubsection
from Components.ConfigList import ConfigListScreen
from Components.config import ConfigOnOff
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN
from Tools.Transponder import ConvertToHumanReadable
from enigma import eListboxPythonMultiContent, eListbox, gFont, eTimer, getDesktop, iServiceInformation
#from bitratecalc import eBitrateCalculator
from os import listdir, popen, error as os_error
import os

config.plugins.MerlinInfo = ConfigSubsection()
config.plugins.MerlinInfo.Hotkey = ConfigOnOff(default = True)
config.plugins.MerlinInfo.ExMenu = ConfigOnOff(default = True)

mysession = None
baseHelpableScreen__init__ = None

# Thanks to Dr.Best for his help for Hotkey stuff...
def autostart(reason, **kwargs):
        global mysession, baseHelpableScreen__init__
        mysession = kwargs["session"]
        if baseHelpableScreen__init__ is None:
                baseHelpableScreen__init__ = HelpableScreen.__init__
        HelpableScreen.__init__ = HelpableScreen__init__
        config.plugins.MerlinInfo.Hotkey.addNotifier(hotkeyChanged, initial_call = False)

def HelpableScreen__init__(self):
        if (isinstance(self,InfoBar) or isinstance(self,MoviePlayer)) and config.plugins.MerlinInfo.Hotkey.value:
                self["helpActions"] = ActionMap( [ "HelpActions" ],
                        {
                                "displayHelp": showMerlinInfo,
                        })
        else:
                baseHelpableScreen__init__(self)

def hotkeyChanged(configElement = None):
        from Screens.InfoBar import InfoBar
        if configElement.value:
                InfoBar.instance["helpActions"].actions["displayHelp"] = showMerlinInfo
        else:
                InfoBar.instance["helpActions"].actions["displayHelp"] = InfoBar.instance.showHelp

def showMerlinInfo():
        mysession.open(merlinInfo)

def main(session,**kwargs):
        session.open(merlinInfo)

def Plugins(**kwargs):
        list = [PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = autostart)] 
        list.append(PluginDescriptor(name="Merlin Info", description=_("Merlin Information..."), where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main))
        if config.plugins.MerlinInfo.ExMenu.value:
                list.append(PluginDescriptor(name="Merlin Info", description=_("Merlin Information..."), where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main))
        return list

RT_HALIGN_LEFT = 0
TYPE_TEXT = 0
TYPE_VALUE_HEX = 1
TYPE_VALUE_DEC = 2
TYPE_VALUE_HEX_DEC = 3
TYPE_SLIDER = 4

from Components.GUIComponent import GUIComponent

class myInfoList(GUIComponent):
        def __init__(self, source, fontSize = 18):
                GUIComponent.__init__(self)
                self.l = eListboxPythonMultiContent()
                self.list = source
                self.l.setList(self.list)
                self.l.setFont(0, gFont("Regular", fontSize))
                self.l.setItemHeight(fontSize + 2)

        GUI_WIDGET = eListbox

        def postWidgetCreate(self, instance):
                self.instance.setContent(self.l)

# mainwindow...
class merlinInfo(Screen):
        def createVideoPictureSkinpart(self, x, y, w, h):
                skin = """<widget source="session.VideoPicture" position="%d,%d" render="Pig" size="%d,%d" zPosition="0" backgroundColor="#FF000000"/>""" % (x,y,w,h)
                return skin

        def createSysInfoSkinpart(self, x, y, w, h, fs):
                skin = """<widget render="Label" source="sysInfo" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" halign="left" transparent="1" zPosition="3"/>""" % (x,y,w,h,fs)
                self["sysInfo"] = StaticText()
                return skin

        def createServiceInfoSkinpart(self, x, y, w, h, fs):
                skin  = """<widget source="session.CurrentService" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#00fcc000" backgroundColor="#04000e" halign="left" noWrap="1" transparent="1" valign="top" zPosition="2">""" % (x,y,w,h,fs+2)
                skin += """     <convert type="ServiceName">Name</convert>"""
                skin += """</widget>"""

                y += h+2
                skin += """<widget source="session.CurrentService" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" halign="left" noWrap="1" transparent="1" zPosition="2">""" % (x,y,w,h,fs)
                skin += """     <convert type="ServiceName">Provider</convert>"""
                skin += """</widget>"""

                y += h
                skin += """<widget render="Label" source="OrbitalPosition" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" halign="left" noWrap="1" transparent="1" zPosition="2"/>""" % (x,y,w,h,fs-4)

                y += h+4
                skin += """<widget render="Label" source="ServiceInfos" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" halign="left" transparent="1" zPosition="2"/>""" % (x,y,w,h*4,fs-2)

                y += h*4
                skin += """<eLabel text="Audio Pid:" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" transparent="1" halign="left" valign="center" zPosition="2"/>""" % (x,y,w,h,fs+2)
                skin += """<widget source="session.CurrentService" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" transparent="1" halign="left" noWrap="1" valign="center" zPosition="2">""" % (x+160,y,w,h,fs+2)
                skin += """      <convert type="ServiceInfo">AudioPid</convert>"""
                skin += """</widget>"""

                y += h
                skin += """<eLabel text="Video Pid:" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" transparent="1" halign="left" valign="center" zPosition="2"/>""" % (x,y,w,h,fs+2)
                skin += """<widget source="session.CurrentService" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" transparent="1" halign="left" noWrap="1" valign="center" zPosition="2">""" % (x+160,y,w,h,fs+2)
                skin += """      <convert type="ServiceInfo">VideoPid</convert>"""
                skin += """</widget>"""

                self["OrbitalPosition"] = StaticText()
                self["ServiceInfos"] = StaticText()
                #self["VideoBitrate"] = StaticText()
                #self["AudioBitrate"] = StaticText()

                return skin

        def createFrontendInfoSkinpart(self, x, y, fs, png):
                w = 80+png*10
                h = fs+2
                skin  = """<widget source="session.FrontendStatus" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#00fcc000" backgroundColor="#04000e" halign="left" transparent="1" zPosition="2">""" % (x,y,w,h,fs)
                skin += """     <convert type="FrontendInfo">BER</convert>"""
                skin += """</widget>"""

                x1 = x+80+png*10
                w = 50+png*10
                h = fs+2
                skin += """<widget source="session.FrontendStatus" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" halign="left" transparent="1" zPosition="2">""" % (x1,y,w,h,fs)
                skin += """     <convert type="FrontendInfo">SNR</convert>"""
                skin += """</widget>"""

                x1 = x+130+png*20
                w = 100+png*10
                h = fs+2
                skin += """<widget source="session.FrontendStatus" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" halign="right" transparent="1" zPosition="2">""" % (x1,y,w,h,fs)
                skin += """     <convert type="FrontendInfo">SNRdB</convert>"""
                skin += """</widget>"""

                pixmap = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinInfo/png/ico_bar_snr%d.png" % png)
                w = 230+png*30
                h = 10+png*10
                y += fs+2
                skin += """<widget source="session.FrontendStatus" render="Progress" position="%d,%d" size="%d,%d" pixmap="%s" borderColor="#555555" borderWidth="1" backgroundColor="#04000e" zPosition="2">""" % (x,y,w,h,pixmap)
                skin += """     <convert type="FrontendInfo">SNR</convert>"""
                skin += """</widget>"""
                return skin

        def createFrontendInfoSkinpartFHD(self, x, y, fs, png):
                w = 80+png*10
                h = fs+2
                skin  = """<widget source="session.FrontendStatus" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#00fcc000" backgroundColor="#04000e" halign="left" transparent="1" zPosition="2">""" % (x,y,w,h,fs)
                skin += """     <convert type="FrontendInfo">BER</convert>"""
                skin += """</widget>"""

                x1 = x+80+png*10
                w = 50+png*10
                h = fs+2
                skin += """<widget source="session.FrontendStatus" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" halign="left" transparent="1" zPosition="2">""" % (x1,y,w,h,fs)
                skin += """     <convert type="FrontendInfo">SNR</convert>"""
                skin += """</widget>"""

                x1 = x+130+png*20
                w = 100+png*10
                h = fs+2
                skin += """<widget source="session.FrontendStatus" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" halign="right" transparent="1" zPosition="2">""" % (x1,y,w,h,fs)
                skin += """     <convert type="FrontendInfo">SNRdB</convert>"""
                skin += """</widget>"""

                pixmap = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinInfo/png2/ico_bar_snr1.png")
                w = 230+png*30
                h = 10+png*10
                y += fs+2
                skin += """<widget source="session.FrontendStatus" render="Progress" position="%d,%d" size="%d,%d" pixmap="%s" borderColor="#555555" borderWidth="1" backgroundColor="#04000e" zPosition="2">""" % (x,y,w,h,pixmap)
                skin += """     <convert type="FrontendInfo">SNR</convert>"""
                skin += """</widget>"""
                return skin

        def createInfoIconsSkinpart(self, x, y, w):
                pixmap = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinInfo/png/ico_format_on.png")
                skin  = """<widget source="session.CurrentService" pixmap="%s" position="%d,%d" render="Pixmap" size="27,20" alphatest="on" zPosition="2">""" % (pixmap,x,y)
                skin += """     <convert type="ServiceInfo">IsWidescreen</convert>"""
                skin += """     <convert type="ConditionalShowHide"/>"""
                skin += """</widget>"""

                pixmap = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinInfo/png/ico_txt_on.png")
                x += w
                skin += """<widget source="session.CurrentService" pixmap="%s" position="%d,%d" render="Pixmap" size="30,20" alphatest="on" zPosition="2">""" % (pixmap,x,y)
                skin += """     <convert type="ServiceInfo">HasTelext</convert>"""
                skin += """     <convert type="ConditionalShowHide"/>"""
                skin += """</widget>"""

                pixmap = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinInfo/png/ico_crypt_on.png")
                x += w
                skin += """<widget source="session.CurrentService" pixmap="%s" position="%d,%d" render="Pixmap" size="24,20" alphatest="on" zPosition="2">""" % (pixmap,x,y)
                skin += """     <convert type="ServiceInfo">IsCrypted</convert>"""
                skin += """     <convert type="ConditionalShowHide"/>"""
                skin += """</widget>"""

                pixmap = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinInfo/png/ico_dolby_on.png")
                x += w
                skin += """<widget source="session.CurrentService" pixmap="%s" position="%d,%d" render="Pixmap" size="46,20" alphatest="on" zPosition="2">""" % (pixmap,x,y)
                skin += """     <convert type="ServiceInfo">IsMultichannel</convert>"""
                skin += """     <convert type="ConditionalShowHide"/>"""
                skin += """</widget>"""
                return skin

        def createInfoIconsSkinpartFHD(self, x, y, w):
                pixmap = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinInfo/png2/ico_format_on.png")
                skin  = """<widget source="session.CurrentService" pixmap="%s" position="%d,%d" render="Pixmap" size="50,40" alphatest="on" zPosition="2">""" % (pixmap,x,y)
                skin += """     <convert type="ServiceInfo">IsWidescreen</convert>"""
                skin += """     <convert type="ConditionalShowHide"/>"""
                skin += """</widget>"""

                pixmap = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinInfo/png2/ico_txt_on.png")
                x += w
                skin += """<widget source="session.CurrentService" pixmap="%s" position="%d,%d" render="Pixmap" size="60,40" alphatest="on" zPosition="2">""" % (pixmap,x,y)
                skin += """     <convert type="ServiceInfo">HasTelext</convert>"""
                skin += """     <convert type="ConditionalShowHide"/>"""
                skin += """</widget>"""

                pixmap = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinInfo/png2/ico_crypt_on.png")
                x += w
                skin += """<widget source="session.CurrentService" pixmap="%s" position="%d,%d" render="Pixmap" size="40,40" alphatest="on" zPosition="2">""" % (pixmap,x,y)
                skin += """     <convert type="ServiceInfo">IsCrypted</convert>"""
                skin += """     <convert type="ConditionalShowHide"/>"""
                skin += """</widget>"""

                pixmap = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/MerlinInfo/png2/ico_dolby_on.png")
                x += w
                skin += """<widget source="session.CurrentService" pixmap="%s" position="%d,%d" render="Pixmap" size="80,40" alphatest="on" zPosition="2">""" % (pixmap,x,y)
                skin += """     <convert type="ServiceInfo">IsMultichannel</convert>"""
                skin += """     <convert type="ConditionalShowHide"/>"""
                skin += """</widget>"""
                return skin

        def createTemperatureSkinpart(self, x, y, w, h, fs):
                pcnt = len(sensors.getSensorsList(sensors.TYPE_TEMPERATURE))

                skin = ""
                if pcnt < 2:
                        skin += """<widget render="Label" source="plabel0" position="%d,%d" size="%d,%d" valign="center" halign="center" zPosition="2" transparent="1" foregroundColor="white" font="Regular;%d"/>""" % (x,y,w*8,h,fs)
                        if pcnt == 0:
                                self["plabel0"] = StaticText(_("No Mainboard Temperature Sensor avaiable..."))
                        else:
                                self["plabel0"] = StaticText()
                else:
                        for i in range(pcnt):
                                skin += """<eLabel text="S%s" position="%d,%d" size="%d,%d" font="Regular;%d" backgroundColor="#04000e" halign="center" valign="center" zPosition="2"/>\n""" % (str(i),x,y-(fs+2),w,fs+2,fs)
                                skin += """<widget name="progress%d" position="%d,%d" size="%d,%d" transparent="1" borderColor="#404040" borderWidth="1" orientation="orBottomToTop" zPosition="2" />\n""" % (i,x,y,w,h)
                                skin += """<widget render="Label" source="plabel%d" position="%d,%d" size="%d,%d" valign="center" halign="center" zPosition="3" transparent="1" foregroundColor="black" backgroundColor="white" font="Regular;%d"/>""" % (i,x,y+h-(fs+2),w,fs+2,fs)
                                x += w
                                self["progress%d" % i] = ProgressBar()
                                self["plabel%d" % i] = StaticText()
                return skin

        def createCamdNameSkinpart(self, x, y, w, h, fs, center = False):
                if center:
                        skin = """<widget source="session.CurrentService" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" zPosition="2" noWrap="1" valign="center" halign="center" foregroundColor="#00fcc000" transparent="1"  backgroundColor="#04000e">
                                     <convert type="VisionCamInfo">Camd</convert>
                                  </widget> """ % (x,y,w,h,fs)
                else:
                        skin = """<widget source="session.CurrentService" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" zPosition="2" noWrap="1" halign="left" foregroundColor="#00fcc000" transparent="1"  backgroundColor="#0e1018">
                                     <convert type="VisionCamInfo">Camd</convert>
                                  </widget>""" % (x,y,w,h,fs)
                return skin

        def createInfoFilesSkinpart(self, x, y, w, h, fs, numFiles):
                skin = ""
                for i in range(numFiles):
                        skin += """<eLabel text=" " position="%d,%d" size="%d,%d" font="Regular;20" backgroundColor="#04000e" halign="center" valign="center" zPosition="1"/>\n""" % (x,y,w-2,h)
                        skin += """<widget render="Label" source="infoFileName%d" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#00fcc000" backgroundColor="#0e1018" halign="left" transparent="2" zPosition="2"/>""" % (i,x+4,y,w-8,fs+6,fs+4)
                        self["infoFileName%d" % i] = StaticText()
                        skin += """<widget render="Label" source="infoFile%d" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#0e1018" halign="left" transparent="2" zPosition="2"/>""" % (i,x+4,y+fs+8,w-8,h-(fs+8),fs)
                        x += w+2
                        self["infoFile%d" % i] = StaticText()
                return skin

        def createFrameSkinpart(self, x, y, w, h):
                return """<eLabel text=" " position="%d,%d" size="%d,%d" backgroundColor="#04000e" zPosition="1"/>\n""" % (x,y,w,h)

        def createFrontendListSkinpart(self, x, y, w, h, w1, w2, fs):
                skin = """<widget name="infolist" position="%d,%d" size="%d,%d" selectionDisabled="1" foregroundColor="#f0f0f0" backgroundColor="#04000e" zPosition="4"/>""" % (x,y,w,h)
                self["infolist"] = myInfoList([], fs)
                # uncool: Variablen fuer die ListEntrys...
                self.W1 = w1
                self.W2 = w2
                self.H  = fs+2
                return skin

        def createHddInfoSkinpart(self, x, y, w, h, fs):
                skin = """<widget name="hddInfo" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" halign="left" transparent="0" zPosition="4"/>""" % (x,y,w,h,fs)
                self["hddInfo"] = Label("")
                return skin

        def createHddTempSkinpart(self, x, y, w, h, fs):
                skin = """<widget name="hddTemp" position="%d,%d" size="%d,%d" font="Regular;%d" foregroundColor="#f0f0f0" backgroundColor="#04000e" valign="center" halign="left" transparent="0" zPosition="4"/>""" % (x,y,w*8,h,fs)
                self["hddTemp"] = Label("")
                return skin

        def __init__(self, session, args = 0):
                sz_w = getDesktop(0).size().width()
                if sz_w == 1920:
                        part  = """<screen title="Merlin Info" flags="wfNoBorder" position="0,0" size="1920,1080" backgroundColor="#0e1018">"""
                        part += self.createVideoPictureSkinpart(90, 50, 1195, 640)
                        part += self.createFrameSkinpart(1300, 50, 550, 530)
                        part += self.createServiceInfoSkinpart(1310, 55, 540, 40, 30)
                        part += self.createInfoIconsSkinpartFHD(1310, 445, 150)
                        part += self.createFrontendInfoSkinpartFHD(1400, 495, 30, 3)
                        part += self.createFrameSkinpart(1300, 590, 550, 70)
                        part += self.createCamdNameSkinpart(1310, 595, 540, 60, 45, True)
                        part += self.createFrameSkinpart(1300, 670, 550, 390)
                        part += self.createSysInfoSkinpart(1310, 675, 540, 150, 26)
                        part += self.createTemperatureSkinpart(1300, 850, 70, 130, 30)
                        part += self.createInfoFilesSkinpart(90, 700, 600, 360, 24, 2)
                        part += self.createFrontendListSkinpart(1300, 50, 550, 530, 280, 280, 24)
                        part += self.createHddInfoSkinpart(1310, 675, 520, 180, 25)
                        part += self.createHddTempSkinpart(1310, 850, 55, 150, 25)
                elif sz_w == 1280:
                        part  = """<screen title="Merlin Info" flags="wfNoBorder" position="0,0" size="1280,720" backgroundColor="#0e1018">"""
                        part += self.createVideoPictureSkinpart(75, 30, 820, 460)
                        part += self.createFrameSkinpart(905, 30, 300, 350)
                        part += self.createServiceInfoSkinpart(915, 40, 280, 26, 22)
                        part += self.createInfoIconsSkinpart(915, 290, 75)
                        part += self.createFrontendInfoSkinpart(925, 330, 14, 1)
                        part += self.createFrameSkinpart(905, 390, 300, 60)
                        part += self.createCamdNameSkinpart(915, 390, 300, 60, 24, True)
                        part += self.createFrameSkinpart(905, 460, 300, 230)
                        part += self.createSysInfoSkinpart(915, 470, 280, 100, 18)
                        part += self.createTemperatureSkinpart(915, 580, 34, 95, 18)
                        part += self.createInfoFilesSkinpart(75, 500, 410, 190, 14, 2)
                        part += self.createFrontendListSkinpart(915, 70, 280, 310, 155, 125, 18)
                        part += self.createHddInfoSkinpart(915, 470, 280, 100, 18)
                        part += self.createHddTempSkinpart(915, 560, 34, 115, 18)
                elif sz_w == 1024:
                        part  = """<screen title="Merlin Info" flags="wfNoBorder" position="0,0" size="1024,576" backgroundColor="#0e1018">"""
                        part += self.createVideoPictureSkinpart(60, 20, 620, 340)
                        part += self.createFrameSkinpart(690, 20, 280, 300)
                        part += self.createServiceInfoSkinpart(700, 25, 260, 22, 18)
                        part += self.createInfoIconsSkinpart(700, 240, 70)
                        part += self.createFrontendInfoSkinpart(700, 275, 14, 1)
                        part += self.createFrameSkinpart(690, 326, 280, 34)
                        part += self.createCamdNameSkinpart(690, 326, 280, 34, 22, True)
                        part += self.createFrameSkinpart(690, 366, 280, 190)
                        part += self.createSysInfoSkinpart(700, 371, 260, 70, 18)
                        part += self.createTemperatureSkinpart(700, 460, 32, 88, 16)
                        part += self.createInfoFilesSkinpart(60, 366, 310, 190, 14, 2)
                        part += self.createFrontendListSkinpart(700, 50, 260, 270, 145, 115, 18)
                        part += self.createHddInfoSkinpart(700, 371, 260, 70, 18)
                        part += self.createHddTempSkinpart(700, 442, 32, 106, 16)
                else:
                        part  = """<screen title="Merlin Info" flags="wfNoBorder" position="0,0" size="720,576" backgroundColor="#0e1018">"""
                        part += self.createVideoPictureSkinpart(40, 40, 400, 300)
                        part += self.createServiceInfoSkinpart(450, 40, 230, 20, 16)
                        part += self.createInfoIconsSkinpart(450, 240, 60)
                        part += self.createFrontendInfoSkinpart(450, 275, 14, 0)
                        part += self.createCamdNameSkinpart(450, 320, 210, 24, 20)
                        part += self.createSysInfoSkinpart(450, 355, 230, 60, 16)
                        part += self.createTemperatureSkinpart(450, 455, 28, 80, 16)
                        part += self.createInfoFilesSkinpart(40, 355, 200, 180, 12, 2)
                        part += self.createFrontendListSkinpart(450, 60, 260, 250, 145, 115, 18)
                        part += self.createHddInfoSkinpart(450, 355, 230, 60, 16)
                        part += self.createHddTempSkinpart(450, 437, 28, 98, 16)
                part += """</screen>"""
                self.skin = part
                self.session = session
                Screen.__init__(self, session)

                self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "HelpActions", "MenuActions"],
                {
                        "left": self.left,
                        "right": self.right,
                        "cancel": self.close,
                        "displayHelp": self.close,
                        "up": self.nextBouquet,
                        "down": self.prevBouquet,
                        "menu": self.HotkeyDlg
                }, -1)

                self.showFile = 0
                self.loading = True
                self["infolist"].hide()
                self["hddInfo"].hide()
                self["hddTemp"].hide()
                self.refreshTimer = eTimer()
                self.refreshTimer.callback.append(self.readDynamicData)
                self.onLayoutFinish.append(self.readStaticData)

        def readStaticData(self):
                self.getServiceInfo()
                self.getSysInfo()
                #self.getCamd()
                self.getTemperature()
                self.getInfoFiles()
                self.refreshTimer.start(5000)

        def readDynamicData(self):
                self.getSysInfo()
                self.getTemperature()
                self.getInfoFiles()

        def getServiceInfo(self):
                service = self.session.nav.getCurrentService()
                if service:
                        info = service.info()
                        feinfo = service.frontendInfo()
                        caids = info.getInfoObject(iServiceInformation.sCAIDs)
                else:
                        info = None
                        feinfo = None
                width = info and info.getInfo(iServiceInformation.sVideoWidth) or -1
                height = info and info.getInfo(iServiceInformation.sVideoHeight) or -1
                if width != -1 and height != -1:
                        resolution = "Resolution: %dx%d\n" % (width, height)
                else:
                        resolution = "Resolution: N/A\n"

                caidstr = ""
                if caids != 0.0:
                        if len(caids) > 0:
                                caidstr += "caid\'s:\n"
                                for caid in caids:
                                        tmp = hex(caid).lstrip("0x")
                                        if len(tmp) < 4:
                                                tmp = "0" + tmp
                                        caidstr += tmp + ", "
                self["ServiceInfos"].setText(resolution + caidstr[:-2])

                frontendDataOrg = feinfo and feinfo.getAll(True)
                if frontendDataOrg and len(frontendDataOrg):
                        frontendData = ConvertToHumanReadable(frontendDataOrg)
                        if frontendDataOrg["tuner_type"] == "DVB-S":
                                position = frontendData["orbital_position"]
                                self["OrbitalPosition"].setText(position)

                myServiceInfo = ServiceInfo(self.session, self.session.nav.getCurrentlyPlayingServiceReference())
                FEData = myServiceInfo.getFEData(frontendDataOrg)

                tlist = [ ]
                for item in FEData:
                        if item[1] is None:
                                continue;
                        b = item[1]
                        valueType = item[2]
                        if not isinstance(b, str):
                                if valueType == TYPE_VALUE_HEX:
                                        b = ("0x%0" + str(param) + "x") % to_unsigned(b)
                                elif valueType == TYPE_VALUE_DEC:
                                        b = str(b)
                                elif valueType == TYPE_VALUE_HEX_DEC:
                                        b = ("0x%0" + str(param) + "x (%dd)") % (to_unsigned(b), b)
                                else:
                                        b = str(b)
                        a= item[0]+":"
                        t0 = (eListboxPythonMultiContent.TYPE_TEXT,       0, 0, self.W1-5, self.H, 0, RT_HALIGN_LEFT, "")
                        t1 = (eListboxPythonMultiContent.TYPE_TEXT,       0, 0, self.W1-5, self.H, 0, RT_HALIGN_LEFT, a)
                        t2 = (eListboxPythonMultiContent.TYPE_TEXT, self.W1, 0, self.W2  , self.H, 0, RT_HALIGN_LEFT, b)
                        tlist.append([t0, t1, t2])

                self["infolist"].l.setList(tlist)

                #if info:
                #                ref = self.session.nav.getCurrentlyPlayingServiceReference()
                #                vpid = apid = dvbnamespace = tsid = onid = -1
                #                vpid = info.getInfo(iServiceInformation.sVideoPID)
                #                apid = info.getInfo(iServiceInformation.sAudioPID)
                #                if not ref.getPath():
                #                       tsid = ref.getData(2)
                #                        onid = ref.getData(3)
                #                        dvbnamespace = ref.getData(4)
                #                if vpid:
                #                        self.videoBitrate = eBitrateCalculator(vpid, dvbnamespace, tsid, onid, 1000, 1024*1024)
                #                        self.videoBitrate.callback.append(self.getVideoBitrateData)
                                #if apid:
                                #        self.audioBitrate = eBitrateCalculator(apid, dvbnamespace, tsid, onid, 1000, 64*1024)
                                #        self.audioBitrate.callback.append(self.getAudioBitrateData)

        #def getVideoBitrateData(self, value, status): # value = rate in kbit/s, status ( 1  = ok || 0 = nok (zapped?))
        #        if status:
        #                self["VideoBitrate"].text = "Video: %d kbit/s" % value;
        #        else:
        #                self.videoBitrate = None

        #def getAudioBitrateData(self, value, status): 
        #        if status:
        #                self["AudioBitrate"].text = "Audio: %d kbit/s" % value;
        #        else:
        #                self.audioBitrate = None

        def getSysInfo(self):
                fd = open("/proc/loadavg")
                fread = fd.readline().split()
                fd.close()
                loadavg = "LoadAVG: " + fread[0] + " " + fread[1] + " " + fread[2]

                fd = open("/proc/meminfo")
                for line in fd.readlines():
                        if line.startswith("MemFree:"):
                                memfree = "MemFree: " + line.split(':')[1].strip()
                                break
                fd.close()

                freeflash = "Free Flash: "
                # fix error "cannot allocate memory" mit popen...
                try:
                        fd = popen("df -h")
                        for line in fd.readlines():
                                items = line.split()
                                if len(items) > 5:
                                        if items[5] == '/':
                                                freeflash += items[3] + "B used: " +  items[4]
                                                break
                        fd.close()
                except os_error, err:
                        print "[Merlin Info] popen os.error:", err
                        freeflash += "popen error"
                self["sysInfo"].setText(loadavg + "\n" + memfree + "\n" +freeflash)

                hddStr = _("Detected HDD:\n")
                hddlist = harddiskmanager.HDDList()
                hdd = hddlist and hddlist[0][1] or None
                if hdd is not None and hdd.model() != "":
                        hddStr += _("%s\n%s, %d MB free") % (hdd.model(), hdd.capacity(),hdd.free())
                        hddDeviceName = hdd.getDeviceName()
                else:
                        hddStr += _("none")
                        hddDeviceName = None
                self["hddInfo"].setText(hddStr)

                hddTemp = _("No Harddisk Temperature avaiable...")
                if hddDeviceName:
                        # fix error "cannot allocate memory" mit popen...
                        try:
                                fd = popen("smartctl -a %s | grep Temperature_Celsius" % hddDeviceName)
                                fread = fd.readline().split()
                                if len(fread) > 8:
                                        hddTemp = "Harddisk Temperature: %d °C" % int(fread[9])
                                fd.close()
                        except os_error, err:
                                print "[Merlin Info] popen os.error:", err
                                hddTemp = "Harddisk Temperature: popen error"
                self["hddTemp"].setText(hddTemp)

        def getTemperature(self):
                sensorid_list = sensors.getSensorsList(sensors.TYPE_TEMPERATURE)
                if len(sensorid_list) == 0:
                        return
                elif len(sensorid_list) == 1:
                        self["plabel0"].setText(_("Temperature")+" "+str(sensors.getSensorValue(sensorid_list[0]))+"°C")
                else:
                        for i,id in enumerate(sensorid_list):
                                self["progress%d" % i].setValue(sensors.getSensorValue(id))
                                self["plabel%d" % i].setText(str(sensors.getSensorValue(id)))

        def getInfoFiles(self):
                self.loading = True
                self.fileData = []
                cntFiles = 0

                # info files einlesen...
                files = listdir("/tmp")
                files.sort()
                # in ecm.info und ecm0.info ist der gleiche Inhalt...
                if "ecm.info" in files and "ecm0.info" in files:
                        files.remove("ecm.info")
                for fname in files:
                        fname = fname.lower()
                        if fname.endswith(".info"):
                                fdata = ""
                                try:
                                        for line in open("/tmp/" + fname).readlines():
                                                fdata += line
                                except:
                                        fdata += "no valid file found..."
                                self.fileData.append(("info%d: "%cntFiles + fname, fdata))
                                cntFiles += 1

                # rest "auffuellen", mehr als sechs info files nicht moeglich...
                for i in range(cntFiles, 6):
                        self.fileData.append(("info%d: "%i + "not found", ""))

                self.refreshInfoFiles()
                self.loading = False

        def refreshInfoFiles(self):
                for i in range(2):
                        self["infoFileName%d" % i].setText(self.fileData[self.showFile+i][0])
                        self["infoFile%d" % i].setText(self.fileData[self.showFile+i][1])

        def left(self):
                if self.loading: return
                self.showFile -= 2
                if self.showFile < 0: self.showFile = 4
                self.refreshInfoFiles()

        def right(self):
                if self.loading: return
                self.showFile += 2
                if self.showFile > 4: self.showFile = 0
                self.refreshInfoFiles()

        def nextBouquet(self):
                self["infolist"].show()
                self["hddInfo"].show()
                self["hddTemp"].show()

        def prevBouquet(self):
                self["infolist"].hide()
                self["hddInfo"].hide()
                self["hddTemp"].hide()

        def HotkeyDlg(self):
                self.session.open(hotkeyConfigScreen)

class hotkeyConfigScreen(Screen, ConfigListScreen):
        skin = """
                <screen position="center,center" size="420,160" title="Merlin Info Setup" >
                        <widget name="config" position="10,10" size="400,100" scrollbarMode="showOnDemand" />
                        <ePixmap name="ButtonRed" pixmap="buttons/red.png" position="0,120" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
                        <widget render="Label" source= "ButtonRedtext" position="0,120" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
                        <ePixmap name="ButtonGreen" pixmap="buttons/green.png" position="140,120" size="140,40" zPosition="4" transparent="1" alphatest="on"/>
                        <widget render="Label" source= "ButtonGreentext" position="140,120" size="140,40" valign="center" halign="center" zPosition="5" transparent="1" foregroundColor="white" font="Regular;18"/>
                </screen>"""

        def __init__(self, session):
                self.skin = hotkeyConfigScreen.skin
                self.session = session
                Screen.__init__(self, session)

                list = []
                list.append(getConfigListEntry(_("Hotkey HELP"), config.plugins.MerlinInfo.Hotkey))
                list.append(getConfigListEntry(_("Show Plugin in Extensions Menu"), config.plugins.MerlinInfo.ExMenu))
                ConfigListScreen.__init__(self, list, session = session)

                self["ButtonRedtext"] = StaticText(_("return"))
                self["ButtonGreentext"] = StaticText(_("save"))
                self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
                {
                        "red": self.Exit,
                        "green": self.Save,
                        "cancel": self.Exit
                }, -1)

        def Save(self):
                for x in self["config"].list:
                        x[1].save()
                self.close()

        def Exit(self):
                for x in self["config"].list:
                        x[1].cancel()
                self.close()
