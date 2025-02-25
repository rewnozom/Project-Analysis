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
from PySide6.QtCore import Qt, QThread, Signal, Slot, QSize, QTimer, QUrl
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QAction, QDesktopServices

# Import our project analyzer modules
from project_analyzer import ProjectAnalyzer
from microservice_detector import MicroserviceDetector

class PathSelector(QWidget):
    """
    Custom widget for dynamic path selection with add/remove functionality.
    """
    pathAdded = Signal()
    pathRemoved = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.paths = []
        self.path_widgets = []
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        
        # Add first path row
        self.add_path_row()
        
        # Button container for action buttons
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        # Add path button
        self.add_btn = QPushButton("Add Path")
        self.add_btn.setIcon(QIcon.fromTheme("list-add"))
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2929;
                color: #fb923c;
                border: 1px solid #fb923c;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #3a3939;
                border: 1px solid #ea580c;
            }
            QPushButton:pressed {
                background-color: #ea580c;
                color: white;
            }
        """)
        self.add_btn.clicked.connect(self.add_path_row)
        
        # Add subdirectories button
        self.add_subdirs_btn = QPushButton("Add Subdirectories")
        self.add_subdirs_btn.setIcon(QIcon.fromTheme("folder-multiple"))
        self.add_subdirs_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2929;
                color: #fb923c;
                border: 1px solid #fb923c;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #3a3939;
                border: 1px solid #ea580c;
            }
            QPushButton:pressed {
                background-color: #ea580c;
                color: white;
            }
        """)
        self.add_subdirs_btn.clicked.connect(self.add_subdirectories)
        
        # Add buttons to layout
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.add_subdirs_btn)
        button_layout.addStretch()
        
        self.layout.addWidget(button_container)
        self.layout.addStretch()
    
    def add_path_row(self):
        """Add a new path row."""
        index = len(self.path_widgets)
        
        # Create row widget
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        # Path number label
        label = QLabel(f"Path {index + 1}:")
        label.setStyleSheet("color: #d1cccc;")
        
        # Path input
        path_input = QLineEdit()
        path_input.setPlaceholderText("Select a directory to analyze...")
        path_input.setStyleSheet("""
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
        
        # Browse button
        browse_btn = QToolButton()
        browse_btn.setText("...")
        browse_btn.setStyleSheet("""
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
        
        # Delete button (hidden for first row)
        delete_btn = QToolButton()
        delete_btn.setIcon(QIcon.fromTheme("list-remove"))
        delete_btn.setStyleSheet("""
            QToolButton {
                background-color: #1a1a1a;
                color: #fb923c;
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
        
        if index == 0:
            delete_btn.setVisible(False)
        
        # Add widgets to layout
        row_layout.addWidget(label)
        row_layout.addWidget(path_input, 1)  # Give stretch factor
        row_layout.addWidget(browse_btn)
        row_layout.addWidget(delete_btn)
        
        # Connect signals
        browse_btn.clicked.connect(lambda: self.browse_path(index))
        delete_btn.clicked.connect(lambda: self.remove_path_row(index))
        
        # Add to main layout
        self.layout.insertWidget(index, row_widget)
        
        # Store widget and path
        self.path_widgets.append({
            'widget': row_widget,
            'label': label,
            'input': path_input,
            'browse': browse_btn,
            'delete': delete_btn
        })
        self.paths.append("")
        
        self.pathAdded.emit()
        
        return path_input
    
    def browse_path(self, index):
        """Open directory dialog for path selection."""
        if index < 0 or index >= len(self.path_widgets):
            return
        
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory to Analyze",
            os.path.expanduser("~")
        )
        
        if directory:
            self.paths[index] = directory
            self.path_widgets[index]['input'].setText(directory)
    
    def add_subdirectories(self):
        """Add all subdirectories of the selected path."""
        # Use first path as the parent directory
        if not self.paths or not self.paths[0]:
            QMessageBox.warning(
                self,
                "No Parent Directory",
                "Please select a parent directory in the first path field."
            )
            return
        
        parent_dir = self.paths[0]
        if not os.path.isdir(parent_dir):
            QMessageBox.warning(
                self,
                "Invalid Directory",
                f"The selected path '{parent_dir}' is not a valid directory."
            )
            return
        
        # Get all immediate subdirectories
        try:
            subdirs = [os.path.join(parent_dir, d) for d in os.listdir(parent_dir) 
                      if os.path.isdir(os.path.join(parent_dir, d))]
            
            if not subdirs:
                QMessageBox.information(
                    self,
                    "No Subdirectories",
                    f"No subdirectories found in '{parent_dir}'."
                )
                return
            
            # Add each subdirectory
            for subdir in subdirs:
                # Skip if already in paths
                if subdir in self.paths:
                    continue
                
                # Add new path row and set value
                path_input = self.add_path_row()
                path_input.setText(subdir)
                
                # Update the corresponding path in self.paths
                self.paths[-1] = subdir
            
            QMessageBox.information(
                self,
                "Subdirectories Added",
                f"Added {len(subdirs)} subdirectories from '{parent_dir}'."
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to add subdirectories: {str(e)}"
            )
    
    def remove_path_row(self, index):
        """Remove a path row."""
        if index < 0 or index >= len(self.path_widgets) or index == 0:
            return  # Don't remove the first row
        
        # Remove widget and path
        widget_data = self.path_widgets.pop(index)
        self.paths.pop(index)
        
        # Remove widget from layout and delete it
        self.layout.removeWidget(widget_data['widget'])
        widget_data['widget'].deleteLater()
        
        # Update remaining labels
        self.update_labels()
        
        self.pathRemoved.emit(index)
    
    def update_labels(self):
        """Update path labels after removing a row."""
        for i, widget_data in enumerate(self.path_widgets):
            widget_data['label'].setText(f"Path {i + 1}:")
    
    def get_paths(self):
        """Get the list of valid paths."""
        return [p for p in self.paths if p and os.path.isdir(p)]


class AnalyzerThread(QThread):
    """
    Thread for running the project analysis in the background.
    """
    progress_update = Signal(float, str)
    analysis_complete = Signal(dict)
    analysis_error = Signal(str)
    
    def __init__(self, paths, output_dir, options):
        """
        Initialize the analyzer thread.
        
        Args:
            paths: List of paths to analyze
            output_dir: Directory to save reports
            options: Analysis options
        """
        super().__init__()
        self.paths = paths
        self.output_dir = output_dir
        self.options = options
    
    def run(self):
        """Run the analysis."""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Initialize results
            all_results = {
                'projects': [],
                'microservices': [],
                'relationships': [],
                'reports': {},
                'stats': {},
                'paths_analyzed': self.paths,
                'analysis_time': None
            }
            
            start_time = time.time()
            
            # Process each path
            for i, path in enumerate(self.paths):
                path_progress_base = i / len(self.paths)
                path_progress_step = 1 / len(self.paths)
                
                self.progress_update.emit(path_progress_base, f"Analyzing {os.path.basename(path)}")
                
                # Initialize analyzer for this path
                analyzer = ProjectAnalyzer(
                    root_dir=path,
                    output_dir=self.output_dir,
                    ignore_patterns=self.options.get('ignore_patterns', []),
                    max_workers=self.options.get('max_workers', 4),
                    max_depth=self.options.get('max_depth', 3),
                    verbose=self.options.get('verbose', False)
                )
                
                # Run scan with progress callback
                def progress_callback(progress, message):
                    # Scale progress to the portion for this path
                    overall_progress = path_progress_base + (progress * path_progress_step)
                    self.progress_update.emit(overall_progress, message)
                
                # Scan projects
                projects = analyzer.scan_projects(callback=progress_callback)
                
                # Generate reports
                self.progress_update.emit(
                    path_progress_base + 0.8 * path_progress_step, 
                    "Generating reports"
                )
                reports = analyzer.generate_reports()
                
                # Run microservice detection if enabled
                microservices = []
                relationships = []
                if self.options.get('detect_microservices', False) and projects:
                    self.progress_update.emit(
                        path_progress_base + 0.9 * path_progress_step,
                        "Detecting microservices"
                    )
                    microservice_detector = MicroserviceDetector(analyzer)
                    ms_results = microservice_detector.detect_microservices()
                    
                    microservices = ms_results.get('microservices', [])
                    relationships = ms_results.get('relationships', [])
                
                # Add results from this path
                all_results['projects'].extend(projects)
                all_results['microservices'].extend(microservices)
                all_results['relationships'].extend(relationships)
                
                # Combine report paths
                for report_type, report_path in reports.items():
                    if report_type not in all_results['reports']:
                        all_results['reports'][report_type] = []
                    
                    if isinstance(report_path, dict):
                        # Handle nested report structures
                        for name, path in report_path.items():
                            all_results['reports'][report_type].append({
                                'name': f"{os.path.basename(path)}_{name}",
                                'path': path
                            })
                    else:
                        all_results['reports'][report_type].append({
                            'name': os.path.basename(path),
                            'path': report_path
                        })
            
            # Calculate overall statistics
            all_results['stats'] = self._calculate_overall_stats(all_results['projects'])
            all_results['analysis_time'] = time.time() - start_time
            
            # Complete
            self.progress_update.emit(1.0, "Analysis complete")
            self.analysis_complete.emit(all_results)
            
        except Exception as e:
            self.analysis_error.emit(str(e))
    
    def _calculate_overall_stats(self, projects):
        """
        Calculate overall statistics for all projects.
        
        Args:
            projects: List of analyzed projects
            
        Returns:
            dict: Overall statistics
        """
        from collections import Counter
        
        # Skip if no projects
        if not projects:
            return {}
        
        # Set up counters
        project_types = Counter()
        languages = Counter()
        frameworks = Counter()
        confidence_levels = Counter()
        microservices_count = 0
        
        # Process each project
        for project in projects:
            # Count project type and language
            project_types[project.get('project_type', 'unknown')] += 1
            languages[project.get('primary_language', 'unknown')] += 1
            
            # Count confidence level
            confidence_levels[project.get('confidence_text', 'Unknown')] += 1
            
            # Count frameworks
            for framework, score in project.get('framework_scores', {}).items():
                if score > 1.0:  # Threshold for counting
                    frameworks[framework] += 1
            
            # Count microservices
            if project.get('is_microservice', False):
                microservices_count += 1
        
        # Return stats dictionary
        return {
            'total_projects': len(projects),
            'project_types': dict(project_types),
            'languages': dict(languages),
            'frameworks': dict(frameworks),
            'confidence_levels': dict(confidence_levels),
            'microservices_count': microservices_count
        }