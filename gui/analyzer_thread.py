








# analyzer_thread.py

import os
import time
from collections import Counter
from PySide6.QtCore import QThread, Signal

from project_analyzer import ProjectAnalyzer
from microservice_detector import MicroserviceDetector


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














