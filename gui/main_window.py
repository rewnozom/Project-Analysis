

# Imports for main_window.py



import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import time
import json

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QTabWidget, QProgressBar, 
    QTextEdit, QScrollArea, QFrame, QSplitter, QStatusBar, 
    QTreeWidget, QTreeWidgetItem, QLineEdit, QGridLayout, QGroupBox,
    QComboBox, QCheckBox, QToolButton, QMessageBox, QSpacerItem,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QUrl, QTimer
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QAction, QDesktopServices

# Import custom modules
from gui.path_selector import PathSelector
from gui.settings_panel import SettingsPanel
from gui.analyzer_thread import AnalyzerThread
from gui.chart_widgets import BarChartWidget, DonutChartWidget


class ProjectAnalyzerGUI(QMainWindow):
    """
    Main window for the Project Analyzer GUI.
    """
    def __init__(self):
        super().__init__()
        
        # Setup
        self.setup_ui()
        self.analyzer_thread = None
        self.analysis_results = None
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main window settings
        self.setWindowTitle("Project Analyzer")
        self.setMinimumSize(800, 600)
        
        # Set dark theme stylesheet
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2b2929;
                color: #d1cccc;
            }
            QTabWidget::pane {
                border: 1px solid rgba(82, 82, 82, 0.3);
                border-radius: 4px;
                padding: 5px;
            }
            QTabBar::tab {
                background-color: #1a1a1a;
                color: #d1cccc;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background-color: #fb923c;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #262626;
                border-bottom: 2px solid #fb923c;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a4a4a;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #fb923c;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QMessageBox {
                background-color: #2b2929;
                color: #d1cccc;
            }
            QMessageBox QPushButton {
                background-color: #1a1a1a;
                color: #d1cccc;
                border: 1px solid #fb923c;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #fb923c;
                color: white;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create splitter for left and right panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Input paths and settings
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)
        
        # Path selection
        path_group = QGroupBox("Analysis Paths")
        path_group.setStyleSheet("""
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
        path_layout = QVBoxLayout(path_group)
        
        # Path selector widget
        self.path_selector = PathSelector()
        path_layout.addWidget(self.path_selector)
        
        # Add path group to left layout
        left_layout.addWidget(path_group)
        
        # Settings panel
        self.settings_panel = SettingsPanel()
        left_layout.addWidget(self.settings_panel)
        
        # Start analysis button
        self.start_button = QPushButton("Start Analysis")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #fb923c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ea580c;
            }
            QPushButton:pressed {
                background-color: #c2410c;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #a3a3a3;
            }
        """)
        self.start_button.clicked.connect(self.start_analysis)
        
        left_layout.addWidget(self.start_button)
        
        # Add left panel to splitter
        splitter.addWidget(left_panel)
        
        # Right panel - Results view
        right_panel = QTabWidget()
        right_panel.setDocumentMode(True)
        
        # Progress tab
        progress_tab = QWidget()
        progress_layout = QVBoxLayout(progress_tab)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a1a;
                color: white;
                border: none;
                border-radius: 4px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #fb923c;
                border-radius: 4px;
            }
        """)
        
        self.status_label = QLabel("Ready to analyze.")
        self.status_label.setStyleSheet("color: #d1cccc; margin-top: 10px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #d1cccc;
                border: 1px solid rgba(82, 82, 82, 0.5);
                border-radius: 4px;
                font-family: monospace;
            }
        """)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(QLabel("Log:"))
        progress_layout.addWidget(self.log_output)
        
        # Summary tab (will be populated after analysis)
        self.summary_tab = QScrollArea()
        self.summary_tab.setWidgetResizable(True)
        self.summary_tab.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.summary_tab.setStyleSheet("""
            QScrollArea {
                border: none;
            }
        """)
        
        summary_content = QWidget()
        self.summary_layout = QVBoxLayout(summary_content)
        self.summary_layout.setAlignment(Qt.AlignTop)
        self.summary_tab.setWidget(summary_content)
        
        # Projects tab (will be populated after analysis)
        self.projects_tab = QScrollArea()
        self.projects_tab.setWidgetResizable(True)
        self.projects_tab.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.projects_tab.setStyleSheet(self.summary_tab.styleSheet())
        
        projects_content = QWidget()
        self.projects_layout = QVBoxLayout(projects_content)
        self.projects_layout.setAlignment(Qt.AlignTop)
        self.projects_tab.setWidget(projects_content)
        
        # Microservices tab (will be populated after analysis)
        self.microservices_tab = QScrollArea()
        self.microservices_tab.setWidgetResizable(True)
        self.microservices_tab.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.microservices_tab.setStyleSheet(self.summary_tab.styleSheet())
        
        microservices_content = QWidget()
        self.microservices_layout = QVBoxLayout(microservices_content)
        self.microservices_layout.setAlignment(Qt.AlignTop)
        self.microservices_tab.setWidget(microservices_content)
        
        # Add tabs to the tab widget
        right_panel.addTab(progress_tab, "Progress")
        right_panel.addTab(self.summary_tab, "Summary")
        right_panel.addTab(self.projects_tab, "Projects")
        right_panel.addTab(self.microservices_tab, "Microservices")
        
        # Add right panel to splitter
        splitter.addWidget(right_panel)
        
        # Set default splitter sizes (1:2 ratio)
        splitter.setSizes([300, 500])
        
        # Add splitter to main layout
        main_layout.addWidget(splitter)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Create status bar
        self.statusBar().setStyleSheet("color: #d1cccc; background-color: #1a1a1a;")
        self.statusBar().showMessage("Ready")
        
        # Set up menu bar
        self.setup_menu()
    
    def setup_menu(self):
        """Set up the menu bar."""
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #1a1a1a;
                color: #d1cccc;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
            }
            QMenuBar::item:selected {
                background-color: #fb923c;
                color: white;
            }
            QMenu {
                background-color: #1a1a1a;
                color: #d1cccc;
                border: 1px solid #fb923c;
            }
            QMenu::item {
                padding: 6px 20px 6px 10px;
            }
            QMenu::item:selected {
                background-color: #fb923c;
                color: white;
            }
        """)
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # Save results action
        save_action = QAction("Save Results", self)
        save_action.triggered.connect(self.save_results)
        file_menu.addAction(save_action)
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Project Analyzer",
            """<h3>Project Analyzer</h3>
            <p>A tool to analyze project structures, detect frameworks, and identify microservice architectures.</p>
            <p>Version 1.0</p>"""
        )
    
    def start_analysis(self):
        """Start the analysis process."""
        # Get paths
        paths = self.path_selector.get_paths()
        if not paths:
            QMessageBox.warning(
                self,
                "No Paths Selected",
                "Please select at least one directory to analyze."
            )
            return
        
        # Get settings
        settings = self.settings_panel.get_settings()
        output_dir = settings['output_dir']
        
        # Create output directory if it doesn't exist
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Could not create output directory: {str(e)}"
            )
            return
        
        # Update UI for analysis start
        self.start_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting analysis...")
        self.log_output.clear()
        self.add_log_message("Analysis started.")
        self.add_log_message(f"Paths to analyze: {', '.join(paths)}")
        self.add_log_message(f"Output directory: {output_dir}")
        
        # Start analyzer thread
        self.analyzer_thread = AnalyzerThread(paths, output_dir, settings)
        self.analyzer_thread.progress_update.connect(self.update_progress)
        self.analyzer_thread.analysis_complete.connect(self.analysis_completed)
        self.analyzer_thread.analysis_error.connect(self.analysis_error)
        self.analyzer_thread.start()
    
    def update_progress(self, progress, message):
        """Update progress bar and status message."""
        self.progress_bar.setValue(int(progress * 100))
        self.status_label.setText(message)
        self.add_log_message(message)
    
    def add_log_message(self, message):
        """Add message to log output."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
    
    def analysis_completed(self, results):
        """Handle analysis completion."""
        self.analysis_results = results
        
        # Update UI
        self.start_button.setEnabled(True)
        self.status_label.setText("Analysis completed successfully.")
        self.add_log_message("Analysis completed successfully.")
        self.add_log_message(f"Found {len(results['projects'])} projects.")
        self.add_log_message(f"Found {len(results['microservices'])} microservices.")
        self.add_log_message(f"Analysis took {results['analysis_time']:.2f} seconds.")
        
        # Show summary tab
        self.display_summary_results()
        self.display_projects_results()
        self.display_microservices_results()
        
        # Switch to summary tab
        tabw = self.findChild(QTabWidget)
        if tabw:
            tabw.setCurrentIndex(1)  # Summary tab
    
    def analysis_error(self, error_message):
        """Handle analysis error."""
        self.start_button.setEnabled(True)
        self.status_label.setText("Analysis failed.")
        self.add_log_message(f"ERROR: {error_message}")
        
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"An error occurred during analysis:\n\n{error_message}"
        )
    
    def display_summary_results(self):
        """Display summary results in the summary tab."""
        # Clear previous content
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.analysis_results:
            return
        
        # Add summary header
        header = QLabel("Analysis Summary")
        header.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        self.summary_layout.addWidget(header)
        
        # Add basic info
        stats = self.analysis_results.get('stats', {})
        
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 26, 26, 0.7);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        info_layout = QGridLayout(info_frame)
        
        # Basic stats
        info_layout.addWidget(QLabel("Total Projects:"), 0, 0)
        info_layout.addWidget(QLabel(f"<b>{stats.get('total_projects', 0)}</b>"), 0, 1)
        
        info_layout.addWidget(QLabel("Microservices:"), 1, 0)
        info_layout.addWidget(QLabel(f"<b>{stats.get('microservices_count', 0)}</b>"), 1, 1)
        
        info_layout.addWidget(QLabel("Analysis Time:"), 2, 0)
        info_layout.addWidget(QLabel(f"<b>{self.analysis_results.get('analysis_time', 0):.2f} seconds</b>"), 2, 1)
        
        self.summary_layout.addWidget(info_frame)
        
        # Project types chart
        if stats.get('project_types'):
            self.summary_layout.addWidget(QLabel("Project Types:"))
            self._add_bar_chart(self.summary_layout, stats['project_types'], "#fb923c")
        
        # Languages chart
        if stats.get('languages'):
            self.summary_layout.addWidget(QLabel("Languages:"))
            self._add_bar_chart(self.summary_layout, stats['languages'], "#3b82f6")
        
        # Frameworks chart
        if stats.get('frameworks'):
            self.summary_layout.addWidget(QLabel("Top Frameworks:"))
            # Limit to top 10 frameworks
            top_frameworks = dict(sorted(stats['frameworks'].items(), key=lambda x: x[1], reverse=True)[:10])
            self._add_bar_chart(self.summary_layout, top_frameworks, "#10b981")
        
        # Confidence levels chart
        if stats.get('confidence_levels'):
            self.summary_layout.addWidget(QLabel("Confidence Levels:"))
            self._add_bar_chart(self.summary_layout, stats['confidence_levels'], "#a855f7")
        
        # Add link to reports
        if self.analysis_results.get('reports'):
            reports_frame = QFrame()
            reports_frame.setStyleSheet(info_frame.styleSheet())
            reports_layout = QVBoxLayout(reports_frame)
            
            reports_layout.addWidget(QLabel("<b>Generated Reports:</b>"))
            
            # Add links to summary reports
            if 'summary' in self.analysis_results['reports']:
                for report in self.analysis_results['reports']['summary']:
                    report_link = QPushButton(f"Open {report['name']} Report")
                    report_link.setStyleSheet("""
                        QPushButton {
                            background-color: transparent;
                            color: #fb923c;
                            border: none;
                            text-align: left;
                            padding: 5px;
                        }
                        QPushButton:hover {
                            text-decoration: underline;
                        }
                    """)
                    report_link.clicked.connect(lambda _, path=report['path']: self._open_report(path))
                    reports_layout.addWidget(report_link)
            
            # Add link to microservice report if available
            if self.analysis_results.get('microservices'):
                report_link = QPushButton("Open Microservice Architecture Report")
                report_link.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #fb923c;
                        border: none;
                        text-align: left;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        text-decoration: underline;
                    }
                """)
                output_dir = self.settings_panel.get_settings()['output_dir']
                report_path = os.path.join(output_dir, 'microservice_report.html')
                report_link.clicked.connect(lambda _, path=report_path: self._open_report(path))
                reports_layout.addWidget(report_link)
            
            self.summary_layout.addWidget(reports_frame)
        
        # Add spacer
        self.summary_layout.addStretch()
    
    def display_projects_results(self):
        """Display project results in the projects tab."""
        # Clear previous content
        while self.projects_layout.count():
            item = self.projects_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.analysis_results or not self.analysis_results.get('projects'):
            return
        
        # Add projects header
        header = QLabel("Analyzed Projects")
        header.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        self.projects_layout.addWidget(header)
        
        # Add project cards
        for project in sorted(self.analysis_results['projects'], key=lambda x: x['name']):
            self._add_project_card(project)
        
        # Add spacer
        self.projects_layout.addStretch()
    
    def display_microservices_results(self):
        """Display microservice results in the microservices tab."""
        # Clear previous content
        while self.microservices_layout.count():
            item = self.microservices_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.analysis_results or not self.analysis_results.get('microservices'):
            # No microservices found
            label = QLabel("No microservices detected in the analyzed projects.")
            label.setAlignment(Qt.AlignCenter)
            self.microservices_layout.addWidget(label)
            return
        
        # Add microservices header
        header = QLabel("Detected Microservices")
        header.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        self.microservices_layout.addWidget(header)
        
        # Add microservice cards
        for ms in sorted(self.analysis_results['microservices'], key=lambda x: x['name']):
            self._add_microservice_card(ms)
        
        # Add relationships section if available
        if self.analysis_results.get('relationships'):
            rel_header = QLabel("Service Relationships")
            rel_header.setStyleSheet("color: white; font-size: 18px; font-weight: bold; margin-top: 20px;")
            self.microservices_layout.addWidget(rel_header)
            
            # Add relationship cards
            for rel in self.analysis_results['relationships']:
                self._add_relationship_card(rel)
        
        # Add spacer
        self.microservices_layout.addStretch()
    
    def _add_project_card(self, project):
        """Add a project card to the projects layout."""
        # Create card frame
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 26, 26, 0.7);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
        """)
        card_layout = QVBoxLayout(card)
        
        # Project header (name and type)
        header_layout = QHBoxLayout()
        project_name = QLabel(f"<b>{project['name']}</b>")
        project_name.setStyleSheet("color: white; font-size: 16px;")
        
        project_type = QLabel(project.get('project_type', 'unknown'))
        project_type.setStyleSheet("""
            background-color: #fb923c;
            color: white;
            border-radius: 4px;
            padding: 3px 8px;
        """)
        
        header_layout.addWidget(project_name)
        header_layout.addStretch()
        header_layout.addWidget(project_type)
        
        card_layout.addLayout(header_layout)
        
        # Project details
        details_layout = QGridLayout()
        details_layout.setColumnStretch(1, 1)
        
        # Path
        details_layout.addWidget(QLabel("Path:"), 0, 0)
        path_label = QLabel(f"<code>{project['path']}</code>")
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        details_layout.addWidget(path_label, 0, 1)
        
        # Language
        details_layout.addWidget(QLabel("Language:"), 1, 0)
        details_layout.addWidget(QLabel(project.get('primary_language', 'Unknown')), 1, 1)
        
        # Confidence
        details_layout.addWidget(QLabel("Confidence:"), 2, 0)
        confidence_text = project.get('confidence_text', 'Unknown')
        confidence_pct = f"{project.get('confidence', 0) * 100:.0f}%"
        confidence_label = QLabel(f"{confidence_text} ({confidence_pct})")
        details_layout.addWidget(confidence_label, 2, 1)
        
        # Files
        details_layout.addWidget(QLabel("Files:"), 3, 0)
        details_layout.addWidget(QLabel(f"{project.get('file_count', 0)}"), 3, 1)
        
        card_layout.addLayout(details_layout)
        
        # Top frameworks section if available
        if project.get('framework_scores'):
            # Get top 5 frameworks
            top_frameworks = sorted(
                project['framework_scores'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            if top_frameworks:
                frameworks_label = QLabel("Top Frameworks:")
                frameworks_label.setStyleSheet("margin-top: 10px;")
                card_layout.addWidget(frameworks_label)
                
                for framework, score in top_frameworks:
                    if score > 0:
                        fw_layout = QHBoxLayout()
                        fw_layout.addWidget(QLabel(framework))
                        fw_layout.addStretch()
                        fw_layout.addWidget(QLabel(f"{score:.2f}"))
                        card_layout.addLayout(fw_layout)
        
        # View report button
        view_btn = QPushButton("View Detailed Report")
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #fb923c;
                border: 1px solid #fb923c;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #fb923c;
                color: white;
            }
        """)
        
        # Find report path
        report_path = None
        output_dir = self.settings_panel.get_settings()['output_dir']
        potential_path = os.path.join(output_dir, f"{project['name'].replace(' ', '_')}_report.html")
        if os.path.exists(potential_path):
            report_path = potential_path
        
        if report_path:
            view_btn.clicked.connect(lambda _, path=report_path: self._open_report(path))
        else:
            view_btn.setEnabled(False)
            view_btn.setToolTip("Report not found")
        
        card_layout.addWidget(view_btn)
        
        # Add card to layout
        self.projects_layout.addWidget(card)
    


    def _add_microservice_card(self, microservice):
        """Add a microservice card to the microservices layout."""
        # Create card frame
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 26, 26, 0.7);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
        """)
        card_layout = QVBoxLayout(card)
        
        # Microservice header (name)
        header_layout = QHBoxLayout()
        ms_name = QLabel(f"<b>{microservice['name']}</b>")
        ms_name.setStyleSheet("color: white; font-size: 16px;")
        
        ms_prob = QLabel(f"{microservice.get('microservice_probability', 0) * 100:.0f}% confidence")
        ms_prob.setStyleSheet("""
            background-color: #3b82f6;
            color: white;
            border-radius: 4px;
            padding: 3px 8px;
        """)
        
        header_layout.addWidget(ms_name)
        header_layout.addStretch()
        header_layout.addWidget(ms_prob)
        
        card_layout.addLayout(header_layout)
        
        # Microservice details
        details_layout = QGridLayout()
        details_layout.setColumnStretch(1, 1)
        
        # Path
        details_layout.addWidget(QLabel("Path:"), 0, 0)
        path_label = QLabel(f"<code>{microservice['path']}</code>")
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        details_layout.addWidget(path_label, 0, 1)
        
        # Communication style
        details_layout.addWidget(QLabel("Communication:"), 1, 0)
        details_layout.addWidget(QLabel(microservice.get('primary_communication', 'Unknown')), 1, 1)
        
        # Endpoints count
        endpoint_count = len(microservice.get('service_endpoints', []))
        details_layout.addWidget(QLabel("Endpoints:"), 2, 0)
        details_layout.addWidget(QLabel(f"{endpoint_count}"), 2, 1)
        
        # Service calls count
        call_count = len(microservice.get('service_calls', []))
        details_layout.addWidget(QLabel("Service Calls:"), 3, 0)
        details_layout.addWidget(QLabel(f"{call_count}"), 3, 1)
        
        card_layout.addLayout(details_layout)
        
        # Add microservice indicators if available
        if microservice.get('microservice_scores'):
            indicators_label = QLabel("Microservice Indicators:")
            indicators_label.setStyleSheet("margin-top: 10px;")
            card_layout.addWidget(indicators_label)
            
            # Get top indicators
            top_indicators = sorted(
                microservice['microservice_scores'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            for indicator, score in top_indicators:
                ind_layout = QHBoxLayout()
                ind_layout.addWidget(QLabel(indicator))
                ind_layout.addStretch()
                ind_layout.addWidget(QLabel(f"{score:.1f}"))
                card_layout.addLayout(ind_layout)
        
        # View report button
        view_btn = QPushButton("View Detailed Report")
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #fb923c;
                border: 1px solid #fb923c;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #fb923c;
                color: white;
            }
        """)
        
        # Microservice report is combined in the main report
        output_dir = self.settings_panel.get_settings()['output_dir']
        report_path = os.path.join(output_dir, "microservice_report.html")
        
        if os.path.exists(report_path):
            view_btn.clicked.connect(lambda _, path=report_path: self._open_report(path))
        else:
            view_btn.setEnabled(False)
            view_btn.setToolTip("Report not found")
        
        card_layout.addWidget(view_btn)
        
        # Add card to layout
        self.microservices_layout.addWidget(card)
    
    def _add_relationship_card(self, relationship):
        """Add a relationship card to the microservices layout."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 26, 26, 0.5);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
            }
        """)
        card_layout = QHBoxLayout(card)
        
        # Source
        source_label = QLabel(relationship['source'])
        source_label.setStyleSheet("""
            background-color: #3b82f6;
            color: white;
            border-radius: 4px;
            padding: 3px 8px;
        """)
        
        # Arrow
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("color: #d1cccc; font-weight: bold; padding: 0 10px;")
        
        # Target
        target_label = QLabel(relationship['target'])
        target_label.setStyleSheet("""
            background-color: #10b981;
            color: white;
            border-radius: 4px;
            padding: 3px 8px;
        """)
        
        # Type
        type_label = QLabel(f"({relationship['type']})")
        type_label.setStyleSheet("color: #d1cccc; margin-left: 10px;")
        
        # File reference
        file_label = QLabel(relationship.get('file', ''))
        file_label.setStyleSheet("color: #a3a3a3; font-size: smaller;")
        
        # Add to layout
        card_layout.addWidget(source_label)
        card_layout.addWidget(arrow_label)
        card_layout.addWidget(target_label)
        card_layout.addWidget(type_label)
        card_layout.addStretch()
        card_layout.addWidget(file_label)
        
        # Add card to layout
        self.microservices_layout.addWidget(card)
    
    def _add_bar_chart(self, layout, data, color):
        """Add a simple bar chart to the layout."""
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 26, 26, 0.7);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
            }
        """)
        chart_layout = QVBoxLayout(chart_frame)
        
        # Find max value for scaling
        max_value = max(data.values()) if data else 1
        
        # Create bars for each item
        for key, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
            item_layout = QHBoxLayout()
            
            # Label
            label = QLabel(key)
            label.setMinimumWidth(100)
            
            # Bar
            bar = QFrame()
            bar.setStyleSheet(f"""
                background-color: {color};
                border-radius: 4px;
                min-height: 20px;
            """)
            
            # Calculate width percentage
            width_percent = (value / max_value) * 100
            
            # Value label
            value_label = QLabel(str(value))
            value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            value_label.setMinimumWidth(50)
            
            item_layout.addWidget(label)
            item_layout.addWidget(bar, int(width_percent))
            item_layout.addWidget(value_label)
            
            chart_layout.addLayout(item_layout)
        
        layout.addWidget(chart_frame)
    
    def _open_report(self, path):
        """Open a report file in the default browser."""
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The report file was not found:\n{path}"
            )
    
    def save_results(self):
        """Save analysis results to a JSON file."""
        if not self.analysis_results:
            QMessageBox.warning(
                self,
                "No Results",
                "No analysis results to save."
            )
            return
        
        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            os.path.join(self.settings_panel.get_settings()['output_dir'], "analysis_results.json"),
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            # Prepare results for saving (remove items that can't be serialized)
            save_data = {
                'stats': self.analysis_results.get('stats', {}),
                'analysis_time': self.analysis_results.get('analysis_time', 0),
                'paths_analyzed': self.analysis_results.get('paths_analyzed', []),
                'projects_count': len(self.analysis_results.get('projects', [])),
                'microservices_count': len(self.analysis_results.get('microservices', [])),
                'reports': self.analysis_results.get('reports', {})
            }
            
            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2)
                
            QMessageBox.information(
                self,
                "Save Successful",
                f"Results saved to:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Error saving results:\n{str(e)}"
            )
















