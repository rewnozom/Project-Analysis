# Imports for settings_panel.py
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
    QLabel, QLineEdit, QToolButton, QGroupBox, 
    QComboBox, QCheckBox, QTextEdit, QFileDialog
)
from PySide6.QtCore import Qt


class SettingsPanel(QWidget):
    """
    Widget for analysis settings.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Create general settings group
        general_group = QGroupBox("General Settings")
        general_group.setStyleSheet("""
            QGroupBox {
                color: #d1cccc;
                font-weight: bold;
                border: 1px solid rgba(82, 82, 82, 0.5);
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 5px;
            }
        """)
        general_layout = QGridLayout(general_group)
        general_layout.setSpacing(12)
        
        # Output directory setting
        output_label = QLabel("Output Directory:")
        output_label.setStyleSheet("color: #d1cccc;")
        
        self.output_path = QLineEdit()
        self.output_path.setText(os.path.join(os.path.expanduser("~"), "project_analysis"))
        self.output_path.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #d1cccc;
                border: 1px solid rgba(82, 82, 82, 0.5);
                border-radius: 4px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #fb923c;
            }
        """)
        
        output_browse = QToolButton()
        output_browse.setText("...")
        output_browse.setStyleSheet("""
            QToolButton {
                background-color: #1a1a1a;
                color: #d1cccc;
                border: 1px solid rgba(82, 82, 82, 0.5);
                border-radius: 4px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #3a3939;
                border: 1px solid #fb923c;
            }
            QToolButton:pressed {
                background-color: #ea580c;
                color: white;
            }
        """)
        output_browse.clicked.connect(self.browse_output_dir)
        
        general_layout.addWidget(output_label, 0, 0)
        general_layout.addWidget(self.output_path, 0, 1)
        general_layout.addWidget(output_browse, 0, 2)
        
        # Max depth setting
        depth_label = QLabel("Maximum Search Depth:")
        depth_label.setStyleSheet("color: #d1cccc;")
        
        self.max_depth = QComboBox()
        self.max_depth.addItems(["1", "2", "3", "4", "5"])
        self.max_depth.setCurrentIndex(2)  # Default to 3
        self.max_depth.setStyleSheet("""
            QComboBox {
                background-color: #1a1a1a;
                color: #d1cccc;
                border: 1px solid rgba(82, 82, 82, 0.5);
                border-radius: 4px;
                padding: 8px;
            }
            QComboBox:focus {
                border: 1px solid #fb923c;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 15px;
                border-left: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #d1cccc;
                border: 1px solid #fb923c;
                selection-background-color: #fb923c;
                selection-color: white;
            }
        """)
        
        general_layout.addWidget(depth_label, 1, 0)
        general_layout.addWidget(self.max_depth, 1, 1, 1, 2)
        
        # Parallel workers setting
        workers_label = QLabel("Parallel Workers:")
        workers_label.setStyleSheet("color: #d1cccc;")
        
        self.max_workers = QComboBox()
        self.max_workers.addItems(["1", "2", "4", "8", "16"])
        self.max_workers.setCurrentIndex(2)  # Default to 4
        self.max_workers.setStyleSheet(self.max_depth.styleSheet())
        
        general_layout.addWidget(workers_label, 2, 0)
        general_layout.addWidget(self.max_workers, 2, 1, 1, 2)
        
        # Add general settings to main layout
        layout.addWidget(general_group)
        
        # Create detection settings group
        detection_group = QGroupBox("Detection Settings")
        detection_group.setStyleSheet(general_group.styleSheet())
        detection_layout = QVBoxLayout(detection_group)
        detection_layout.setSpacing(12)
        
        # Microservice detection checkbox
        self.detect_microservices = QCheckBox("Detect Microservice Architecture")
        self.detect_microservices.setChecked(True)
        self.detect_microservices.setStyleSheet("""
            QCheckBox {
                color: #d1cccc;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid rgba(82, 82, 82, 0.7);
                border-radius: 4px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #1a1a1a;
            }
            QCheckBox::indicator:checked {
                background-color: #fb923c;
                border: 1px solid #fb923c;
            }
            QCheckBox::indicator:unchecked:hover, QCheckBox::indicator:checked:hover {
                border: 1px solid #fb923c;
            }
        """)
        
        # Verbose logging checkbox
        self.verbose_logging = QCheckBox("Enable Verbose Logging")
        self.verbose_logging.setChecked(False)
        self.verbose_logging.setStyleSheet(self.detect_microservices.styleSheet())
        
        detection_layout.addWidget(self.detect_microservices)
        detection_layout.addWidget(self.verbose_logging)
        detection_layout.addStretch()
        
        # Add detection settings to main layout
        layout.addWidget(detection_group)
        
        # Create ignore patterns group
        ignore_group = QGroupBox("Ignore Patterns")
        ignore_group.setStyleSheet(general_group.styleSheet())
        ignore_layout = QVBoxLayout(ignore_group)
        
        # Ignore patterns text edit
        self.ignore_patterns = QTextEdit()
        self.ignore_patterns.setPlaceholderText("Enter patterns to ignore, one per line (e.g., node_modules, venv, *.pyc)")
        self.ignore_patterns.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #d1cccc;
                border: 1px solid rgba(82, 82, 82, 0.5);
                border-radius: 4px;
                padding: 4px;
            }
            QTextEdit:focus {
                border: 1px solid #fb923c;
            }
        """)
        
        # Set some default patterns
        default_patterns = [
            "node_modules", "venv", ".venv", "__pycache__",
            "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dylib", "*.dll",
            ".git", ".svn", ".hg", ".DS_Store"
        ]
        self.ignore_patterns.setText("\n".join(default_patterns))
        
        ignore_layout.addWidget(self.ignore_patterns)
        
        # Add ignore patterns to main layout
        layout.addWidget(ignore_group)
        
        # Add spacer to push everything up
        layout.addStretch()
    
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_path.text()
        )
        
        if directory:
            self.output_path.setText(directory)
    
    def get_settings(self):
        """Get all settings as a dictionary."""
        # Parse ignore patterns
        ignore_patterns = []
        for line in self.ignore_patterns.toPlainText().strip().split("\n"):
            line = line.strip()
            if line:
                ignore_patterns.append(line)
        
        return {
            'output_dir': self.output_path.text(),
            'max_depth': int(self.max_depth.currentText()),
            'max_workers': int(self.max_workers.currentText()),
            'detect_microservices': self.detect_microservices.isChecked(),
            'verbose': self.verbose_logging.isChecked(),
            'ignore_patterns': ignore_patterns
        }