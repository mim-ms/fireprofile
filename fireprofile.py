#!/usr/bin/env python3

import sys
import json
import os
import signal
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QLineEdit,
                              QComboBox, QTableWidget, QTableWidgetItem,
                              QDialog, QMessageBox, QTabWidget, QStyleFactory,
                              QHeaderView, QCheckBox)
from PySide6.QtCore import Qt, QTimer

CONFIG_FILE = os.path.expanduser("~/.fireprofile.json")

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {"profiles": [], "domains": {}}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_profiles(self):
        return self.config.get("profiles", [])

    def add_profile(self, name, command):
        self.config["profiles"].append({"name": name, "command": command})
        self.save_config()

    def remove_profile(self, name):
        self.config["profiles"] = [p for p in self.config["profiles"] if p["name"] != name]
        # Remove associated domain rules
        self.config["domains"] = {d: p for d, p in self.config["domains"].items() if p != name}
        self.save_config()

    def get_domain_profile(self, domain):
        return self.config["domains"].get(domain)

    def set_domain_profile(self, domain, profile):
        self.config["domains"][domain] = profile
        self.save_config()

    def remove_domain(self, domain):
        if domain in self.config["domains"]:
            del self.config["domains"][domain]
            self.save_config()

class ProfileDialog(QDialog):
    def __init__(self, profiles, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Profile")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        self.profile_combo = QComboBox()
        for profile in profiles:
            self.profile_combo.addItem(profile["name"])
        
        # Add checkbox for automatic rule creation
        self.remember_choice = QCheckBox("Remember this choice")
        self.remember_choice.setChecked(True)  # Checked by default
        
        buttons = QHBoxLayout()
        open_btn = QPushButton("Open")
        cancel_btn = QPushButton("Cancel")
        
        open_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addWidget(open_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addWidget(QLabel("Select Firefox Profile:"))
        layout.addWidget(self.profile_combo)
        layout.addWidget(self.remember_choice)
        layout.addLayout(buttons)
        
        self.setLayout(layout)

class ConfigWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("FireProfile Configuration")
        self.setMinimumSize(800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        tabs = QTabWidget()
        
        # Profile Management Tab
        profile_tab = QWidget()
        profile_layout = QVBoxLayout(profile_tab)
        
        # Profile input fields
        input_layout = QHBoxLayout()
        self.profile_name = QLineEdit()
        self.profile_name.setPlaceholderText("Profile Name")
        self.profile_command = QLineEdit()
        self.profile_command.setPlaceholderText("Firefox Command (e.g., firefox -P profile1)")
        add_profile_btn = QPushButton("Add Profile")
        add_profile_btn.clicked.connect(self.add_profile)
        
        input_layout.addWidget(self.profile_name)
        input_layout.addWidget(self.profile_command)
        input_layout.addWidget(add_profile_btn)
        
        # Profile table
        self.profile_table = QTableWidget()
        self.profile_table.setColumnCount(4)
        self.profile_table.setHorizontalHeaderLabels(["Profile Name", "Command", "Edit", "Delete"])
        self.profile_table.horizontalHeader().setStretchLastSection(False)
        self.profile_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.profile_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.profile_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.profile_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.profile_table.setColumnWidth(2, 40)  # Edit column width
        self.profile_table.setColumnWidth(3, 40)  # Delete column width
        
        # Save button
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_profile_changes)
        
        profile_layout.addLayout(input_layout)
        profile_layout.addWidget(self.profile_table)
        profile_layout.addWidget(save_btn)
        
        # Domain Management Tab
        domain_tab = QWidget()
        domain_layout = QVBoxLayout(domain_tab)
        
        # Domain input fields
        domain_input_layout = QHBoxLayout()
        self.domain_name = QLineEdit()
        self.domain_name.setPlaceholderText("Domain (e.g., example.com)")
        self.domain_profile = QComboBox()
        add_domain_btn = QPushButton("Add Domain Rule")
        add_domain_btn.clicked.connect(self.add_domain)
        
        domain_input_layout.addWidget(self.domain_name)
        domain_input_layout.addWidget(self.domain_profile)
        domain_input_layout.addWidget(add_domain_btn)
        
        # Domain table
        self.domain_table = QTableWidget()
        self.domain_table.setColumnCount(3)
        self.domain_table.setHorizontalHeaderLabels(["Domain", "Profile", "Delete"])
        self.domain_table.horizontalHeader().setStretchLastSection(False)
        self.domain_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.domain_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.domain_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.domain_table.setColumnWidth(2, 40)  # Delete column width
        
        # Save button for domain rules
        domain_save_btn = QPushButton("Save Changes")
        domain_save_btn.clicked.connect(self.save_domain_changes)
        
        domain_layout.addLayout(domain_input_layout)
        domain_layout.addWidget(self.domain_table)
        domain_layout.addWidget(domain_save_btn)
        
        tabs.addTab(profile_tab, "Profile Management")
        tabs.addTab(domain_tab, "Domain Rules")
        
        layout.addWidget(tabs)
        
        self.refresh_tables()

    def refresh_tables(self):
        # Refresh profile table
        profiles = self.config_manager.get_profiles()
        self.profile_table.setRowCount(len(profiles))
        for i, profile in enumerate(profiles):
            # Make name and command editable
            name_item = QTableWidgetItem(profile["name"])
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            command_item = QTableWidgetItem(profile["command"])
            command_item.setFlags(command_item.flags() | Qt.ItemIsEditable)
            
            self.profile_table.setItem(i, 0, name_item)
            self.profile_table.setItem(i, 1, command_item)
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(40)
            edit_btn.clicked.connect(lambda checked, row=i: self.edit_profile(row))
            self.profile_table.setCellWidget(i, 2, edit_btn)
            
            # Delete button
            delete_btn = QPushButton("×")  # Using × symbol for delete
            delete_btn.setFixedWidth(40)
            delete_btn.clicked.connect(lambda checked, name=profile["name"]: self.delete_profile(name))
            self.profile_table.setCellWidget(i, 3, delete_btn)
        
        # Refresh domain table
        domains = self.config_manager.config["domains"]
        self.domain_table.setRowCount(len(domains))
        for i, (domain, profile) in enumerate(domains.items()):
            self.domain_table.setItem(i, 0, QTableWidgetItem(domain))
            
            # Create a combo box for profile selection
            profile_combo = QComboBox()
            for p in profiles:
                profile_combo.addItem(p["name"])
            # Set the current profile
            index = profile_combo.findText(profile)
            if index >= 0:
                profile_combo.setCurrentIndex(index)
            # Connect the change signal
            profile_combo.currentTextChanged.connect(
                lambda text, d=domain: self.update_domain_profile(d, text)
            )
            self.domain_table.setCellWidget(i, 1, profile_combo)
            
            # Delete button
            delete_btn = QPushButton("×")  # Using × symbol for delete
            delete_btn.setFixedWidth(40)
            delete_btn.clicked.connect(lambda checked, d=domain: self.delete_domain(d))
            self.domain_table.setCellWidget(i, 2, delete_btn)
        
        # Refresh domain profile combo
        self.domain_profile.clear()
        for profile in profiles:
            self.domain_profile.addItem(profile["name"])

    def update_domain_profile(self, domain, new_profile):
        """Update the profile for a domain when changed in the table"""
        self.config_manager.set_domain_profile(domain, new_profile)

    def add_profile(self):
        name = self.profile_name.text().strip()
        command = self.profile_command.text().strip()
        
        if not name or not command:
            QMessageBox.warning(self, "Error", "Please fill in all fields")
            return
        
        self.config_manager.add_profile(name, command)
        self.profile_name.clear()
        self.profile_command.clear()
        self.refresh_tables()

    def delete_profile(self, name):
        reply = QMessageBox.question(self, "Confirm Delete",
                                   f"Are you sure you want to delete profile '{name}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.config_manager.remove_profile(name)
            self.refresh_tables()

    def add_domain(self):
        domain = self.domain_name.text().strip()
        profile = self.domain_profile.currentText()
        
        if not domain:
            QMessageBox.warning(self, "Error", "Please enter a domain")
            return
        
        self.config_manager.set_domain_profile(domain, profile)
        self.domain_name.clear()
        self.refresh_tables()

    def delete_domain(self, domain):
        reply = QMessageBox.question(self, "Confirm Delete",
                                   f"Are you sure you want to delete domain rule for '{domain}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.config_manager.remove_domain(domain)
            self.refresh_tables()

    def edit_profile(self, row):
        """Enable editing for the selected profile row"""
        self.profile_table.setCurrentCell(row, 0)
        self.profile_table.editItem(self.profile_table.item(row, 0))

    def save_profile_changes(self):
        """Save changes made to profiles"""
        profiles = []
        for row in range(self.profile_table.rowCount()):
            name = self.profile_table.item(row, 0).text().strip()
            command = self.profile_table.item(row, 1).text().strip()
            
            if name and command:
                profiles.append({"name": name, "command": command})
        
        # Update the configuration
        self.config_manager.config["profiles"] = profiles
        self.config_manager.save_config()
        
        # Refresh the tables to ensure everything is in sync
        self.refresh_tables()
        
        QMessageBox.information(self, "Success", "Profile changes saved successfully!")

    def save_domain_changes(self):
        """Save changes made to domain rules"""
        # The changes are already saved when profile selections change
        # This is just to provide feedback to the user
        QMessageBox.information(self, "Success", "Domain rules saved successfully!")

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    print("\nReceived termination signal. Exiting gracefully...")
    QApplication.quit()

def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    app = QApplication(sys.argv)
    
    # Set the application style to the system's default style
    if "Fusion" in QStyleFactory.keys():
        app.setStyle("Fusion")  # Fusion is a good fallback if system style isn't available
    
    # Create a timer to process signals in the Qt event loop
    timer = QTimer()
    timer.timeout.connect(lambda: None)  # Empty function to keep timer running
    timer.start(100)  # Check every 100ms
    
    # Launch config window if --config flag is used or no URL is provided
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        window = ConfigWindow()
        window.show()
    elif len(sys.argv) < 2:
        # No URL provided, launch config window
        window = ConfigWindow()
        window.show()
    else:
        # Handle URL opening
        url = sys.argv[1]
        config_manager = ConfigManager()
        
        # Extract domain from URL
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Check if we have a rule for this domain or any of its subdomains
        profile_name = None
        for config_domain, profile in config_manager.config["domains"].items():
            if domain == config_domain or domain.endswith(f".{config_domain}"):
                profile_name = profile
                break
        
        if profile_name:
            # Find the profile command
            profile = next((p for p in config_manager.get_profiles() if p["name"] == profile_name), None)
            if profile:
                os.system(f"{profile['command']} {url}")
                sys.exit(0)
        
        # No rule found, show profile selector
        dialog = ProfileDialog(config_manager.get_profiles())
        if dialog.exec_() == QDialog.Accepted:
            profile_name = dialog.profile_combo.currentText()
            profile = next((p for p in config_manager.get_profiles() if p["name"] == profile_name), None)
            if profile:
                # Create domain rule if checkbox is checked
                if dialog.remember_choice.isChecked():
                    # Extract parent domain (e.g., example.com from sub.example.com)
                    parts = domain.split('.')
                    if len(parts) > 1:
                        parent_domain = '.'.join(parts[-2:])  # Get last two parts for parent domain
                        config_manager.set_domain_profile(parent_domain, profile_name)
                os.system(f"{profile['command']} {url}")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 