#!/usr/bin/env python3
"""
Project Analyzer - GUI Application
----------------------------------
A comprehensive tool for analyzing project structures, detecting frameworks,
and identifying microservice architectures with a PySide6 GUI.
"""

import sys
import os
from pathlib import Path
import logging
import argparse

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

# Import our GUI classes
from gui.main_window import ProjectAnalyzerGUI
from gui.path_selector import PathSelector
from gui.settings_panel import SettingsPanel
from gui.analyzer_thread import AnalyzerThread
from gui.chart_widgets import BarChartWidget, DonutChartWidget

# Import analyzer modules
from project_analyzer import ProjectAnalyzer
from microservice_detector import MicroserviceDetector

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Project Analyzer - A tool for analyzing project structures, frameworks, and microservices',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--path',
        help='Initial path to analyze'
    )
    
    parser.add_argument(
        '--output',
        help='Custom output directory for reports'
    )
    
    return parser.parse_args()

def setup_logging(debug=False):
    """Set up logging configuration."""
    log_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('project_analyzer.log')
        ]
    )
    
    # Create logger
    logger = logging.getLogger("ProjectAnalyzer")
    logger.setLevel(log_level)
    
    return logger

def setup_app_style():
    """Set up application style."""
    return """
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
        QMenu {
            background-color: #1a1a1a;
            color: #d1cccc;
            border: 1px solid #fb923c;
            border-radius: 4px;
        }
        QMenu::item {
            padding: 6px 20px;
        }
        QMenu::item:selected {
            background-color: #fb923c;
            color: white;
        }
        QToolTip {
            background-color: #1a1a1a;
            color: #d1cccc;
            border: 1px solid #fb923c;
            padding: 5px;
        }
    """

def main():
    """Main function to run the application."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set up logging
    logger = setup_logging(args.debug)
    logger.info("Starting Project Analyzer GUI")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Project Analyzer")
    app.setOrganizationName("Project Analyzer")
    app.setApplicationVersion("1.0.0")
    
    # Set application style
    app.setStyle("Fusion")
    app.setStyleSheet(setup_app_style())
    
    # Create main window with initial arguments if provided
    window = ProjectAnalyzerGUI()
    
    # Set initial path if provided
    if args.path:
        if os.path.isdir(args.path):
            window.path_selector.path_widgets[0]['input'].setText(args.path)
            window.path_selector.paths[0] = args.path
            logger.info(f"Setting initial path to: {args.path}")
        else:
            logger.warning(f"Initial path not found: {args.path}")
    
    # Set output directory if provided
    if args.output:
        window.settings_panel.output_path.setText(args.output)
        logger.info(f"Setting output directory to: {args.output}")
    
    # Show the window
    window.show()
    logger.info("GUI application started")
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()