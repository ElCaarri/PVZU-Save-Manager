# **PVZ Universe \- Save Manager 🌻🧟‍♂️**

Welcome to the **PVZ Universe Save Manager**\! This is an open-source tool developed in Python (PyQt6) designed to manage, edit, and backup your save files (savefile.sav) from the popular fangame *Plants vs. Zombies: Universe*.

## **✨ Main Features**

This tool offers two editing modes to suit both casual and advanced users:

### **🛠️ Basic Mode (Graphical Interface)**

Modify your save values safely through a clean and easy-to-use interface:

* **Resources:** Edit your amount of Coins, Gems (Diamonds), and Tacos.  
* **World Keys:** Add or remove keys for any world (Ancient Egypt, Pirate Seas, Far Future, Dragon Palace, etc.).  
* **Events \- Travel Log:** Missed an event or want to play it again? Reset or modify your progress in special events such as:  
  * Valenbrainz 2026  
  * Feastivus 2025  
  * Tangerine Batter  
  * Birthdayz Party  
* **Upgrades / Boosters:** Quickly enable or disable game upgrades such as:  
  * Sun Shovel (Level 1 & 2\)  
  * 7 Seed Slots  
  * Extra Starting Sun (Level 1\)  
* **Unlock Plants:** A dedicated panel with checkboxes to individually unlock or lock any plant in the game, with quick buttons to "Unlock All" or "Lock All".

### **💻 Advanced Mode (JSON Editor)**

For users who want full control:

* View the original file (which is a single line of code) as a perfectly structured and indented JSON.  
* Edit any hidden game variable directly.  
* Two-way synchronization: Changes in the text editor are automatically reflected in the Basic Mode and vice versa.

### **⚙️ Extra Features**

* **Direct Integration:** Run the game directly from the manager. The program will detect if the game is already running to avoid read/write conflicts.  
* **Import / Export:** Create backups of your saves in the original compressed format (.sav) or export them as readable files (.json).  
* **Multi-language Support:** Interface translated into English, Spanish, and Chinese (configurable from the settings menu).

## **🚀 Installation and Usage**

### **Option 1: Use the Executable (.exe) \- *Recommended***

If you just want to use the program, you don't need to install Python.

1. Go to the **Releases** tab in this repository.  
2. Download the .zip file of the latest release.  
3. Extract the files into a folder (make sure main.exe and lang.json are always together in the same folder).  
4. Run main.exe.

### **Option 2: Run from Source Code**

If you are a developer and want to modify the code:

1. Make sure you have **Python 3.8+** installed.

2. Clone this repository:
```bash
git clone https://github.com/ElCaarri/PVZU-Save-Manager.git
```

3. Install the required dependencies (PyQt6):
```bash
pip install PyQt6
```

4. Run the main script:
```bash
python main.py
```

## **🛠️ How to compile your own .exe**

If you have made modifications to the code and want to compile your own executable for Windows, we use PyInstaller:

1. Install PyInstaller:  
   
```bash
pip install pyinstaller
```
	
2. Run the build command:  

```bash
python \-m PyInstaller \--noconsole \--onefile main.py
```
 
3. You will find your executable in the dist folder. **Don't forget to copy the lang.json file next to it so the languages work\!**

## **🌐 Adding new languages**

The program uses an external dictionary system for languages. To add a new language, simply open the lang.json file, add your language code (e.g., "fr" for French), and translate the corresponding text strings.

*(Note: For the new language to appear in the 'Settings' dropdown menu, you must add it in the SettingsDialog class inside main.py)*.

## **⚠️ Disclaimer**

This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with PopCap Games, Electronic Arts (EA), or the creators of the fangame *Plants vs. Zombies: Universe*.

Modifying save files is done at your own risk. It is highly recommended to **backup (Export)** your save file before making massive modifications.
