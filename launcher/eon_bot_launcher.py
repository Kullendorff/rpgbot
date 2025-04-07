import sys
import os
import json
import subprocess
import threading
import webbrowser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QTabWidget, QGroupBox, QMessageBox, QFileDialog,
                            QTextEdit, QCheckBox, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPalette
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QThread

class BotThread(QThread):
    status_update = pyqtSignal(str)
    
    def __init__(self, config_path):
        super().__init__()
        self.config_path = config_path
        self.process = None
        self.running = False
        
    def run(self):
        try:
            # Läs konfigurationen
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Skapa miljövariabler
            env = os.environ.copy()
            env['DISCORD_TOKEN'] = config.get('discord_token', '')
            env['PINECONE_API_KEY'] = config.get('pinecone_api_key', '')
            env['ANTHROPIC_API_KEY'] = config.get('anthropic_api_key', '')
            env['OPENAI_API_KEY'] = config.get('openai_api_key', '')
            env['CHANNEL_IDS'] = config.get('channel_ids', '')
            env['PINECONE_INDEX_NAME'] = config.get('pinecone_index_name', 'rpg-knowledge')
            
            # Hitta huvudskriptet (anta att det är main.py i src-mappen)
            script_path = os.path.join(os.path.dirname(self.config_path), 'src', 'main.py')
            if not os.path.exists(script_path):
                # Sök efter ett Python-huvudskript
                for root, _, files in os.walk(os.path.dirname(self.config_path)):
                    for file in files:
                        if file.endswith('.py'):
                            with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if 'discord.ext.commands' in content and 'bot.run' in content:
                                    script_path = os.path.join(root, file)
                                    break
                    if script_path != os.path.join(os.path.dirname(self.config_path), 'src', 'main.py'):
                        break
            
            self.status_update.emit(f"Startar boten med skript: {script_path}")
            
            # Starta boten
            self.running = True
            self.process = subprocess.Popen(
                [sys.executable, script_path],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Läs och skicka output
            while self.running and self.process.poll() is None:
                stdout_line = self.process.stdout.readline()
                if stdout_line:
                    self.status_update.emit(stdout_line.strip())
                
                stderr_line = self.process.stderr.readline()
                if stderr_line:
                    self.status_update.emit("FEL: " + stderr_line.strip())
                    
            if self.process.poll() is not None:
                self.status_update.emit(f"Boten avslutades med kod: {self.process.returncode}")
                
        except Exception as e:
            self.status_update.emit(f"Ett fel uppstod: {str(e)}")
            
    def stop(self):
        self.running = False
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.status_update.emit("Boten har stoppats")


class EONBotLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EON Diceroller Bot Launcher")
        self.setMinimumSize(800, 600)
        
        # Konfigurera färger och stil
        self.setup_style()
        
        # Huvudwidget och layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Titelbanner
        title_layout = QHBoxLayout()
        title_label = QLabel("EON Diceroller Bot")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        main_layout.addLayout(title_layout)
        
        # Flikar för olika delar av appen
        self.tabs = QTabWidget()
        
        # Skapa flikar
        self.setup_tab = QWidget()
        self.logs_tab = QWidget()
        self.help_tab = QWidget()
        
        self.tabs.addTab(self.setup_tab, "Inställningar")
        self.tabs.addTab(self.logs_tab, "Logg")
        self.tabs.addTab(self.help_tab, "Hjälp")
        
        # Skapa innehåll för varje flik
        self.setup_setup_tab()
        self.setup_logs_tab()
        self.setup_help_tab()
        
        main_layout.addWidget(self.tabs)
        
        # Statusraden längst ner
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Redo att starta")
        
        # Bot-tråd
        self.bot_thread = None
        
        # Standardsökväg för konfigurationsfil
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eon_bot_config.json")
        
        # Förinställ sökväg till bot-koden (antar att launchers ligger i launcher-mapp i rotkatalogen)
        bot_root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.default_bot_path = bot_root_path
        
        # Läs in konfiguration om den finns
        self.load_config()
        
    def setup_style(self):
        # Konfigurera färger och stil
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(palette)
        
    def setup_setup_tab(self):
        layout = QVBoxLayout(self.setup_tab)
        
        # API-nyckelkonfiguration
        api_group = QGroupBox("API-nycklar")
        api_layout = QVBoxLayout()
        
        # Discord Token
        discord_layout = QHBoxLayout()
        discord_label = QLabel("Discord Token:")
        self.discord_token_input = QLineEdit()
        self.discord_token_input.setEchoMode(QLineEdit.Password)
        discord_help_btn = QPushButton("?")
        discord_help_btn.setFixedSize(25, 25)
        discord_help_btn.clicked.connect(lambda: self.open_help_url("https://discord.com/developers/applications"))
        
        discord_layout.addWidget(discord_label)
        discord_layout.addWidget(self.discord_token_input)
        discord_layout.addWidget(discord_help_btn)
        api_layout.addLayout(discord_layout)
        
        # Pinecone API
        pinecone_layout = QHBoxLayout()
        pinecone_label = QLabel("Pinecone API-nyckel:")
        self.pinecone_api_input = QLineEdit()
        self.pinecone_api_input.setEchoMode(QLineEdit.Password)
        pinecone_help_btn = QPushButton("?")
        pinecone_help_btn.setFixedSize(25, 25)
        pinecone_help_btn.clicked.connect(lambda: self.open_help_url("https://app.pinecone.io/"))
        
        pinecone_layout.addWidget(pinecone_label)
        pinecone_layout.addWidget(self.pinecone_api_input)
        pinecone_layout.addWidget(pinecone_help_btn)
        api_layout.addLayout(pinecone_layout)
        
        # Anthropic Claude API
        anthropic_layout = QHBoxLayout()
        anthropic_label = QLabel("Anthropic Claude API-nyckel:")
        self.anthropic_api_input = QLineEdit()
        self.anthropic_api_input.setEchoMode(QLineEdit.Password)
        anthropic_help_btn = QPushButton("?")
        anthropic_help_btn.setFixedSize(25, 25)
        anthropic_help_btn.clicked.connect(lambda: self.open_help_url("https://console.anthropic.com/"))
        
        anthropic_layout.addWidget(anthropic_label)
        anthropic_layout.addWidget(self.anthropic_api_input)
        anthropic_layout.addWidget(anthropic_help_btn)
        api_layout.addLayout(anthropic_layout)
        
        # OpenAI API
        openai_layout = QHBoxLayout()
        openai_label = QLabel("OpenAI API-nyckel:")
        self.openai_api_input = QLineEdit()
        self.openai_api_input.setEchoMode(QLineEdit.Password)
        openai_help_btn = QPushButton("?")
        openai_help_btn.setFixedSize(25, 25)
        openai_help_btn.clicked.connect(lambda: self.open_help_url("https://platform.openai.com/"))
        
        openai_layout.addWidget(openai_label)
        openai_layout.addWidget(self.openai_api_input)
        openai_layout.addWidget(openai_help_btn)
        api_layout.addLayout(openai_layout)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Discord-konfiguration
        discord_group = QGroupBox("Discord-konfiguration")
        discord_config_layout = QVBoxLayout()
        
        # Kanal IDs
        channel_layout = QHBoxLayout()
        channel_label = QLabel("Kanal IDs (kommaseparerade):")
        self.channel_ids_input = QLineEdit()
        channel_help_btn = QPushButton("?")
        channel_help_btn.setFixedSize(25, 25)
        channel_help_btn.clicked.connect(self.show_channel_id_help)
        
        channel_layout.addWidget(channel_label)
        channel_layout.addWidget(self.channel_ids_input)
        channel_layout.addWidget(channel_help_btn)
        discord_config_layout.addLayout(channel_layout)
        
        # Pinecone index
        pinecone_index_layout = QHBoxLayout()
        pinecone_index_label = QLabel("Pinecone Index-namn:")
        self.pinecone_index_input = QLineEdit()
        self.pinecone_index_input.setText("rpg-knowledge")  # Standardvärde
        
        pinecone_index_layout.addWidget(pinecone_index_label)
        pinecone_index_layout.addWidget(self.pinecone_index_input)
        discord_config_layout.addLayout(pinecone_index_layout)
        
        discord_group.setLayout(discord_config_layout)
        layout.addWidget(discord_group)
        
        # Bot-sökväg
        path_group = QGroupBox("Bot-inställningar")
        path_layout = QHBoxLayout()
        
        path_label = QLabel("Sökväg till bot-kod:")
        self.path_input = QLineEdit()
        browse_btn = QPushButton("Bläddra...")
        browse_btn.clicked.connect(self.browse_for_bot)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # Kontrollknappar
        controls_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Spara inställningar")
        self.save_btn.clicked.connect(self.save_config)
        
        self.start_btn = QPushButton("Starta bot")
        self.start_btn.clicked.connect(self.toggle_bot)
        
        controls_layout.addWidget(self.save_btn)
        controls_layout.addWidget(self.start_btn)
        
        layout.addLayout(controls_layout)
        layout.addStretch()
        
    def setup_logs_tab(self):
        layout = QVBoxLayout(self.logs_tab)
        
        # Loggvisare
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        
        # Rensa-knapp
        clear_btn = QPushButton("Rensa logg")
        clear_btn.clicked.connect(self.log_output.clear)
        layout.addWidget(clear_btn)
        
    def setup_help_tab(self):
        layout = QVBoxLayout(self.help_tab)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>Hjälp för EON Diceroller Bot</h2>
        
        <h3>Att komma igång</h3>
        <p>För att köra EON Diceroller Bot behöver du:</p>
        <ol>
            <li>En Discord-bot token</li>
            <li>En Pinecone API-nyckel</li>
            <li>En Anthropic Claude API-nyckel</li>
            <li>En OpenAI API-nyckel</li>
            <li>ID för Discord-kanaler där boten ska vara aktiv (valfritt)</li>
        </ol>
        
        <h3>Skaffa API-nycklar</h3>
        <p><b>Discord Token:</b> Gå till <a href="https://discord.com/developers/applications">Discord Developer Portal</a>, skapa en applikation, lägg till en bot, och kopiera token.</p>
        <p><b>Pinecone API:</b> Skapa ett konto på <a href="https://app.pinecone.io/">Pinecone</a> och hämta din API-nyckel.</p>
        <p><b>Anthropic Claude API:</b> Skaffa en API-nyckel från <a href="https://console.anthropic.com/">Anthropic Console</a>.</p>
        <p><b>OpenAI API:</b> Skaffa en API-nyckel från <a href="https://platform.openai.com/">OpenAI Platform</a>.</p>
        
        <h3>Hitta kanal-ID i Discord</h3>
        <p>För att hitta ett kanal-ID i Discord:</p>
        <ol>
            <li>Aktivera utvecklarläge i Discord (Inställningar -> Avancerat -> Utvecklarläge)</li>
            <li>Högerklicka på en kanal</li>
            <li>Välj "Kopiera ID"</li>
        </ol>
        
        <h3>Bot-kommandon</h3>
        <p>EON Diceroller Bot har följande huvudfunktioner:</p>
        <ul>
            <li><b>Tärningskast:</b> !roll, !ex, !count</li>
            <li><b>Hemliga tärningskast:</b> !secret</li>
            <li><b>Kunskapsbas:</b> !ask, !sök, !allt</li>
            <li><b>Regler:</b> !regel</li>
            <li><b>Stridssimulering:</b> !hugg, !stick, !kross, !fummel</li>
            <li><b>Statistik:</b> !stats, !mystats</li>
            <li><b>Sessionshantering:</b> !startsession, !endsession</li>
        </ul>
        """)
        
        layout.addWidget(help_text)
        
    def open_help_url(self, url):
        webbrowser.open(url)
        
    def show_channel_id_help(self):
        msg = QMessageBox()
        msg.setWindowTitle("Hitta Discord Kanal ID")
        msg.setText("""
        För att hitta ett kanal-ID i Discord:
        
        1. Aktivera utvecklarläge i Discord:
           - Gå till Användarinställningar
           - Välj Avancerat
           - Slå på "Utvecklarläge"
           
        2. Högerklicka på en kanal
        
        3. Välj "Kopiera ID"
        
        Du kan ange flera kanal-ID separerade med kommatecken.
        """)
        msg.exec_()
        
    def browse_for_bot(self):
        folder = QFileDialog.getExistingDirectory(self, "Välj mapp med bot-kod")
        if folder:
            self.path_input.setText(folder)
            
    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                self.discord_token_input.setText(config.get('discord_token', ''))
                self.pinecone_api_input.setText(config.get('pinecone_api_key', ''))
                self.anthropic_api_input.setText(config.get('anthropic_api_key', ''))
                self.openai_api_input.setText(config.get('openai_api_key', ''))
                self.channel_ids_input.setText(config.get('channel_ids', ''))
                self.pinecone_index_input.setText(config.get('pinecone_index_name', 'rpg-knowledge'))
                self.path_input.setText(config.get('bot_path', self.default_bot_path))
                
                self.log_message("Konfiguration laddad")
        except Exception as e:
            self.log_message(f"Kunde inte ladda konfiguration: {str(e)}")
            
    def save_config(self):
        try:
            config = {
                'discord_token': self.discord_token_input.text(),
                'pinecone_api_key': self.pinecone_api_input.text(),
                'anthropic_api_key': self.anthropic_api_input.text(),
                'openai_api_key': self.openai_api_input.text(),
                'channel_ids': self.channel_ids_input.text(),
                'pinecone_index_name': self.pinecone_index_input.text(),
                'bot_path': self.path_input.text()
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
            self.log_message("Konfiguration sparad")
            self.status_bar.showMessage("Konfiguration sparad", 3000)
            
            return True
        except Exception as e:
            self.log_message(f"Kunde inte spara konfiguration: {str(e)}")
            self.status_bar.showMessage("Fel vid sparande av konfiguration", 3000)
            return False
            
    def log_message(self, message):
        self.log_output.append(f"[{self.get_timestamp()}] {message}")
        
    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def toggle_bot(self):
        if self.bot_thread is None or not self.bot_thread.isRunning():
            # Spara konfigurationen först
            if not self.save_config():
                return
                
            # Kontrollera om bot-sökvägen finns
            bot_path = self.path_input.text()
            if not bot_path or not os.path.exists(bot_path):
                QMessageBox.warning(self, "Felaktig sökväg", 
                                    "Bot-sökvägen finns inte. Välj en giltig sökväg.")
                return
                
            # Starta bot-tråden
            self.bot_thread = BotThread(self.config_path)
            self.bot_thread.status_update.connect(self.log_message)
            self.bot_thread.start()
            
            # Uppdatera UI
            self.start_btn.setText("Stoppa bot")
            self.status_bar.showMessage("Bot startad")
        else:
            # Stoppa bot-tråden
            self.bot_thread.stop()
            self.bot_thread.wait()
            
            # Uppdatera UI
            self.start_btn.setText("Starta bot")
            self.status_bar.showMessage("Bot stoppad")
            
    def closeEvent(self, event):
        if self.bot_thread is not None and self.bot_thread.isRunning():
            reply = QMessageBox.question(self, 'Avsluta', 
                                         "Boten körs fortfarande. Vill du stoppa den och avsluta?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                self.bot_thread.stop()
                self.bot_thread.wait()
            else:
                event.ignore()
                return
                
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EONBotLauncher()
    window.show()
    sys.exit(app.exec_())