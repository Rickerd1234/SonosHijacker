# SonosHijacker
Project 2IC80 - Group 52 - Vrijdag Phish


### Disclaimer
By dowloading, cloning or using this tool, you agree to not use it to cause any harm to any speakers or networks that are not owned by yourself. Do not attempt to violate the law with anything contained here. If you planned to use the content for illegal purpose, then please leave this site immediately! We will not be responsible for any illegal actions.


## Contents
<ul>
  <li><a href="#about-the-tool">About the Tool</a></li>
  <li><a href="#prerequisites">Prerequisites</a></li>
  <li><a href="#usage">Usage</a></li>
  <li><a href="#control">Control</a></li>
  <li><a href="#arp-poisoning">ARP Poisoning</a></li>
  <li><a href="#routines">Routines</a></li>
</ul>
  
## About the Tool
This tool was developed for the course 2IC80 Lab on Offensive Computer Security, the objective was engineer an attack (on IoT devices). Our group decided on attacking a Sonos speaker system from within the Local Area Network (LAN), where the main goals were controlling the speakers and blocking the victim from controlling the speakers. To achieve this, we started by analyzing the Sonos applications and reverse engineering the software and network activity for Sonos speakers. Using <a href="https://www.wireshark.org/">Wireshark</a> we were able to understand the structure of Sonos commands. Which we could simply record and repeat to control the Sonos speakers. Besides, it became obvious that the application sends the commands directly to the selected speaker(s). So target control would be as easy as listing Sonos speakers and slightly changing the packets. After the basic control mechanisms were in place we looked into disrupting standard control. For this we looked into <a href="https://en.wikipedia.org/wiki/ARP_spoofing">ARP poisoning</a>, which should allow us to mess with clients that try to control the Sonos. After a trial and error process we managed to get this working, which allows the attacker to take full control of the speakers in a network. The only exception to this is physicial interaction with the speakers, since the speakers have volume and play/pause buttons. For this reason, we developed another kind of attack in the form of routines. Routines allow the attacker to send multiple commands in (quick) succession, which means that the buttons will be rather useless. In summary, our tool allows hijacking in multiple ways, to make sure the attackers remains in control.

## Prerequisites
In order to run the source code for the tool, you can simply run the gui.py using Python 3 (tested using 3.9.1). Besides the default Python libraries, the following libraries are required:
<ul>
  <li><a href="https://scapy.readthedocs.io/en/latest/introduction.html">Scapy</a></li>
  <li><a href="https://pypi.org/project/python-nmap/">Python-Nmap</a></li>
  <li><a href="https://github.com/martinblech/xmltodict">XMLtoDict</a></li>
  <li><a href="https://pypi.org/project/requests/">Requests</a></li>
</ul>
Furthermore, you will also need to have <a href="https://nmap.org/">Nmap</a> installed on the system and it must be included in the System PATH variables.

## Usage
![gui](https://user-images.githubusercontent.com/25881390/123850485-60b84c00-d91a-11eb-86d3-16cecc645d98.png)<br>
### GUI
Running gui.py (with all prerequisites installed) will first perform a network scan, after which it will display the GUI. This GUI consists of 4 main parts, Sonos control, target selection, ARP poisoning and routine management. The Sonos control consists of the left column, where you can control targeted Sonos speakers. These targets are selected in the target selection part, which is in the top of the right column, the selected speakers are used as targets for the control section as well as the ARP poisoning and routines. The ARP poisoning is managed in the middle of the right column, here you can pick target devices, as well as start and stop the poison attack. Lastly, the routines are managed in the bottom right part of the GUI. When recording, all the commands from the control section will be recorded and later used in the routine attack.

### CLI
In case you want to run the tool as a Command-Line-Interface (CLI), you can run SonosHijacker.py. The CLI is very similar to the GUI, however routines are not implemented for the CLI. To get started with the CLI, simply invoke ?h as your first command, this will show a list of possible commands.
  
## Control
The tool allows extensive control of Sonos speakers, most actions you would find in the official Sonos application are also featured in our control section. In the screenshot above you can see the commands, most of which are very easy to use. However, the Song Control and Source Control will be elaborated on, since these are a bit more complex.<br>

### Song Control
For these 2 commands, you need to provide a parameter. Skip to time will set the current time in the song to a given timestamp. This command requires a timestamp as parameter, where you can separate hours minutes and seconds using a whitespace, however using "1 40" is equivalent to using "100", both will set the timestamp to 1:40. Play queue no. will select the provided song from the queue, for this you simply provide a single integer value. The queue will continue from the given index, note: indexing starts from 1.

### Source Control
The parameter field allows either the full content URI or just the id for both the Spotify and TuneIn command. For Spotify, you can provide the "share" URL for:<br> a playlist (https://open.spotify.com/playlist/37i9dQZF1DZ06evO05tE88?si=25f760009e0f46c5 _id: 37i9dQZF1DZ06evO05tE88_)<br> or song (https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT?si=09022f85b4624278 _id: 4cOdK2wGLETKBW3PvgPWqT_)<br>whilst for TuneIn you can provide the URL of the station (https://tunein.com/radio/Efteling-Kids-Radio-s95494/ _id: s95494_).<br>
After finding the right URI or id, press the corresponding button. Note that the Sonos will not start playing automatically, to guarante that the queue is being played, first manage the queue, next use the playqueue command to set the Sonos source to the queue, after which you can press play. For the TuneIn radio stations to be played, you first need to use the play tunein command, after which you press play to start playing.
  
## ARP Poisoning
The ARP poisoning attack allows the attacker to deny other devices access to the Sonos speaker. For this you need to select targets to deny access from the "Select targets" popup in the Poison Control section. This popup is shown as a screenshot below. As a rule of thumb, to deny all network access: Select all devices except Sonos and routing/switching devices. Besides these targets, you will also need to provide the standard Sonos targets. When you start poisoning, the tool will send an ARP poisoning packet to every target device for every target Sonos within roughly 5 seconds. This way all devices should have their ARP tables poisoned quickly and they will remain poisoned until you stop the attack.<br>
![popup](https://user-images.githubusercontent.com/25881390/123853227-7e3ae500-d91d-11eb-9c1f-9fc884aa11d9.png)

  
## Routines
The last part of the tool is the routine control, which allows you to send multiple commands repeatedly in a 5 second period. This feature is a counter-attack against the physical buttons. The way to use this is by recording a routine, then selecting Sonos targets and starting the routine. All control commands that were recorded, will be sent in the same order, separated by roughly 5/L seconds, where L is the amount of commands in the recorded routine. So to force the speaker to play on max volume, you can record a routine containing Play, SetVolume 100 and Unmute. To make this even better, you can repeat these commands multiple times whilst recording, to increase the frequency of each command being sent.
