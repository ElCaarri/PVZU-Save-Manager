import sys
import os
import shutil
import json
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                             QTextEdit, QMessageBox, QLineEdit, QTabWidget, 
                             QSpinBox, QFormLayout, QGroupBox, QDialog, 
                             QComboBox, QToolButton, QScrollArea, QCheckBox, 
                             QGridLayout)
from PyQt6.QtCore import Qt

# --- LOAD EXTERNAL TRANSLATIONS ---
def get_base_dir():
    """Obtiene el directorio base, compatible con el .exe de PyInstaller"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def load_translations():
    base_dir = get_base_dir()
    lang_path = os.path.join(base_dir, "lang.json")
    
    try:
        with open(lang_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ADVERTENCIA: No se pudo cargar lang.json ({e}).")
        return {
            "es": {
                "title": "Error: Falta lang.json", 
                "settings_title": "Error", 
                "set_lang": "Idioma", 
                "btn_save": "Ok", 
                "btn_cancel": "Cancelar"
            }
        }

TRANSLATIONS = load_translations()

class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_format="sav", current_lang="es"):
        super().__init__(parent)
        tr = TRANSLATIONS.get(current_lang, TRANSLATIONS["es"])
        self.setWindowTitle(tr.get("settings_title", "Configuración"))
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(tr.get("set_lang", "Idioma:")))
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("Español", "es")
        self.combo_lang.addItem("English", "en")
        self.combo_lang.addItem("中文", "zh")
        
        idx = self.combo_lang.findData(current_lang)
        if idx >= 0:
            self.combo_lang.setCurrentIndex(idx)
            
        layout.addWidget(self.combo_lang)

        layout.addWidget(QLabel(tr.get("set_export_format", "Formato:")))
        self.combo_format = QComboBox()
        self.combo_format.addItem(".sav (Original)", "sav")
        self.combo_format.addItem(".json (Estructurado)", "json")
        
        index = self.combo_format.findData(current_format)
        if index >= 0:
            self.combo_format.setCurrentIndex(index)
            
        layout.addWidget(self.combo_format)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton(tr.get("btn_save", "Guardar"))
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton(tr.get("btn_cancel", "Cancelar"))
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def get_selected_format(self):
        return self.combo_format.currentData()

    def get_selected_lang(self):
        return self.combo_lang.currentData()

class PVZSaveManager(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.current_data = {} 
        self.is_updating_ui = False 
        
        local_appdata = os.environ.get('LOCALAPPDATA')
        self.save_dir = os.path.join(local_appdata, 'PVZUniverse2')
        self.save_file_path = os.path.join(self.save_dir, 'savefile.sav')
        
        self.config_file = "manager_config.json"
        self.config_data = self.load_config()
        self.game_exe_path = self.config_data.get("exe_path", "")
        self.export_format = self.config_data.get("export_format", "sav")
        self.current_lang = self.config_data.get("language", "es") 

        # Variables for dynamic plant handling
        self.plant_checkboxes = {}
        self.plant_grid_row = 0
        self.plant_grid_col = 0

        self.init_ui()
        self.load_save_data_from_file()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        self.resize(900, 650) # Increased size so plants fit comfortably

        exe_layout = QHBoxLayout()
        self.exe_label = QLabel("Ruta del Juego:")
        self.exe_input = QLineEdit(self.game_exe_path)
        self.exe_input.setReadOnly(True)
        
        self.btn_search_exe = QPushButton("Buscar .exe")
        self.btn_search_exe.clicked.connect(self.select_exe)
        
        self.btn_settings = QToolButton()
        self.btn_settings.setText("⚙️ Configuración")
        self.btn_settings.setToolTip("Opciones de exportación")
        self.btn_settings.clicked.connect(self.open_settings)
        
        exe_layout.addWidget(self.exe_label)
        exe_layout.addWidget(self.exe_input)
        exe_layout.addWidget(self.btn_search_exe)
        exe_layout.addWidget(self.btn_settings)
        layout.addLayout(exe_layout)

        btn_layout = QHBoxLayout()
        
        self.btn_play = QPushButton("▶ JUGAR")
        self.btn_play.setObjectName("btnPlay")
        self.btn_play.clicked.connect(self.play_game)
        
        self.btn_import = QPushButton("📥 Importar")
        self.btn_import.clicked.connect(self.import_save)
        
        self.btn_export = QPushButton("📤 Exportar")
        self.btn_export.clicked.connect(self.export_save)

        btn_layout.addWidget(self.btn_play)
        btn_layout.addWidget(self.btn_import)
        btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        self.tab_basic = QWidget()
        self.init_basic_tab()
        self.tabs.addTab(self.tab_basic, "🛠️ Modo Básico")
        
        self.tab_advanced = QWidget()
        self.init_advanced_tab()
        self.tabs.addTab(self.tab_advanced, "💻 Modo Avanzado (JSON)")
        
        layout.addWidget(self.tabs)

        self.btn_save_changes = QPushButton("💾 Guardar Cambios en el Juego")
        self.btn_save_changes.clicked.connect(self.save_to_game_file)
        layout.addWidget(self.btn_save_changes)

        self.apply_css()
        self.retranslate_ui()

    def init_basic_tab(self):
        main_basic_layout = QHBoxLayout(self.tab_basic)
        
        # --- NEW: Scroll container for the left column ---
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }") # No border for a clean design
        
        left_widget = QWidget()
        left_column = QVBoxLayout(left_widget)
        left_column.setContentsMargins(0, 0, 15, 0) # Margin to separate the scroll bar from the boxes
        
        # Resources
        self.group_resources = QGroupBox("Recursos Principales")
        form_resources = QFormLayout(self.group_resources)
        
        self.spin_coins = self.create_spinbox(999999999)
        self.spin_diamonds = self.create_spinbox(999999999)
        self.spin_tacos = self.create_spinbox(9999999) 
        
        self.lbl_coins = QLabel("Monedas:")
        self.lbl_diamonds = QLabel("Gemas (Diamonds):")
        self.lbl_tacos = QLabel("Tacos:")

        form_resources.addRow(self.lbl_coins, self.spin_coins)
        form_resources.addRow(self.lbl_diamonds, self.spin_diamonds)
        form_resources.addRow(self.lbl_tacos, self.spin_tacos)
        
        # World Keys
        self.group_keys = QGroupBox("Llaves de Mundo (World Keys)")
        form_keys = QFormLayout(self.group_keys)
        
        self.world_keys_spins = {}
        self.lbl_keys = {}
        
        worlds = ["egypt", "pirate", "cowboy", "kungfu", "future", "mausoleum", "palace"]
        
        for world_key in worlds:
            spin = self.create_spinbox(999)
            self.world_keys_spins[world_key] = spin
            lbl = QLabel(f"Llaves de {world_key}:")
            self.lbl_keys[world_key] = lbl
            form_keys.addRow(lbl, spin)
            
        # Events (Travel Log)
        self.group_events = QGroupBox("Eventos - Tronco del Viaje")
        form_events = QFormLayout(self.group_events)
        
        self.spin_valentines = self.create_spinbox(5)
        self.spin_feastivus = self.create_spinbox(6)
        self.spin_tangerine = self.create_spinbox(5)
        self.spin_birthday = self.create_spinbox(5)
        
        self.lbl_val = QLabel("San Valentín 2026 (Progreso 0-5):")
        self.lbl_fea = QLabel("Navidad 2025 (Progreso 0-6):")
        self.lbl_tan = QLabel("Tangerine Batter (Progreso 0-5):")
        self.lbl_bday = QLabel("Fiesta de Cumpleaños (Progreso 0-5):")

        form_events.addRow(self.lbl_val, self.spin_valentines)
        form_events.addRow(self.lbl_fea, self.spin_feastivus)
        form_events.addRow(self.lbl_tan, self.spin_tangerine)
        form_events.addRow(self.lbl_bday, self.spin_birthday)
        
        # --- NEW: Upgrades group ---
        self.group_upgrades = QGroupBox("Mejoras / Potenciadores")
        form_upgrades = QVBoxLayout(self.group_upgrades)
        
        self.chk_upg_sunshovel_1 = QCheckBox("Pala de Sol (Nivel 1)")
        self.chk_upg_7_slots = QCheckBox("7 Espacios para Plantas")
        self.chk_upg_start_sun = QCheckBox("Sol Inicial Extra (Nivel 1)")
        self.chk_upg_sunshovel_2 = QCheckBox("Pala de Sol (Nivel 2)")
        
        form_upgrades.addWidget(self.chk_upg_sunshovel_1)
        form_upgrades.addWidget(self.chk_upg_7_slots)
        form_upgrades.addWidget(self.chk_upg_start_sun)
        form_upgrades.addWidget(self.chk_upg_sunshovel_2)

        left_column.addWidget(self.group_resources)
        left_column.addWidget(self.group_keys)
        left_column.addWidget(self.group_events)
        left_column.addWidget(self.group_upgrades)
        left_column.addStretch() # Prevents boxes from stretching vertically if the window is large
        
        left_scroll.setWidget(left_widget) # Assign the column to the scroll area
        
        # Right Column (Plants)
        right_column = QVBoxLayout()
        
        self.group_plants = QGroupBox("Desbloqueo de Plantas")
        plants_layout = QVBoxLayout(self.group_plants)
        
        # Buttons to check all or uncheck all
        plants_btn_layout = QHBoxLayout()
        self.btn_unlock_all = QPushButton("Desbloquear Todas")
        self.btn_unlock_all.clicked.connect(self.unlock_all_plants)
        self.btn_lock_all = QPushButton("Bloquear Todas")
        self.btn_lock_all.clicked.connect(self.lock_all_plants)
        plants_btn_layout.addWidget(self.btn_unlock_all)
        plants_btn_layout.addWidget(self.btn_lock_all)
        plants_layout.addLayout(plants_btn_layout)
        
        # Scroll area for checkboxes
        self.plants_scroll = QScrollArea()
        self.plants_scroll.setWidgetResizable(True)
        self.plants_scroll_widget = QWidget()
        self.plants_grid_layout = QGridLayout(self.plants_scroll_widget)
        self.plants_scroll.setWidget(self.plants_scroll_widget)
        
        plants_layout.addWidget(self.plants_scroll)
        right_column.addWidget(self.group_plants)

        # Add both columns to the main layout of the basic tab
        main_basic_layout.addWidget(left_scroll, stretch=1) # Add the scroll widget
        main_basic_layout.addLayout(right_column, stretch=2) # Give more space to plants

    def init_advanced_tab(self):
        layout = QVBoxLayout(self.tab_advanced)
        self.json_editor = QTextEdit()
        layout.addWidget(self.json_editor)

    def create_spinbox(self, max_val):
        spin = QSpinBox()
        spin.setRange(0, max_val)
        spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        return spin

    def apply_css(self):
        stylesheet = """
        QWidget { background-color: #2c3e50; color: #ecf0f1; font-family: 'Segoe UI', Arial; font-size: 13px; }
        QLineEdit, QTextEdit, QSpinBox, QComboBox { 
            background-color: #34495e; border: 1px solid #7f8c8d; border-radius: 4px; padding: 5px; color: #2ecc71; 
        }
        QSpinBox::up-button, QSpinBox::down-button { width: 20px; background-color: #7f8c8d; }
        QPushButton, QToolButton { 
            background-color: #3498db; color: white; border: none; padding: 8px 15px; border-radius: 4px; font-weight: bold; 
        }
        QPushButton:hover, QToolButton:hover { background-color: #2980b9; }
        QPushButton#btnPlay { background-color: #27ae60; font-size: 15px; }
        QPushButton#btnPlay:hover { background-color: #2ecc71; }
        QTabWidget::pane { border: 1px solid #7f8c8d; border-radius: 4px; top: -1px; }
        QTabBar::tab { background: #34495e; border: 1px solid #7f8c8d; padding: 8px 15px; border-top-left-radius: 4px; border-top-right-radius: 4px; }
        QTabBar::tab:selected { background: #2c3e50; border-bottom-color: #2c3e50; font-weight: bold; color: #3498db; }
        QGroupBox { border: 1px solid #7f8c8d; border-radius: 5px; margin-top: 15px; font-weight: bold; padding-top: 15px; }
        QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 5px; }
        QScrollArea { border: 1px solid #7f8c8d; border-radius: 4px; }
        QCheckBox { padding: 5px; }
        QCheckBox::indicator { width: 15px; height: 15px; background-color: #34495e; border: 1px solid #7f8c8d; border-radius: 3px; }
        QCheckBox::indicator:checked { background-color: #2ecc71; }
        """
        self.setStyleSheet(stylesheet)

    def retranslate_ui(self):
        tr = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["es"])

        self.setWindowTitle(tr.get("title", "PVZ Universe - Administrador"))
        self.exe_label.setText(tr.get("exe_label", "Ruta del Juego:"))
        self.btn_search_exe.setText(tr.get("btn_search", "Buscar .exe"))
        self.btn_settings.setText(tr.get("btn_settings", "⚙️ Configuración"))
        self.btn_play.setText(tr.get("btn_play", "▶ JUGAR"))
        self.btn_import.setText(tr.get("btn_import", "📥 Importar"))
        self.btn_export.setText(tr.get("btn_export", "📤 Exportar"))
        self.tabs.setTabText(0, tr.get("tab_basic", "🛠️ Modo Básico"))
        self.tabs.setTabText(1, tr.get("tab_adv", "💻 Modo Avanzado (JSON)"))
        self.btn_save_changes.setText(tr.get("btn_save_game", "💾 Guardar Cambios en el Juego"))

        self.group_resources.setTitle(tr.get("grp_res", "Recursos Principales"))
        self.lbl_coins.setText(tr.get("lbl_coins", "Monedas:"))
        self.lbl_diamonds.setText(tr.get("lbl_gems", "Gemas:"))
        self.lbl_tacos.setText(tr.get("lbl_tacos", "Tacos:"))

        self.group_keys.setTitle(tr.get("grp_keys", "Llaves de Mundo"))
        for world_key in self.lbl_keys:
            dict_key = f"key_{world_key}"
            self.lbl_keys[world_key].setText(tr.get(dict_key, dict_key))

        self.group_events.setTitle(tr.get("grp_evt", "Eventos - Tronco del Viaje"))
        self.lbl_val.setText(tr.get("lbl_val", "San Valentín:"))
        self.lbl_fea.setText(tr.get("lbl_fea", "Navidad:"))
        self.lbl_tan.setText(tr.get("lbl_tan", "Tangerine Batter:"))
        self.lbl_bday.setText(tr.get("lbl_bday", "Fiesta de Cumpleaños:"))

        # Translations for upgrades
        self.group_upgrades.setTitle(tr.get("grp_upgrades", "Mejoras / Potenciadores"))
        self.chk_upg_sunshovel_1.setText(tr.get("upg_sunshovel_1", "Pala de Sol (Nivel 1)"))
        self.chk_upg_7_slots.setText(tr.get("upg_7_slots", "7 Espacios para Plantas"))
        self.chk_upg_start_sun.setText(tr.get("upg_start_sun", "Sol Inicial Extra (Nivel 1)"))
        self.chk_upg_sunshovel_2.setText(tr.get("upg_sunshovel_2", "Pala de Sol (Nivel 2)"))

        # Translations for plants
        self.group_plants.setTitle(tr.get("grp_plants", "Desbloqueo de Plantas"))
        self.btn_unlock_all.setText(tr.get("btn_unlock_all", "Desbloquear Todas"))
        self.btn_lock_all.setText(tr.get("btn_lock_all", "Bloquear Todas"))

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_config(self):
        self.config_data["exe_path"] = self.game_exe_path
        self.config_data["export_format"] = self.export_format
        self.config_data["language"] = self.current_lang
        with open(self.config_file, 'w') as f:
            json.dump(self.config_data, f)

    def open_settings(self):
        dialog = SettingsDialog(self, self.export_format, self.current_lang)
        if dialog.exec():
            self.export_format = dialog.get_selected_format()
            new_lang = dialog.get_selected_lang()
            
            if new_lang != self.current_lang:
                self.current_lang = new_lang
                self.retranslate_ui()

            self.save_config()
            tr = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["es"])
            QMessageBox.information(self, tr.get("settings_title", "Configuración"), tr.get("msg_settings_saved", "Guardado."))

    def select_exe(self):
        tr = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["es"])
        file_path, _ = QFileDialog.getOpenFileName(self, tr.get("fd_exe", "Seleccionar .exe"), "", "Ejecutables (*.exe)")
        if file_path:
            self.game_exe_path = file_path
            self.exe_input.setText(file_path)
            self.save_config()

    def play_game(self):
        tr = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["es"])
        if not self.game_exe_path or not os.path.exists(self.game_exe_path):
            QMessageBox.warning(self, tr.get("msg_error", "Error"), tr.get("msg_no_exe", "Falta .exe"))
            return
        try:
            game_dir = os.path.dirname(self.game_exe_path)
            subprocess.Popen([self.game_exe_path], cwd=game_dir) 
            QApplication.quit()
        except Exception as e:
            QMessageBox.critical(self, tr.get("msg_error", "Error"), f"{tr.get('msg_cant_start', 'Error:')} {str(e)}")

    def load_save_data_from_file(self):
        tr = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["es"])
        if not os.path.exists(self.save_file_path):
            self.json_editor.setText(tr.get("msg_no_save", "Archivo no encontrado."))
            self.tab_basic.setEnabled(False)
            return
            
        try:
            with open(self.save_file_path, 'r', encoding='utf-8') as f:
                raw_data = f.read().strip()
                if raw_data:
                    self.current_data = json.loads(raw_data)
                    self.tab_basic.setEnabled(True)
                    self.update_ui_from_data()
        except Exception as e:
            self.json_editor.setText(f"{tr.get('msg_json_error', 'Error:')}{str(e)}")
            self.tab_basic.setEnabled(False)

    def unlock_all_plants(self):
        for cb in self.plant_checkboxes.values():
            cb.setChecked(True)

    def lock_all_plants(self):
        for cb in self.plant_checkboxes.values():
            cb.setChecked(False)

    def update_ui_from_data(self):
        self.is_updating_ui = True
        
        self.spin_coins.setValue(int(self.current_data.get("coins", 0)))
        self.spin_diamonds.setValue(int(self.current_data.get("diamonds", 0)))
        self.spin_tacos.setValue(int(self.current_data.get("tacos", 0))) 
        
        worldkeys = self.current_data.get("worldkey", {})
        for world, spin in self.world_keys_spins.items():
            spin.setValue(int(worldkeys.get(world, 0)))

        travellog = self.current_data.get("travellog", {})
        mainquests = travellog.get("mainquests", {})
        
        valentines_quest = mainquests.get("valentinespinata2026", {})
        self.spin_valentines.setValue(int(valentines_quest.get("progress", 0)))

        feastivus_quest = mainquests.get("feastivuspinata2025", {})
        self.spin_feastivus.setValue(int(feastivus_quest.get("progress", 0)))

        tangerine_quest = mainquests.get("orangequest0", {})
        self.spin_tangerine.setValue(int(tangerine_quest.get("progress", 0)))

        birthday_quest = mainquests.get("birthdayparty0", {})
        self.spin_birthday.setValue(int(birthday_quest.get("progress", 0)))

        # --- UPGRADES LOGIC ---
        upgrades = self.current_data.get("upgradeprogress", [])
        self.chk_upg_sunshovel_1.setChecked("upgrade_sunshovel_lvl1" in upgrades)
        self.chk_upg_7_slots.setChecked("upgrade_7_slots" in upgrades)
        self.chk_upg_start_sun.setChecked("upgrade_starting_sun_lvl1" in upgrades)
        self.chk_upg_sunshovel_2.setChecked("upgrade_sunshovel_lvl2" in upgrades)

        # --- PLANTS LOGIC (Dynamic creation and update) ---
        plants_data = self.current_data.get("plant", {})
        
        # Iterate over plants that exist in the JSON
        for plant_key, plant_info in plants_data.items():
            # If the plant does not yet have a checkbox in the UI, create it
            if plant_key not in self.plant_checkboxes:
                cb = QCheckBox(plant_key)
                self.plant_checkboxes[plant_key] = cb
                self.plants_grid_layout.addWidget(cb, self.plant_grid_row, self.plant_grid_col)
                
                # Arrange in 3 columns
                self.plant_grid_col += 1
                if self.plant_grid_col > 2:
                    self.plant_grid_col = 0
                    self.plant_grid_row += 1

            # Update checkbox state (1.0 = checked, otherwise unchecked)
            is_owned = (plant_info.get("owned", 0.0) == 1.0)
            self.plant_checkboxes[plant_key].setChecked(is_owned)

        pretty_json = json.dumps(self.current_data, indent=4)
        self.json_editor.setText(pretty_json)
        
        self.is_updating_ui = False

    def update_data_from_basic_ui(self):
        self.current_data["coins"] = float(self.spin_coins.value())
        self.current_data["diamonds"] = float(self.spin_diamonds.value())
        self.current_data["tacos"] = float(self.spin_tacos.value()) 
        
        if "worldkey" not in self.current_data:
            self.current_data["worldkey"] = {}
            
        for world, spin in self.world_keys_spins.items():
            self.current_data["worldkey"][world] = float(spin.value())

        val_progress = float(self.spin_valentines.value())
        fea_progress = float(self.spin_feastivus.value())
        tan_progress = float(self.spin_tangerine.value())
        bday_progress = float(self.spin_birthday.value())
        
        if "travellog" not in self.current_data:
            self.current_data["travellog"] = {"mainquests": {}}
        elif "mainquests" not in self.current_data["travellog"]:
            self.current_data["travellog"]["mainquests"] = {}
            
        val_quest = self.current_data["travellog"]["mainquests"].get("valentinespinata2026", {})
        val_quest["progress"] = val_progress
        val_quest["finished"] = 1.0 if val_progress >= 5.0 else 0.0
        val_quest["anim"] = "new"
        if "displaynum" not in val_quest:
            val_quest["displaynum"] = 0.0
        self.current_data["travellog"]["mainquests"]["valentinespinata2026"] = val_quest

        fea_quest = self.current_data["travellog"]["mainquests"].get("feastivuspinata2025", {})
        fea_quest["progress"] = fea_progress
        fea_quest["finished"] = 1.0 if fea_progress >= 6.0 else 0.0
        fea_quest["anim"] = "new"
        if "displaynum" not in fea_quest:
            fea_quest["displaynum"] = 0.0
        self.current_data["travellog"]["mainquests"]["feastivuspinata2025"] = fea_quest

        tan_quest = self.current_data["travellog"]["mainquests"].get("orangequest0", {})
        tan_quest["progress"] = tan_progress
        tan_quest["finished"] = 1.0 if tan_progress >= 5.0 else 0.0
        tan_quest["anim"] = "new"
        if "displaynum" not in tan_quest:
            tan_quest["displaynum"] = 0.0
        self.current_data["travellog"]["mainquests"]["orangequest0"] = tan_quest

        bday_quest = self.current_data["travellog"]["mainquests"].get("birthdayparty0", {})
        bday_quest["progress"] = bday_progress
        bday_quest["finished"] = 1.0 if bday_progress >= 5.0 else 0.0
        bday_quest["anim"] = "new"
        if "displaynum" not in bday_quest:
            bday_quest["displaynum"] = 0.0
        self.current_data["travellog"]["mainquests"]["birthdayparty0"] = bday_quest

        if "levelprogress" not in self.current_data:
            self.current_data["levelprogress"] = {}
            
        for i in range(1, 6):
            lvl_key = f"valentines20260{i}"
            lvl_data = self.current_data["levelprogress"].get(lvl_key, {"unlocked": 0.0, "anim": "locked", "finished": 0.0})
            if i <= int(val_progress):
                lvl_data["finished"] = 1.0
            else:
                lvl_data["finished"] = 0.0
            self.current_data["levelprogress"][lvl_key] = lvl_data

        for i in range(1, 7):
            lvl_key = f"feastivus20250{i}"
            lvl_data = self.current_data["levelprogress"].get(lvl_key, {"unlocked": 0.0, "anim": "locked", "finished": 0.0})
            if i <= int(fea_progress):
                lvl_data["finished"] = 1.0
            else:
                lvl_data["finished"] = 0.0
            self.current_data["levelprogress"][lvl_key] = lvl_data

        for i in range(1, 6):
            lvl_key = f"orange{i}"
            lvl_data = self.current_data["levelprogress"].get(lvl_key, {"unlocked": 1.0, "anim": "locked", "finished": 0.0})
            if i <= int(tan_progress):
                lvl_data["finished"] = 1.0
                lvl_data["anim"] = "finished"
            else:
                lvl_data["finished"] = 0.0
            self.current_data["levelprogress"][lvl_key] = lvl_data

        for i in range(1, 6):
            lvl_key = f"birthday{i}"
            lvl_data = self.current_data["levelprogress"].get(lvl_key, {"unlocked": 1.0, "anim": "unlocked", "finished": 0.0})
            if i <= int(bday_progress):
                lvl_data["finished"] = 1.0
            else:
                lvl_data["finished"] = 0.0
            self.current_data["levelprogress"][lvl_key] = lvl_data

        # --- UPGRADES LOGIC (Save to JSON) ---
        new_upgrades = []
        if self.chk_upg_sunshovel_1.isChecked(): new_upgrades.append("upgrade_sunshovel_lvl1")
        if self.chk_upg_7_slots.isChecked(): new_upgrades.append("upgrade_7_slots")
        if self.chk_upg_start_sun.isChecked(): new_upgrades.append("upgrade_starting_sun_lvl1")
        if self.chk_upg_sunshovel_2.isChecked(): new_upgrades.append("upgrade_sunshovel_lvl2")
        self.current_data["upgradeprogress"] = new_upgrades

        # --- PLANTS LOGIC (Save to JSON) ---
        if "plant" in self.current_data:
            for plant_key, cb in self.plant_checkboxes.items():
                if plant_key in self.current_data["plant"]:
                    # Save as 1.0 if checked, 0.0 if unchecked
                    self.current_data["plant"][plant_key]["owned"] = 1.0 if cb.isChecked() else 0.0

    def update_data_from_advanced_ui(self):
        tr = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["es"])
        text_data = self.json_editor.toPlainText()
        if text_data.startswith('//'):
            return False
        try:
            self.current_data = json.loads(text_data)
            return True
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, tr.get("msg_error", "Error"), f"{tr.get('msg_json_invalid', 'Inválido:')}{str(e)}")
            return False

    def on_tab_changed(self, index):
        if self.is_updating_ui or not self.current_data:
            return
            
        if index == 1: 
            self.update_data_from_basic_ui()
            self.update_ui_from_data() 
        elif index == 0: 
            success = self.update_data_from_advanced_ui()
            if success:
                self.update_ui_from_data()
            else:
                self.tabs.setCurrentIndex(1)

    def import_save(self):
        tr = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["es"])
        file_path, _ = QFileDialog.getOpenFileName(self, tr.get("fd_import", "Importar"), "", "Save Files (*.sav *.json)")
        if file_path:
            try:
                os.makedirs(self.save_dir, exist_ok=True)
                shutil.copy2(file_path, self.save_file_path)
                QMessageBox.information(self, tr.get("msg_success", "Éxito"), tr.get("msg_imported", "Importado"))
                self.load_save_data_from_file()
            except Exception as e:
                QMessageBox.critical(self, tr.get("msg_error", "Error"), f"{tr.get('msg_error', 'Error')}: {str(e)}")

    def export_save(self):
        tr = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["es"])
        if not self.current_data:
            QMessageBox.warning(self, tr.get("msg_error", "Error"), tr.get("msg_no_data", "Sin datos"))
            return

        if self.tabs.currentIndex() == 0:
            self.update_data_from_basic_ui()
        else:
            if not self.update_data_from_advanced_ui():
                return

        if self.export_format == "json":
            default_name = "pvz_save_export.json"
            file_filter = "JSON Files (*.json)"
        else:
            default_name = "pvz_save_export.sav"
            file_filter = "Save Files (*.sav)"

        file_path, _ = QFileDialog.getSaveFileName(self, tr.get("fd_export", "Exportar"), default_name, file_filter)
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if self.export_format == "json":
                        json.dump(self.current_data, f, indent=4)
                    else:
                        json.dump(self.current_data, f, separators=(',', ':'))
                QMessageBox.information(self, tr.get("msg_success", "Éxito"), f"{tr.get('msg_exported', 'Exportado')}.{self.export_format}")
            except Exception as e:
                QMessageBox.critical(self, tr.get("msg_error", "Error"), f"{tr.get('msg_error', 'Error')}: {str(e)}")

    def save_to_game_file(self):
        tr = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["es"])
        if not self.current_data:
            return

        if self.tabs.currentIndex() == 0:
            self.update_data_from_basic_ui()
        else:
            if not self.update_data_from_advanced_ui():
                return

        try:
            single_line_json = json.dumps(self.current_data, separators=(',', ':'))
            
            os.makedirs(self.save_dir, exist_ok=True)
            with open(self.save_file_path, 'w', encoding='utf-8') as f:
                f.write(single_line_json)
                
            QMessageBox.information(self, tr.get("msg_success", "Éxito"), tr.get("msg_saved", "Guardado"))
            self.update_ui_from_data() 
        except Exception as e:
            QMessageBox.critical(self, tr.get("msg_error", "Error"), f"{tr.get('msg_error', 'Error')}: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = PVZSaveManager()
    window.show()
    sys.exit(app.exec())