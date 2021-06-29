import re
import tkinter as tk
from functools import partial
from threading import Timer
from SonosCommander import *
from SonosDetector import *
from SonosPoisoner import *
from SonosRoutiner import *
from collections import OrderedDict
from scapy.all import *

### CONSTANTS ###
THEMES = {
    "grey":{
        "MAIN_COLOR" : "#495867",
        "LIGHT_MAIN_COLOR" : "#577399",
        "CONT_COLOR" : "#f7f7ff",
        "DARK_CONT_COLOR" : "#bdd5ea",
        "CONT2_COLOR" : "#fe5f55"
    },
    "navy":{
        "MAIN_COLOR" : "#073b4c",
        "LIGHT_MAIN_COLOR" : "#118ab2",
        "CONT_COLOR" : "#06d6a0",
        "DARK_CONT_COLOR" : "#009c87",
        "CONT2_COLOR" : "#ef476f"
    },
    "dark":{
        "MAIN_COLOR" : "#252422",
        "LIGHT_MAIN_COLOR" : "#403d39",
        "CONT_COLOR" : "#fffcf2",
        "DARK_CONT_COLOR" : "#ccc5b9",
        "CONT2_COLOR" : "#eb5e28"
    }
}

WENS = "wens" #Used for sticky values


class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey'):
        super().__init__(master)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill='x', side=tk.BOTTOM)

        self.iface = conf.iface
        self.local_ip = get_if_addr(self.iface)
        self.local_mac = get_if_hwaddr(self.iface)
        self.devices = deviceScan(self.local_ip)
        self.sonos_ips = getSonosIPs(self.devices)
        self.sonos_info = getSonosInfo(self.sonos_ips)

        self.target_control = None
        self.target_vars = []
        self.target_buttons = []
        self.targets = {}

        self.target_required_buttons = []
        self.command_buttons = []
        
        self.poisontargets = []
        self.device_vars = []
        self.poison_process = None

        self.volume_timer = None

        self.recording = False
        self.routine = []
        self.routine_process = None

        
        refreshCommands()
        self.after(60000, lambda: self.updateDevices(False))
        
        self.createMenu()
        self.toggleMenu()
        self.master.bind("<Control-m>", self.toggleMenu)

        self.create_widgets()
        self.setTheme("dark")
        self.updateButtons(self.command_buttons + self.target_required_buttons)


    def create_widgets(self):
        self.left_col = tk.Frame(self, padx=5, pady=5)
        self.left_col.grid(row=0, columnspan=2, sticky=WENS)

        self.grid_columnconfigure(1, weight=1)

        self.right_col = tk.Frame(self, padx=5, pady=5)
        self.right_col.grid(row=0, column=2, columnspan=2, sticky=WENS)

        ### Playback control ###
        framerow = 0                        # Keeps track of row count for the first and second column
        rc = 0
        self.playback_control = tk.LabelFrame(self.left_col, text="Playback Control", padx=5, pady=5)
        self.playback_control.grid(row=framerow, columnspan=2, sticky=WENS)
        self.playback_control.grid_columnconfigure(0, weight=1)
        self.playback_control.grid_columnconfigure(1, weight=1)

        self.play = tk.Button(self.playback_control, text="Play", command=self.play_cmd, height=2)
        self.play.grid(row=rc, column=0, columnspan=1, sticky=WENS)
        self.pause = tk.Button(self.playback_control, text="Pause", command=self.pause_cmd, height=2)
        self.pause.grid(row=rc, column=1, columnspan=1, sticky=WENS)
        rc += 1

        self.previous = tk.Button(self.playback_control, text="Previous", command=self.previous_cmd, width=15, height=2)
        self.previous.grid(row=rc, column=0, sticky=WENS)
        self.next = tk.Button(self.playback_control, text="Next", command=self.next_cmd, width=15, height=2)
        self.next.grid(row=rc, column=1, sticky=WENS)
        self.command_buttons += [self.play, self.pause, self.previous, self.next]


        ### Volume control ###
        framerow += 1
        rc = 0
        self.volume_control = tk.LabelFrame(self.left_col, text="Volume Control", padx=5, pady=5)
        self.volume_control.grid(row=framerow, columnspan=2, sticky=WENS)
        self.volume_control.grid_columnconfigure(0, weight=1)
        self.volume_control.grid_columnconfigure(1, weight=1)

        self.setvolume = tk.Scale(self.volume_control, from_=0, to=100, orient=tk.HORIZONTAL, command=self.setvolume_timer_cmd)
        self.setvolume.grid(row=rc, column=0, columnspan=2, sticky=WENS)
        rc += 1

        self.setmute = tk.Button(self.volume_control, text="Mute", command=self.setmute_cmd, height=2)
        self.setmute.grid(row=rc, column=0, sticky=WENS)
        self.setunmute = tk.Button(self.volume_control, text="Unmute", command=self.setunmute_cmd, height=2)
        self.setunmute.grid(row=rc, column=1, sticky=WENS)
        self.command_buttons += [self.setvolume, self.setmute, self.setunmute]


        ### Song Control ###
        framerow += 1
        rc = 0
        self.song_control = tk.LabelFrame(self.left_col, text="Song Control", padx=5, pady=5)
        self.song_control.grid(row=framerow, columnspan=2, sticky=WENS)
        self.song_control.grid_columnconfigure(0, weight=1)
        self.song_control.grid_columnconfigure(1, weight=1)

        self.entry2 = EntryWithPlaceholder(self.song_control, placeholder="(Hr Min) Sec or Queue Number")
        self.entry2.grid(row=rc, columnspan=2, sticky=WENS)
        rc += 1

        self.seektime = tk.Button(self.song_control, text="Skip to time", command=self.seektime_cmd, height=2)
        self.seektime.grid(row=rc, column=0, sticky=WENS)
        self.seekqueue = tk.Button(self.song_control, text="Play queue no.", command=self.seekqueue_cmd, height=2)
        self.seekqueue.grid(row=rc, column=1, sticky=WENS)
        self.command_buttons += [self.seektime, self.seekqueue]


        ### Source Control ###
        framerow += 1
        rc = 0
        self.source_control = tk.LabelFrame(self.left_col, text="Source Control", padx=5, pady=5)
        self.source_control.grid(row=framerow, columnspan=2, sticky=WENS)
        self.source_control.grid_columnconfigure(0, weight=1)
        self.source_control.grid_columnconfigure(1, weight=1)

        self.entry = EntryWithPlaceholder(self.source_control, placeholder="Spotify/TuneIn ID/URL")
        self.entry.grid(row=rc, columnspan=2, sticky=WENS)
        rc += 1

        self.addsongtoqueue = tk.Button(self.source_control, text="Add song", command=self.addsongtoqueue_cmd, height=2)
        self.addsongtoqueue.grid(row=rc, column=0, sticky=WENS)
        self.playuri = tk.Button(self.source_control, text="Play tunein", command=self.playuri_cmd, height=2)
        self.playuri.grid(row=rc, column=1, sticky=WENS)
        rc += 1

        self.addplaylisttoqueue = tk.Button(self.source_control, text="Add playlist", command=self.addplaylisttoqueue_cmd, height=2)
        self.addplaylisttoqueue.grid(row=rc, column=0, sticky=WENS)
        self.playqueue = tk.Button(self.source_control, text="Play queue", command=self.playqueue_cmd, height=2)
        self.playqueue.grid(row=rc, column=1, sticky=WENS)
        rc += 1

        self.clearqueue = tk.Button(self.source_control, text="Clear queue", command=self.clearqueue_cmd, height=2)
        self.clearqueue.grid(row=rc, columnspan=2, sticky=WENS)
        self.command_buttons += [self.addsongtoqueue, self.playuri, self.addplaylisttoqueue, self.playqueue, self.clearqueue]


        ### Close ###
        self.close = tk.Button(self, text="Close", command=self.master.destroy, height=2)
        self.close.grid(row=1, columnspan=4, sticky=WENS)


        ### Target Control ###
        self.updateSonos()


        ### Poison Control ###
        framerow = 1
        rc = 0
        self.poison_control = tk.LabelFrame(self.right_col, text="Poison Control", padx=5, pady=5)
        self.poison_control.grid(row=framerow, column=2, columnspan=2, sticky=WENS)
        self.poison_control.grid_columnconfigure(0, weight=1)
        self.poison_control.grid_columnconfigure(1, weight=1)

        self.poison_indication = tk.Label(self.poison_control, text="Not Poisoning!")
        self.poison_indication.grid(row=rc, columnspan=2, sticky=WENS)
        rc +=1

        self.poison_select_targets = tk.Button(self.poison_control, text="Select Targets", command=self.poison_target_selection_cmd)
        self.poison_select_targets.grid(row=rc, columnspan=2, sticky=WENS)
        rc +=1

        self.start_poison_button = tk.Button(self.poison_control, text="Start Poison", command=self.start_poison_button_cmd, state=tk.NORMAL)
        self.start_poison_button.grid(row=rc, column=0, sticky=WENS)
        self.target_required_buttons += [self.start_poison_button]
        self.stop_poison_button = tk.Button(self.poison_control, text="Stop Poison", command=self.stop_poison_button_cmd, state=tk.DISABLED)
        self.stop_poison_button.grid(row=rc, column=1, sticky=WENS)

        ### Routine Control ###
        framerow += 1
        rc = 0
        self.routine_control = tk.LabelFrame(self.right_col, text="Routine Control", padx=5, pady=5)
        self.routine_control.grid(row=framerow, column=2, columnspan=2, sticky=WENS)
        self.routine_control.grid_columnconfigure(0, weight=1)
        self.routine_control.grid_columnconfigure(1, weight=1)

        self.routine_indication = tk.Label(self.routine_control, text="Ready to Record")
        self.routine_indication.grid(row=rc, columnspan=2, sticky=WENS)
        rc +=1

        self.record_button = tk.Button(self.routine_control, text="Start Recording", command=self.record_routine_cmd)
        self.record_button.grid(row=rc, columnspan=2, sticky=WENS)
        rc +=1

        self.start_routine_button = tk.Button(self.routine_control, text="Start Routine", command=self.start_routine_button_cmd, state=tk.NORMAL)
        self.start_routine_button.grid(row=rc, column=0, sticky=WENS)
        self.target_required_buttons += [self.start_routine_button]
        self.stop_routine_button = tk.Button(self.routine_control, text="Stop Routine", command=self.stop_routine_button_cmd, state=tk.DISABLED)
        self.stop_routine_button.grid(row=rc, column=1, sticky=WENS)


    # Update (poison) device list in background
    def updateDevices(self, single):
        print("~Updating Devices~")
        threadedUpdateDevices(self.local_ip, self.devices)
        if single:
            self.after(60000, lambda: self.updateDevices(False))
    
    # Update Sonos target list
    def updateSonos(self):
        updateTheme = False

        # Clear targets (if set)
        if self.targets:
            self.cleartargets_cmd()

        # 'Disable' GUI and refresh devices (foreground process)
        if not self.target_control is None:
            self.tk_setPalette(background="grey60", foreground="grey65",
               activeBackground="grey60", activeForeground="grey65")
            updateTheme = True
            self.update_idletasks()

            self.sonos_ips = getSonosIPs(self.devices)
            self.sonos_info = getSonosInfo(self.sonos_ips)

            self.target_control.grid_forget()

        # Build target list
        framerow = 0
        rc = 0
        self.target_control = tk.LabelFrame(self.right_col, text="Target Control", padx=5, pady=5)
        self.target_control.grid(row=rc, column=2, columnspan=2, sticky=WENS)
        self.target_control.grid_columnconfigure(0, weight=1)

        self.sonos_info = OrderedDict(sorted(self.sonos_info.items()))      # Sorts dictionary on key (ip)
        for ip, info in self.sonos_info.items():
            if info['ZoneName'] == "Unknown Device":
                continue
            target_var = tk.IntVar()
            target_var.ip = ip
            action = partial(self.updatetargets_cmd, {ip:dict(info)})
            target_button = tk.Checkbutton(self.target_control, text=info['ZoneName'],
                variable=target_var, command=action, height=2, indicatoron=0)
            target_button.grid(row=rc, sticky=WENS)

            self.target_vars.append(target_var)
            self.target_buttons.append(target_button)
            rc += 1


        self.cleartargets = tk.Button(self.target_control, text="Clear", command=self.cleartargets_cmd, relief="ridge")
        self.cleartargets.grid(row=rc, sticky=WENS)

        if updateTheme:
            self.setTheme(self.theme_var.get())

    # Update button state if any targets or override
    def updateButtons(self, buttons, override=False):
        state = tk.NORMAL if len(self.targets) > 0 or override else tk.DISABLED
        for button in buttons:
            if button is self.start_poison_button and not self.poison_process is None:
                continue
            elif button is self.start_routine_button and not self.routine_process is None:
                continue
            button['state'] = state

    # Set button state for list of buttons
    def setButtonsState(self, buttons, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        for button in buttons:
            if button is self.start_poison_button and not self.poison_process is None:
                continue
            button['state'] = state

    # Create menubar (togglable with 'm')
    def createMenu(self):
        self.theme_var = tk.StringVar()
        self.menushown = False

        self.menubar = tk.Menu(self)
        self.refreshmenu = tk.Menu(self.menubar, tearoff=0)
        self.refreshmenu.add_command(label="Sonos", command=self.updateSonos)
        self.refreshmenu.add_command(label="Devices", command=partial(self.updateDevices, True))
        self.menubar.add_cascade(label="Refresh", menu=self.refreshmenu)

        self.themes = tk.Menu(self.menubar, tearoff=0)
        for theme in THEMES.keys():
            action = partial(self.setTheme, theme)
            self.themes.add_radiobutton(label=theme.capitalize(), command=action, variable=self.theme_var, val=theme)
        self.menubar.add_cascade(label="Theme", menu=self.themes)
 
    # Toggle menubar
    def toggleMenu(self, b=""):
        self.menushown = bool(self.menushown ^ 1)
        if self.menushown:
            self.master.config(menu=self.menubar)
        else:
            self.master.config(menu="")


    # Set application color theme
    def setTheme(self, style):
        colors = THEMES[style]
        self.MAIN_COLOR, self.CONT_COLOR, self.LIGHT_MAIN_COLOR, self.DARK_CONT_COLOR, self.CONT2_COLOR = colors["MAIN_COLOR"], colors["CONT_COLOR"], colors["LIGHT_MAIN_COLOR"], colors["DARK_CONT_COLOR"], colors["CONT2_COLOR"]

        self.tk_setPalette(background=self.MAIN_COLOR, foreground=self.CONT_COLOR,
               activeBackground=self.LIGHT_MAIN_COLOR, activeForeground=self.DARK_CONT_COLOR)

        for button in self.target_buttons:
            button["selectcolor"] = self.LIGHT_MAIN_COLOR

        self.close["fg"] = self.CONT2_COLOR
        for entry in [self.entry, self.entry2]:
            entry.placeholder_color = self.DARK_CONT_COLOR
            entry["fg"] = self.DARK_CONT_COLOR
            entry.default_fg_color = self.CONT_COLOR

        self.theme_var.set(style)


    ###
    #   Player controls
    #

    def play_cmd(self):
        self.command("play")
        print("Playing...")

    def pause_cmd(self):
        self.command("pause")
        print("Paused.")

    def previous_cmd(self):
        self.command("previous")
        print("Playing previous track.")

    def next_cmd(self):
        self.command("next")
        print("Skipped to next track.")


    def setvolume_timer_cmd(self, vol):
        if not self.volume_timer is None:
            self.volume_timer.cancel()
        self.volume_timer = Timer(.5, self.setvolume_cmd)
        self.volume_timer.start()

    def setvolume_cmd(self):
        vol = self.setvolume.get()
        self.command("setvolume", {"volume":str(vol)})
        print("Volume set to " + str(vol))
        self.volume_timer = None

    def setmute_cmd(self):
        self.command("setmute", {"mute":str(1)})
        print("Speaker has been muted.")

    def setunmute_cmd(self):
        self.command("setmute", {"mute": str(0)})
        print("Speaker has been unmuted.")


    ###
    #   Queue manipulation
    #

    def addsongtoqueue_cmd(self):
        uristring = self.entry.get()
        try:                        # Takes the track uri from a spotify url
            uri = re.search('/track/(.*)?si=', uristring).group(1)[:-1]
        except:
            uri = uristring
        finally:
            if (len(str(uri))==22):
                self.command("addsongtoqueue", {"uri":str(uri)})
                print("Added song " + str(uri) + " to queue.")
            else:
                print("Invalid uri length: " + uri)

    def addplaylisttoqueue_cmd(self):
        uristring = self.entry.get()
        try:                        # Takes the playlist uri from a spotify url
            uri = re.search('/playlist/(.*)?si=', uristring).group(1)[:-1]
        except:
            uri = uristring
        finally:
            if (len(str(uri))==22):
                self.command("addplaylisttoqueue", {"uri":str(uri), "title":"&#128123;"})
                print("Added playlist " + str(uri) + " to queue.")
            else:
                print("Invalid uri length: " + uri)

    def playuri_cmd(self):
        uristring = self.entry.get()
        try:                        # Takes the radio uri from a tunein url
            uri = re.search('-s(.*)/', uristring).group(1)
            uri = "s" + uri
        except:
            uri = uristring
        finally:
            self.command("playuri", {"uri":str(uri)})
            print("Playing tunein " + str(uri))

    def playqueue_cmd(self):
        self.command("playqueue")
        print("Playing queue.")

    def seektime_cmd(self):
        params = tuple([int(p) for p in self.entry2.get().split(" ")])
        if len(params) == 3:
            time = "{0:01d}:{1:02d}:{2:02d}".format(*params)
        elif len(params) == 2:
            time = "0:{0:02d}:{1:02d}".format(*params)
        elif len(params) == 1:
            time = "0:00:{:02d}".format(params[0])

        self.command("seektime", {"time": str(time)})
        print("Skipping to " + str(time))

    def seekqueue_cmd(self):
        no = self.entry2.get()
        if (no.isdecimal()):
            self.command("seekqueue", {"index": str(no)})
            print("Playing queue no. " + str(no))
        else:
            print("Invalid queue no. entry: " + str(no))

    def clearqueue_cmd(self):
        self.command("clearqueue")
        print("Queue cleared.")


    # Sends the actual command to the specified targets
    def command(self, command, params={}):
        if self.recording:
            self.routine += [(command, params)]
        else:
            for ip, info in self.targets.items():
                params["uuid"] = info["LocalUID"]
                sendCommand(command, params, ip)
                print("Sent " + command + " to " + ip)


    ###
    #   Poison commands
    #

    def poison_target_selection_cmd(self):
        rc = 0
        win = self.select_popup = tk.Toplevel()
        win.wm_title("Poison Target Selection")
        win.resizable(False, False)
        win.grid_columnconfigure(0, weight=1)
        win.grid_columnconfigure(1, weight=1)
        win.grid_columnconfigure(2, weight=1)

        px, py = 2, (4, 6)
        rel = "groove"
        ip_label = tk.Label(win, text="IP", borderwidth=2, relief=rel, fg=self.DARK_CONT_COLOR)
        ip_label.grid(row=rc, column=0, sticky=WENS, padx=px, pady=py)
        mac_label = tk.Label(win, text="MAC", borderwidth=2, relief=rel, fg=self.DARK_CONT_COLOR)
        mac_label.grid(row=rc, column=1, sticky=WENS, padx=px, pady=py)
        vendor_label = tk.Label(win, text="VENDOR", borderwidth=2, relief=rel, fg=self.DARK_CONT_COLOR)
        vendor_label.grid(row=rc, column=2, sticky=WENS, padx=px, pady=py)
        rc += 1

        self.device_vars = []
        px, py = 4, 2
        for device in self.devices:
            device_var = tk.IntVar()
            device_var.device = device
            if device in self.poisontargets:
                device_var.set(1)

            ip_field = tk.Checkbutton(win, text=device["ip"], variable=device_var, indicatoron=0, selectcolor=self.LIGHT_MAIN_COLOR)
            ip_field.grid(row=rc, column=0, sticky=WENS, padx=px, pady=py)
            mac_field = tk.Checkbutton(win, text=device["mac"], variable=device_var, indicatoron=0, selectcolor=self.LIGHT_MAIN_COLOR)
            mac_field.grid(row=rc, column=1, sticky=WENS, padx=px//2, pady=py)
            vendor_field = tk.Checkbutton(win, text=device["vendor"], variable=device_var, indicatoron=0, selectcolor=self.LIGHT_MAIN_COLOR)
            vendor_field.grid(row=rc, column=2, sticky=WENS, padx=px, pady=py)

            self.device_vars += [device_var]
            rc += 1

        px, py = 4, (6, 4)
        toggleallbutton = tk.Button(win, text="Toggle All", command=self.toggle_devices_cmd, relief="ridge", fg=self.DARK_CONT_COLOR)
        toggleallbutton.grid(row=rc, column=0, sticky=WENS, padx=px, pady=py)
        selectbutton = tk.Button(win, text="Select Targets", command=self.select_devices_cmd, relief="raised")
        selectbutton.grid(row=rc, column=1, sticky=WENS, padx=px, pady=py)
        cancelbutton = tk.Button(win, text="Cancel", fg=self.CONT2_COLOR, command=win.destroy, relief="raised")
        cancelbutton.grid(row=rc, column=2, sticky=WENS, padx=px, pady=py)
        
    def toggle_devices_cmd(self):
        first = True
        for device_var in self.device_vars:
            if first:
                state = device_var.get() ^ 1
                first = False
            device_var.set(state)

    def select_devices_cmd(self):
        self.poisontargets = []
        for device_var in self.device_vars:
            state = device_var.get()
            if state == 1:
                self.poisontargets += [device_var.device]
        self.select_popup.destroy()


    def start_poison_button_cmd(self):
        try:
            self.startpoison_cmd()
        except:
            self.poison_indication.configure(text="Unable to poison.")
        else:
            self.start_poison_button['state'] = tk.DISABLED
            self.stop_poison_button['state'] = tk.NORMAL
            for i, button in enumerate(self.target_buttons):
                if self.target_vars[i].ip in self.targets.keys():
                    button["fg"] = self.CONT2_COLOR
            self.poison_indication.configure(text="Poisoning {} Device{}!".format(len(self.poisontargets), "s" if len(self.poisontargets) != 1 else ""))

    def startpoison_cmd(self):
        if self.poison_process == None:
            self.poison_process = startPoison(
                        self.iface,
                        list(self.targets.keys()), # Which SONOS will be hidden
                        self.poisontargets,
                        self.local_ip,
                        self.local_mac
                        )
            print("Started poisoning.")
        else:
            print("Already poisoning.")


    def stop_poison_button_cmd(self):
        try:
            self.stoppoison_cmd()
        except:
            self.poison_indication.configure(text="Unable to stop poison.")
        else:
            if len(self.targets) > 0 and not self.recording:
                self.start_poison_button['state'] = tk.NORMAL
            self.stop_poison_button['state'] = tk.DISABLED
            for button in self.target_buttons:
                button["fg"] = self.CONT_COLOR
            self.poison_indication.configure(text="Not Poisoning!")

    def stoppoison_cmd(self):
        if self.poison_process == None:
            print("Currently not poisoning.")
        else:
            stopPoison(self.poison_process)
            self.poison_process = None
            print("Poisoning stopped.")


    ###
    #   Routine commands
    #

    def record_routine_cmd(self):
        self.recording = bool(self.recording ^ 1)
        if self.recording:
            self.routine = []
            self.setButtonsState(self.target_buttons + [self.cleartargets, self.poison_select_targets] + self.target_required_buttons, False)
            self.updateButtons(self.command_buttons, override=True)
            self.routine_indication.configure(text="Recording!")
            self.record_button.configure(text="Stop Recording!")
            print("Started recording.")

        else:
            self.routine_indication.configure(text="Routine Ready!")
            self.record_button.configure(text="Start Recording!")
            self.setButtonsState(self.target_buttons + [self.cleartargets, self.poison_select_targets], True)
            self.updateButtons(self.command_buttons + self.target_required_buttons)
            print("Stopped recording.")


    def start_routine_button_cmd(self):
        try:
            self.startroutine_cmd()
        except:
            self.routine_indication.configure(text="Running Routine!")
        else:
            self.start_routine_button['state'] = tk.DISABLED
            self.stop_routine_button['state'] = tk.NORMAL
            self.routine_indication.configure(text="Running on {} Target{}!".format(len(self.targets), "s" if len(self.targets) != 1 else ""))

    def startroutine_cmd(self):
        if self.routine_process == None:
            self.routine_process = startRoutine(self.targets, self.routine)
            print("Started routine.")
        else:
            print("Routine already running.")


    def stop_routine_button_cmd(self):
        try:
            self.stoproutine_cmd()
        except:
            self.routine_indication.configure(text="Failed to stop Routine!")
        else:
            if len(self.targets) > 0 and not self.recording:
                self.start_routine_button['state'] = tk.NORMAL
            self.stop_routine_button['state'] = tk.DISABLED
            self.routine_indication.configure(text="Routine Ready!")

    def stoproutine_cmd(self):
        if self.routine_process == None:
            print("Routine currently not running.")
        else:
            stopPoison(self.routine_process)
            self.routine_process = None
            print("Routine stopped.")


    ###
    #   Targeting commands
    #

    def cleartargets_cmd(self):
        self.targets = {}
        for target in self.target_buttons:
            target.deselect()
        self.updateButtons(self.command_buttons + self.target_required_buttons)

    def updatetargets_cmd(self, sonos):
        ip, info = list(sonos.items())[0]
        if ip in self.targets.keys():
            del self.targets[ip]
        else:
            self.targets[ip] = info
        self.updateButtons(self.command_buttons + self.target_required_buttons)


# create window
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Vrijdag Phish")
    root.resizable(False, False)
    app = Application(master=root)
    app.mainloop()
    exit()