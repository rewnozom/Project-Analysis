

###############
##  Part 1   ##
###############

import os
import re
import json
import shutil
from pathlib import Path
import datetime
import markdown
import concurrent.futures
from collections import defaultdict, Counter
import fnmatch
import logging
from typing import Dict, List, Optional, Tuple, Set, Any, Union

class ProjectAnalyzerCore:
    """
    Core functionality for the project analyzer - splitting for better modularity.
    This handles the initialization and basic utility functions.
    """
    
    def __init__(self, 
                 root_dir: str = '.', 
                 output_dir: str = './reports', 
                 ignore_patterns: Optional[List[str]] = None,
                 max_workers: int = 4,
                 verbose: bool = False):
        """
        Initialize the project analyzer.
        
        Args:
            root_dir (str): Root directory to start scanning from
            output_dir (str): Directory to save reports to
            ignore_patterns (list): List of patterns to ignore (e.g. ['node_modules', 'venv'])
            max_workers (int): Maximum number of worker threads for parallel processing
            verbose (bool): Enable verbose logging
        """
        # Set up logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("ProjectAnalyzer")
        
        self.root_dir = os.path.abspath(root_dir)
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.verbose = verbose
        
        # Default ignore patterns - expanded and improved
        self.ignore_patterns = ignore_patterns or [
            # Version control
            '.git', '.github', '.svn', '.hg', '.bzr',
            
            # IDE and editor files
            '.vscode', '__pycache__', '.idea', '.vs',
            '.settings', '.project', '.classpath',
            
            # Virtual environments
            'venv', 'env', '.env', '.virtualenv', '.venv',
            'virtualenv', 'ENV', 'node_modules',
            
            # Build and distribution
            'dist', 'build', 'target', 'out', 'bin',
            '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dylib', '*.dll',
            '*.egg-info', '*.egg', '*.whl', '*.jar', '*.war',
            
            # Operating system files
            '.DS_Store', 'Thumbs.db', '.directory',
            
            # Common system directories that cause permission errors
            '.cache', '.config', '.azure', '.aws', '.android', 
            '.gradle', '.nuget', '.m2', '.npm', '.yarn',
            'AppData', 'Local Settings', 'Application Data',
            '.anaconda', '.brave_automation',
            'Temporary Internet Files', 'Temp', 'tmp',
            
            # Additional ignore patterns for large data directories
            'data', 'dataset', 'datasets', 'large_files',
            'logs', 'log', 'archive', 'bak', 'backup',
            
            # Media files
            '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp',
            '*.mp3', '*.mp4', '*.mov', '*.avi', '*.wmv',
            '*.zip', '*.tar', '*.gz', '*.bz2', '*.xz', '*.rar',
        ]
        
        # Framework patterns will be loaded from a separate module
        self.framework_patterns = {}
        
        # Will be populated with discovered projects
        self.projects = []
        self.summary = {}
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.logger.info(f"Initialized ProjectAnalyzer with root directory: {self.root_dir}")
        self.logger.info(f"Output directory set to: {self.output_dir}")
        self.logger.info(f"Using {self.max_workers} worker threads for parallel processing")
    
    def should_ignore(self, path: Union[str, Path]) -> bool:
        """
        Check if a path should be ignored based on ignore patterns.
        
        Args:
            path: Path to check (string or Path object)
            
        Returns:
            bool: True if the path should be ignored
        """
        path_str = str(path)
        
        # Check each ignore pattern
        for pattern in self.ignore_patterns:
            # First check if pattern is in the path directly
            if pattern in path_str:
                return True
            
            # Then use more sophisticated fnmatch for wildcard matching
            if fnmatch.fnmatch(os.path.basename(path_str), pattern):
                return True
            
            # Also check the full path against the pattern
            if fnmatch.fnmatch(path_str, pattern):
                return True
        
        # Check for hidden directories and files (starting with .)
        if os.path.basename(path_str).startswith('.'):
            return True
        
        # Check for binary files that shouldn't be processed
        if os.path.isfile(path_str):
            # Skip large files (> 10MB) to avoid performance issues
            try:
                if os.path.getsize(path_str) > 10 * 1024 * 1024:
                    self.logger.debug(f"Skipping large file: {path_str}")
                    return True
            except (OSError, PermissionError):
                # If we can't get the size, better to skip
                return True
        
        return False
    
    def load_framework_patterns(self, patterns: Dict[str, Any]) -> None:
        """
        Load framework detection patterns.
        
        Args:
            patterns: Dictionary of framework patterns
        """
        self.framework_patterns = patterns
        self.logger.info(f"Loaded {len(patterns)} framework patterns")
    
    def get_confidence_level(self, score: float) -> str:
        """
        Convert a numerical confidence score to a text representation.
        
        Args:
            score: Confidence score (0.0 to 1.0)
            
        Returns:
            str: Textual confidence level
        """
        if score >= 0.9:
            return "Very High"
        elif score >= 0.75:
            return "High"
        elif score >= 0.5:
            return "Medium"
        elif score >= 0.25:
            return "Low"
        else:
            return "Very Low"






###############
##  Part 2   ##
###############









class ProjectAnalyzerScanner:
    """
    Handles the scanning and analysis of projects.
    Inherits from ProjectAnalyzerCore.
    """
    
    def __init__(self, core):
        """
        Initialize the scanner with a reference to the core analyzer.
        
        Args:
            core: ProjectAnalyzerCore instance
        """
        self.core = core
        self.logger = core.logger
    
    def analyze_file_content(self, file_path: str) -> dict:
        """
        Analyze content of a file for patterns and key indicators.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            dict: Analysis results
        """
        # Skip binary and media files
        if file_path.endswith(('.jpg', '.png', '.gif', '.svg', '.ico', '.woff', '.ttf', '.eot',
                              '.mp3', '.mp4', '.avi', '.mov', '.pdf', '.zip', '.tar.gz', '.exe')):
            return {}
        
        results = {
            'has_main_function': False,
            'imports': [],
            'framework_indicators': defaultdict(int),
            'file_size': 0,  # Default to 0 
            'error': None,
        }
        
        # Get file size safely
        try:
            results['file_size'] = os.path.getsize(file_path)
            # Skip very large files
            if results['file_size'] > 5 * 1024 * 1024:  # 5MB limit
                self.logger.debug(f"Skipping large file for content analysis: {file_path} ({results['file_size'] / 1024 / 1024:.2f} MB)")
                results['error'] = "File too large for analysis"
                return results
        except (OSError, PermissionError) as e:
            results['error'] = f"Error getting file size: {str(e)}"
            return results
        
        try:
            # Check if we can access the file before trying to open it
            if not os.access(file_path, os.R_OK):
                results['error'] = "No read access"
                return results
                
            # Detect file encoding and read with appropriate method
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                try:
                    content = f.read()
                except Exception as e:
                    results['error'] = f"Error reading file content: {str(e)}"
                    return results
                
                # Check for main function in Python files
                if file_path.endswith('.py'):
                    if re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]', content):
                        results['has_main_function'] = True
                    
                    # Extract imports with improved regex
                    import_patterns = [
                        r'import\s+([\w\.]+)(?:\s+as\s+[\w\.]+)?',
                        r'from\s+([\w\.]+)\s+import\s+(?:[\w\., \*]+)'
                    ]
                    
                    for pattern in import_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            # Clean up match and add to imports
                            clean_match = match.strip()
                            if clean_match and clean_match not in results['imports']:
                                results['imports'].append(clean_match)
                
                # Check for framework indicators
                for framework, patterns in self.core.framework_patterns.items():
                    # Check content patterns for any file type
                    if 'content_patterns' in patterns:
                        for pattern in patterns['content_patterns']:
                            if pattern in content:
                                results['framework_indicators'][framework] += patterns.get('weight', 0.5)
                    
                    # Check imports for Python files
                    if 'imports' in patterns and file_path.endswith('.py'):
                        for imp in patterns['imports']:
                            if any(module == imp or module.startswith(f"{imp}.") for module in results['imports']):
                                results['framework_indicators'][framework] += patterns.get('weight', 0.5)
                
                # For package.json files, analyze dependencies with better error handling
                if os.path.basename(file_path) == 'package.json':
                    try:
                        package_data = json.loads(content)
                        dependencies = {}
                        # Combine all dependency types
                        for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                            if dep_type in package_data:
                                dependencies.update(package_data[dep_type])
                        
                        results['dependencies'] = dependencies
                        
                        # Check for specific packages
                        for framework, patterns in self.core.framework_patterns.items():
                            if 'package_dependencies' in patterns:
                                for dep in patterns['package_dependencies']:
                                    if dep in dependencies:
                                        results['framework_indicators'][framework] += patterns.get('weight', 0.5)
                    except json.JSONDecodeError:
                        results['error'] = "Invalid JSON in package.json"
        
        except Exception as e:
            # Log the error but don't fail the analysis
            results['error'] = f"Error analyzing file: {str(e)}"
            self.logger.debug(f"Error analyzing {file_path}: {str(e)}")
        
        return results
    
    def analyze_directory(self, directory: str) -> Optional[dict]:
        """
        Analyze a directory to determine if it's a project/module and what type it is.
        
        Args:
            directory: Directory path to analyze
            
        Returns:
            Optional[dict]: Project information or None if not a valid project
        """
        directory_path = Path(directory)
        
        if self.core.should_ignore(directory_path):
            self.logger.debug(f"Ignoring directory: {directory}")
            return None
            
        # Skip if we don't have read access
        try:
            if not os.access(directory, os.R_OK):
                self.logger.warning(f"Skipping {directory} (no read access)")
                return None
        except Exception as e:
            self.logger.warning(f"Skipping {directory} ({str(e)})")
            return None
        
        # Initialize project info with improved structure
        project_info = {
            'path': str(directory_path),
            'name': directory_path.name,
            'files': [],
            'key_files': [],
            'errors': [],
            'subdirectories': [],
            'framework_scores': defaultdict(float),
            'has_main_function': False,
            'imports': set(),
            'project_type': 'unknown',
            'confidence': 0,
            'confidence_factors': {},  # Store individual confidence factors
            'analysis_date': datetime.datetime.now().isoformat()
        }
        
        # Track files and statistics
        files_found = []
        file_count = 0
        py_file_count = 0
        js_file_count = 0
        ts_file_count = 0
        java_file_count = 0
        html_file_count = 0
        css_file_count = 0
        
        # Store file extensions for language analysis
        file_extensions = Counter()
        
        # First pass: collect file information
        try:
            for root, dirs, files in os.walk(str(directory_path)):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if not self.core.should_ignore(os.path.join(root, d))]
                
                rel_path = os.path.relpath(root, str(directory_path))
                if rel_path == '.':
                    rel_path = ''
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip ignored files
                    if self.core.should_ignore(file_path):
                        continue
                    
                    # Skip files we can't access
                    try:
                        if not os.access(file_path, os.R_OK):
                            continue
                    except Exception:
                        continue
                        
                    rel_file_path = os.path.join(rel_path, file) if rel_path else file
                    
                    # Get file extension and track
                    _, ext = os.path.splitext(file)
                    if ext:
                        file_extensions[ext.lower()] += 1
                    
                    # Count file types
                    file_count += 1
                    if file.endswith('.py'):
                        py_file_count += 1
                    elif file.endswith(('.js', '.jsx')):
                        js_file_count += 1
                    elif file.endswith(('.ts', '.tsx')):
                        ts_file_count += 1
                    elif file.endswith(('.java', '.kt', '.scala')):
                        java_file_count += 1
                    elif file.endswith(('.html', '.htm')):
                        html_file_count += 1
                    elif file.endswith(('.css', '.scss', '.sass')):
                        css_file_count += 1
                    
                    # Prepare file info
                    file_info = {
                        'name': file,
                        'path': rel_file_path,
                        'full_path': file_path,
                        'is_key_file': False,
                        'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    }
                    
                    # Check if this is a key file - more comprehensive check
                    if self._is_key_file(file, file_path):
                        file_info['is_key_file'] = True
                        project_info['key_files'].append(rel_file_path)
                    
                    # Check for framework specific files
                    for framework, patterns in self.core.framework_patterns.items():
                        if 'files' in patterns:
                            for pattern in patterns['files']:
                                if (fnmatch.fnmatch(file, pattern) or 
                                    pattern in file_path or 
                                    fnmatch.fnmatch(file_path, f"*{pattern}*")):
                                    project_info['framework_scores'][framework] += patterns.get('weight', 0.5)
                                    break
                    
                    # Analyze content of important files using multi-threading
                    # We'll use the executor later to run these in parallel
                    files_found.append(file_info)
            
            # Store file statistics
            project_info['file_count'] = file_count
            project_info['py_file_count'] = py_file_count
            project_info['js_file_count'] = js_file_count
            project_info['ts_file_count'] = ts_file_count
            project_info['java_file_count'] = java_file_count
            project_info['html_file_count'] = html_file_count
            project_info['css_file_count'] = css_file_count
            project_info['file_extensions'] = dict(file_extensions)
            
            # Parallel content analysis for important files
            important_files = [f for f in files_found if 
                             f['is_key_file'] or 
                             f['name'].endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.yml', '.yaml', 
                                                '.html', '.htm', '.css', '.java', '.kt', '.scala', '.xml'))]
            
            # Only process files if we have any
            if important_files:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.core.max_workers) as executor:
                    # Map the file paths to the analyze_file_content function
                    future_to_file = {
                        executor.submit(self.analyze_file_content, file_info['full_path']): file_info 
                        for file_info in important_files
                    }
                    
                    # Process results as they complete
                    for future in concurrent.futures.as_completed(future_to_file):
                        file_info = future_to_file[future]
                        try:
                            content_analysis = future.result()
                            file_info.update(content_analysis)
                            
                            if content_analysis.get('error'):
                                project_info['errors'].append({
                                    'file': file_info['path'],
                                    'error': content_analysis['error']
                                })
                            
                            if content_analysis.get('has_main_function', False):
                                project_info['has_main_function'] = True
                            
                            if 'imports' in content_analysis:
                                project_info['imports'].update(content_analysis['imports'])
                            
                            if 'framework_indicators' in content_analysis:
                                for framework, score in content_analysis['framework_indicators'].items():
                                    project_info['framework_scores'][framework] += score
                        except Exception as e:
                            self.logger.error(f"Error processing file {file_info['path']}: {str(e)}")
                            project_info['errors'].append({
                                'file': file_info['path'],
                                'error': str(e)
                            })
            
            # Save processed file information
            project_info['files'] = files_found
            
        except PermissionError as e:
            self.logger.error(f"Permission error accessing {directory}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error analyzing {directory}: {str(e)}")
            return None
        
        # Determine project type with improved confidence scoring
        if file_count == 0:
            return None  # Empty directory, not a project
        
        # Analyze and determine project details
        self._determine_project_details(project_info)
        
        return project_info
    
    def _is_key_file(self, file_name: str, file_path: str) -> bool:
        """
        Check if a file is a key project file.
        
        Args:
            file_name: Name of the file
            file_path: Full path to the file
            
        Returns:
            bool: True if it's a key file
        """
        # List of key file patterns expanded
        key_files = [
            # Python
            'main.py', 'app.py', 'run.py', 'server.py', 'setup.py', 'requirements.txt',
            'pyproject.toml', 'Pipfile', 'Pipfile.lock', 'pytest.ini', 'conftest.py',
            'manage.py', 'wsgi.py', 'asgi.py', 'settings.py', 'urls.py', 'models.py',
            'views.py', 'tox.ini', '__main__.py', 'config.py', 'utils.py',
            
            # JavaScript/TypeScript
            'package.json', 'package-lock.json', 'yarn.lock', 'tsconfig.json',
            'next.config.js', 'nuxt.config.js', 'angular.json', 'vue.config.js',
            'webpack.config.js', 'rollup.config.js', '.babelrc', '.eslintrc',
            'index.js', 'main.js', 'server.js', 'app.js', 'index.ts', 'main.ts',
            
            # Configuration
            '.env', '.env.example', '.gitignore', '.gitattributes', '.editorconfig',
            'README.md', 'LICENSE', 'CONTRIBUTING.md', 'CHANGELOG.md',
            'Makefile', 'CMakeLists.txt', '.gitlab-ci.yml', '.travis.yml',
            '.github/workflows', 'azure-pipelines.yml', 'Jenkinsfile',
            
            # Docker/Kubernetes
            'Dockerfile', 'docker-compose.yml', 'docker-compose.yaml',
            'k8s', 'kubernetes', 'deployment.yaml', 'service.yaml',
            
            # Java/Kotlin
            'pom.xml', 'build.gradle', 'settings.gradle', 'gradlew',
            'AndroidManifest.xml', 'build.xml', 'ivy.xml',
            
            # .NET
            'project.json', '*.csproj', '*.vbproj', '*.fsproj', 'app.config',
            'web.config', 'NuGet.Config', 'packages.config',
            
            # Ruby
            'Gemfile', 'Rakefile', 'Guardfile', 'config.ru',
            
            # PHP
            'composer.json', 'composer.lock', 'artisan', 'wp-config.php',
            
            # Go
            'go.mod', 'go.sum', 'main.go',
            
            # Rust
            'Cargo.toml', 'Cargo.lock',
            
            # Swift
            'Package.swift', 'Info.plist', 'project.pbxproj',
            
            # Flutter/Dart
            'pubspec.yaml', 'pubspec.lock'
        ]
        
        # First check exact matches
        if file_name in key_files:
            return True
        
        # Then check patterns
        for pattern in key_files:
            if '*' in pattern and fnmatch.fnmatch(file_name, pattern):
                return True
            if pattern in file_path:
                return True
        
        return False
    
    def _determine_project_details(self, project_info: dict) -> None:
        """
        Determine project type, primary language, and confidence level.
        
        Args:
            project_info: Project information to update
        """
        # Determine primary language based on file extensions
        file_type_counts = {
            'python': project_info['py_file_count'],
            'javascript': project_info['js_file_count'],
            'typescript': project_info['ts_file_count'],
            'java': project_info['java_file_count'],
            'html': project_info['html_file_count'],
            'css': project_info['css_file_count']
        }
        
        primary_language = max(file_type_counts.items(), key=lambda x: x[1])[0] if any(file_type_counts.values()) else 'unknown'
        project_info['primary_language'] = primary_language
        
        # Calculate confidence scores for different project types
        confidence_scores = {}
        
        # Check for Python package
        if 'setup.py' in [os.path.basename(f) for f in project_info['key_files']] or 'pyproject.toml' in [os.path.basename(f) for f in project_info['key_files']]:
            confidence_scores['python_package'] = 0.9
            project_info['confidence_factors']['has_setup_py'] = True
        
        # Check for Node.js package
        if 'package.json' in [os.path.basename(f) for f in project_info['key_files']]:
            confidence_scores['node_package'] = 0.85
            project_info['confidence_factors']['has_package_json'] = True
        
        # Check for microservice indicators
        if 'Dockerfile' in [os.path.basename(f) for f in project_info['key_files']] or 'docker-compose.yml' in [os.path.basename(f) for f in project_info['key_files']]:
            confidence_scores['microservice'] = 0.7
            project_info['confidence_factors']['has_docker'] = True
        
        # Check for web application indicators
        if project_info['html_file_count'] > 0 and (project_info['js_file_count'] > 0 or project_info['ts_file_count'] > 0):
            confidence_scores['web_application'] = 0.75
            project_info['confidence_factors']['has_html_and_js'] = True
        
        # Calculate framework scores
        max_framework_score = 0
        max_framework = None
        
        for framework, score in project_info['framework_scores'].items():
            if score > max_framework_score:
                max_framework_score = score
                max_framework = framework
        
        if max_framework and max_framework_score > 1.0:  # Threshold for confidence
            confidence_scores[max_framework] = min(max_framework_score / 3.0, 0.95)  # Normalize
            project_info['confidence_factors']['framework_detected'] = max_framework
            project_info['confidence_factors']['framework_score'] = max_framework_score
        
        # Python script/module with main function
        if project_info['has_main_function'] and project_info['primary_language'] == 'python':
            confidence_scores['python_script'] = 0.8
            project_info['confidence_factors']['has_main_function'] = True
        
        # Get the project type with highest confidence
        if confidence_scores:
            project_type, confidence = max(confidence_scores.items(), key=lambda x: x[1])
            project_info['project_type'] = project_type
            project_info['confidence'] = confidence
            project_info['confidence_text'] = self.core.get_confidence_level(confidence)
        else:
            # Default categorization based on language
            if project_info['primary_language'] == 'python':
                project_info['project_type'] = 'python_module'
                project_info['confidence'] = 0.4
                project_info['confidence_text'] = "Low"
            elif project_info['primary_language'] in ('javascript', 'typescript'):
                project_info['project_type'] = 'js_module'
                project_info['confidence'] = 0.4
                project_info['confidence_text'] = "Low" 
            elif project_info['primary_language'] == 'java':
                project_info['project_type'] = 'java_module'
                project_info['confidence'] = 0.4
                project_info['confidence_text'] = "Low"
            else:
                project_info['project_type'] = 'unknown'
                project_info['confidence'] = 0.2
                project_info['confidence_text'] = "Very Low"











###############
##  Part 3   ##
###############









class ProjectAnalyzerReporter:
    """
    Handles generating reports from analyzed projects.
    """
    
    def __init__(self, core):
        """
        Initialize the reporter with a reference to the core analyzer.
        
        Args:
            core: ProjectAnalyzerCore instance
        """
        self.core = core
        self.logger = core.logger
    
    def generate_reports(self, projects: list) -> dict:
        """
        Generate reports for the analyzed projects.
        
        Args:
            projects: List of analyzed projects
            
        Returns:
            dict: Paths to the generated reports
        """
        if not projects:
            self.logger.warning("No projects to generate reports for.")
            return {}
        
        # Create summary statistics
        summary = self._create_summary(projects)
        
        # Generate reports
        report_paths = {
            'summary': self._generate_summary_report(summary, projects),
            'projects': {}
        }
        
        # Generate individual project reports
        for project in projects:
            report_path = self._generate_project_report(project)
            report_paths['projects'][project['name']] = report_path
        
        self.logger.info(f"Reports generated in: {os.path.abspath(self.core.output_dir)}")
        
        return report_paths
    
    def _create_summary(self, projects: list) -> dict:
        """
        Create summary statistics from analyzed projects.
        
        Args:
            projects: List of analyzed projects
            
        Returns:
            dict: Summary statistics
        """
        from collections import Counter
        
        # Count project types, frameworks, languages
        project_types = Counter([p['project_type'] for p in projects])
        languages = Counter([p.get('primary_language', 'unknown') for p in projects])
        frameworks_detected = Counter()
        key_files_frequency = Counter()
        file_extensions = Counter()
        
        # Track confidence levels
        confidence_levels = Counter([p.get('confidence_text', 'Unknown') for p in projects])
        
        # Track microservices if detected
        microservices = [p for p in projects if p.get('is_microservice', False)]
        
        # Aggregate framework, key files and file extension data
        for project in projects:
            # Count frameworks
            for framework, score in project.get('framework_scores', {}).items():
                if score > 1.0:  # Threshold for counting
                    frameworks_detected[framework] += 1
            
            # Count key files
            for key_file in project.get('key_files', []):
                key_files_frequency[os.path.basename(key_file)] += 1
            
            # Aggregate file extensions
            for ext, count in project.get('file_extensions', {}).items():
                file_extensions[ext] += count
        
        # Calculate total code size
        total_files = sum(p['file_count'] for p in projects)
        
        # Create the summary dictionary
        summary = {
            'total_projects': len(projects),
            'project_types': dict(project_types),
            'frameworks_detected': dict(frameworks_detected),
            'languages': dict(languages),
            'key_files_frequency': dict(key_files_frequency),
            'file_extensions': dict(file_extensions),
            'confidence_levels': dict(confidence_levels),
            'total_files': total_files,
            'microservices_count': len(microservices),
            'has_microservices': len(microservices) > 0,
            'scan_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return summary
    
    def _generate_summary_report(self, summary: dict, projects: list) -> str:
        """
        Generate a summary report of all projects.
        
        Args:
            summary: Summary statistics
            projects: List of analyzed projects
            
        Returns:
            str: Path to the generated report
        """
        report_file = os.path.join(self.core.output_dir, 'summary_report.md')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Project Analysis Summary\n\n")
            f.write(f"*Generated on: {summary['scan_date']}*\n\n")
            f.write(f"## Overview\n\n")
            f.write(f"Total projects analyzed: **{summary['total_projects']}**\n")
            f.write(f"Total files: **{summary['total_files']}**\n\n")
            
            # Confidence distribution
            f.write(f"## Confidence Levels\n\n")
            f.write("| Confidence | Count | Percentage |\n")
            f.write("|------------|-------|------------|\n")
            
            for level, count in sorted(summary['confidence_levels'].items(), 
                                      key=lambda x: ["Very High", "High", "Medium", "Low", "Very Low", "Unknown"].index(x[0]) 
                                      if x[0] in ["Very High", "High", "Medium", "Low", "Very Low"] else 999):
                percentage = (count / summary['total_projects']) * 100
                f.write(f"| {level} | {count} | {percentage:.1f}% |\n")
            
            f.write(f"\n## Project Types\n\n")
            f.write("| Project Type | Count | Percentage |\n")
            f.write("|-------------|-------|------------|\n")
            
            for project_type, count in sorted(summary['project_types'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / summary['total_projects']) * 100
                f.write(f"| {project_type} | {count} | {percentage:.1f}% |\n")
            
            f.write(f"\n## Languages\n\n")
            f.write("| Language | Count | Percentage |\n")
            f.write("|----------|-------|------------|\n")
            
            for language, count in sorted(summary['languages'].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / summary['total_projects']) * 100
                f.write(f"| {language} | {count} | {percentage:.1f}% |\n")
            
            f.write(f"\n## Frameworks Detected\n\n")
            f.write("| Framework | Count | Percentage |\n")
            f.write("|-----------|-------|------------|\n")
            
            for framework, count in sorted(summary['frameworks_detected'].items(), key=lambda x: x[1], reverse=True)[:20]:
                percentage = (count / summary['total_projects']) * 100
                f.write(f"| {framework} | {count} | {percentage:.1f}% |\n")
            
            f.write(f"\n## Common Key Files\n\n")
            f.write("| File | Frequency |\n")
            f.write("|------|----------|\n")
            
            for file, count in sorted(summary['key_files_frequency'].items(), key=lambda x: x[1], reverse=True)[:15]:
                f.write(f"| {file} | {count} |\n")
            
            f.write(f"\n## Common File Extensions\n\n")
            f.write("| Extension | Count |\n")
            f.write("|-----------|-------|\n")
            
            for ext, count in sorted(summary['file_extensions'].items(), key=lambda x: x[1], reverse=True)[:20]:
                f.write(f"| {ext} | {count} |\n")
            
            # If microservices are detected
            if summary.get('has_microservices', False):
                f.write(f"\n## Microservices\n\n")
                f.write(f"Detected **{summary['microservices_count']}** microservices in the projects.\n")
                f.write(f"See the detailed microservice report for more information.\n\n")
            
            f.write(f"\n## Project List\n\n")
            for i, project in enumerate(sorted(projects, key=lambda x: x['name']), 1):
                confidence_text = project.get('confidence_text', 'Unknown')
                f.write(f"{i}. [{project['name']}](./{project['name'].replace(' ', '_')}_report.md) - " + 
                       f"{project['project_type']} ({confidence_text} confidence - {project['confidence']*100:.0f}%)\n")
        
        # Also generate an HTML version with improved styling
        html_file = os.path.join(self.core.output_dir, 'summary_report.html')
        
        with open(report_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
            html_content = markdown.markdown(md_content, extensions=['tables'])
            
            with open(html_file, 'w', encoding='utf-8') as html_f:
                html_f.write(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Project Analysis Summary</title>
                    <style>
                        :root {{
                            --bg-color: #2b2929;
                            --secondary-bg: #1a1a1a;
                            --tertiary-bg: #262626;
                            --text-color: #d1cccc;
                            --secondary-text: #a3a3a3;
                            --accent-color: #fb923c;
                            --accent-dark: #ea580c;
                            --border-color: rgba(82, 82, 82, 0.3);
                        }}
                        
                        body {{ 
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
                            line-height: 1.6; 
                            max-width: 1200px; 
                            margin: 0 auto; 
                            padding: 20px;
                            background-color: var(--bg-color);
                            color: var(--text-color);
                        }}
                        
                        h1, h2, h3, h4, h5, h6 {{
                            color: white;
                            margin-top: 1.5em;
                            margin-bottom: 0.5em;
                        }}
                        
                        h1 {{ 
                            border-bottom: 2px solid var(--accent-color);
                            padding-bottom: 10px;
                        }}
                        
                        h2 {{
                            border-bottom: 1px solid var(--border-color);
                            padding-bottom: 5px;
                        }}
                        
                        a {{ 
                            color: var(--accent-color); 
                            text-decoration: none;
                            transition: color 0.2s;
                        }}
                        
                        a:hover {{
                            color: var(--accent-dark);
                            text-decoration: underline;
                        }}
                        
                        table {{ 
                            border-collapse: collapse; 
                            width: 100%; 
                            margin: 20px 0;
                            background-color: var(--tertiary-bg);
                            border-radius: 8px;
                            overflow: hidden;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        }}
                        
                        th {{ 
                            background-color: var(--secondary-bg); 
                            color: white;
                            padding: 12px 15px;
                            text-align: left;
                            font-weight: 600;
                        }}
                        
                        td {{ 
                            padding: 10px 15px;
                            border-top: 1px solid var(--border-color);
                        }}
                        
                        tr:nth-child(even) {{ 
                            background-color: rgba(255, 255, 255, 0.05); 
                        }}
                        
                        tr:hover {{
                            background-color: rgba(255, 255, 255, 0.1);
                        }}
                        
                        em {{
                            color: var(--secondary-text);
                            font-style: italic;
                        }}
                        
                        strong {{
                            color: white;
                            font-weight: 600;
                        }}
                        
                        code {{
                            font-family: 'Courier New', Courier, monospace;
                            background-color: var(--secondary-bg);
                            padding: 2px 4px;
                            border-radius: 3px;
                        }}
                        
                        /* Responsive adjustments */
                        @media (max-width: 768px) {{
                            table {{
                                display: block;
                                overflow-x: auto;
                            }}
                            
                            body {{
                                padding: 10px;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """)
        
        return report_file
    
    def _generate_project_report(self, project: dict) -> str:
        """
        Generate a detailed report for a single project.
        
        Args:
            project: Project information
            
        Returns:
            str: Path to the generated report
        """
        project_name = project['name']
        safe_name = project_name.replace(' ', '_')
        report_file = os.path.join(self.core.output_dir, f"{safe_name}_report.md")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Project Analysis: {project_name}\n\n")
            
            f.write(f"## Overview\n\n")
            f.write(f"- **Path**: `{project['path']}`\n")
            f.write(f"- **Project Type**: {project['project_type']}\n")
            f.write(f"- **Confidence**: {project.get('confidence_text', 'Unknown')} ({project['confidence']*100:.0f}%)\n")
            f.write(f"- **Primary Language**: {project.get('primary_language', 'Unknown')}\n")
            f.write(f"- **File Count**: {project['file_count']}\n")
            
            # More detailed file statistics
            if project.get('py_file_count', 0) > 0:
                f.write(f"- **Python Files**: {project['py_file_count']}\n")
            if project.get('js_file_count', 0) > 0:
                f.write(f"- **JavaScript Files**: {project['js_file_count']}\n")
            if project.get('ts_file_count', 0) > 0:
                f.write(f"- **TypeScript Files**: {project['ts_file_count']}\n")
            if project.get('java_file_count', 0) > 0:
                f.write(f"- **Java Files**: {project['java_file_count']}\n")
            if project.get('html_file_count', 0) > 0:
                f.write(f"- **HTML Files**: {project['html_file_count']}\n")
            if project.get('css_file_count', 0) > 0:
                f.write(f"- **CSS Files**: {project['css_file_count']}\n")
                
            f.write(f"- **Has Main Function**: {project['has_main_function']}\n")
            
            # Confidence factors if available
            if project.get('confidence_factors'):
                f.write(f"\n## Confidence Factors\n\n")
                for factor, value in project['confidence_factors'].items():
                    if isinstance(value, bool):
                        f.write(f"- **{factor}**: {value}\n")
                    elif isinstance(value, (int, float)):
                        f.write(f"- **{factor}**: {value:.2f}\n")
                    else:
                        f.write(f"- **{factor}**: {value}\n")
            
            # Framework detection scores
            if project.get('framework_scores'):
                f.write(f"\n## Framework Detection Scores\n\n")
                f.write("| Framework | Score | Confidence |\n")
                f.write("|-----------|-------|------------|\n")
                
                for framework, score in sorted(project['framework_scores'].items(), key=lambda x: x[1], reverse=True):
                    if score > 0:
                        confidence = self.core.get_confidence_level(min(score / 3.0, 0.95))
                        f.write(f"| {framework} | {score:.2f} | {confidence} |\n")
                f.write("\n")
            
            # Key files section
            if project.get('key_files'):
                f.write(f"\n## Key Files\n\n")
                for key_file in sorted(project['key_files']):
                    f.write(f"- `{key_file}`\n")
                f.write("\n")
            
            # Imports section
            if project.get('imports'):
                f.write(f"\n## Top Imports\n\n")
                import_list = list(project['imports'])
                # Sort by frequency if available, otherwise alphabetically
                top_imports = sorted(import_list)[:30]  # Limit to 30 imports
                for import_name in top_imports:
                    f.write(f"- `{import_name}`\n")
                
                if len(import_list) > 30:
                    f.write(f"\n*...and {len(import_list) - 30} more imports*\n")
                f.write("\n")
            
            # File extensions
            if project.get('file_extensions'):
                f.write(f"\n## File Extensions\n\n")
                f.write("| Extension | Count |\n")
                f.write("|-----------|-------|\n")
                
                for ext, count in sorted(project['file_extensions'].items(), key=lambda x: x[1], reverse=True)[:15]:
                    f.write(f"| {ext} | {count} |\n")
                f.write("\n")
            
            # Errors section
            if project.get('errors'):
                f.write(f"\n## Analysis Errors\n\n")
                f.write("| File | Error |\n")
                f.write("|------|-------|\n")
                
                for error in project['errors'][:20]:  # Limit to 20 errors
                    f.write(f"| {error['file']} | {error['error']} |\n")
                
                if len(project['errors']) > 20:
                    f.write(f"\n*...and {len(project['errors']) - 20} more errors*\n")
                f.write("\n")
            
            # Directory structure
            f.write(f"\n## Directory Structure\n\n")
            f.write(f"```\n")
            try:
                self._write_directory_tree(f, project['path'], max_depth=4)
            except Exception as e:
                f.write(f"Error generating directory tree: {str(e)}\n")
            f.write(f"```\n")
            
            # If microservice, add microservice details
            if project.get('is_microservice', False):
                f.write(f"\n## Microservice Details\n\n")
                f.write(f"- **Microservice Probability**: {project['microservice_probability']*100:.0f}%\n")
                
                if project.get('microservice_scores'):
                    f.write(f"\n### Microservice Indicators\n\n")
                    for indicator, score in sorted(project['microservice_scores'].items(), key=lambda x: x[1], reverse=True):
                        f.write(f"- {indicator}: {score:.1f}\n")
                
                if project.get('service_endpoints'):
                    f.write(f"\n### API Endpoints\n\n")
                    f.write("| Path | Type | File |\n")
                    f.write("|------|------|------|\n")
                    
                    for endpoint in project.get('service_endpoints', []):
                        f.write(f"| {endpoint['path']} | {endpoint['type']} | {endpoint['file']} |\n")
                
                if project.get('service_calls'):
                    f.write(f"\n### External Service Calls\n\n")
                    f.write("| URL | File |\n")
                    f.write("|-----|------|\n")
                    
                    for call in project.get('service_calls', []):
                        url = call['url']
                        if isinstance(url, tuple):
                            url = url[0]
                        f.write(f"| {url} | {call['file']} |\n")
        
        # Also generate HTML version
        html_file = os.path.join(self.core.output_dir, f"{safe_name}_report.html")
        
        with open(report_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
            html_content = markdown.markdown(md_content, extensions=['tables'])
            
            with open(html_file, 'w', encoding='utf-8') as html_f:
                html_f.write(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Project Analysis: {project_name}</title>
                    <style>
                        :root {{
                            --bg-color: #2b2929;
                            --secondary-bg: #1a1a1a;
                            --tertiary-bg: #262626;
                            --text-color: #d1cccc;
                            --secondary-text: #a3a3a3;
                            --accent-color: #fb923c;
                            --accent-dark: #ea580c;
                            --border-color: rgba(82, 82, 82, 0.3);
                        }}
                        
                        body {{ 
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
                            line-height: 1.6; 
                            max-width: 1200px; 
                            margin: 0 auto; 
                            padding: 20px;
                            background-color: var(--bg-color);
                            color: var(--text-color);
                        }}
                        
                        h1, h2, h3, h4, h5, h6 {{
                            color: white;
                            margin-top: 1.5em;
                            margin-bottom: 0.5em;
                        }}
                        
                        h1 {{ 
                            border-bottom: 2px solid var(--accent-color);
                            padding-bottom: 10px;
                        }}
                        
                        h2 {{
                            border-bottom: 1px solid var(--border-color);
                            padding-bottom: 5px;
                        }}
                        
                        a {{ 
                            color: var(--accent-color); 
                            text-decoration: none;
                            transition: color 0.2s;
                        }}
                        
                        a:hover {{
                            color: var(--accent-dark);
                            text-decoration: underline;
                        }}
                        
                        table {{ 
                            border-collapse: collapse; 
                            width: 100%; 
                            margin: 20px 0;
                            background-color: var(--tertiary-bg);
                            border-radius: 8px;
                            overflow: hidden;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        }}
                        
                        th {{ 
                            background-color: var(--secondary-bg); 
                            color: white;
                            padding: 12px 15px;
                            text-align: left;
                            font-weight: 600;
                        }}
                        
                        td {{ 
                            padding: 10px 15px;
                            border-top: 1px solid var(--border-color);
                        }}
                        
                        tr:nth-child(even) {{ 
                            background-color: rgba(255, 255, 255, 0.05); 
                        }}
                        
                        tr:hover {{
                            background-color: rgba(255, 255, 255, 0.1);
                        }}
                        
                        em {{
                            color: var(--secondary-text);
                            font-style: italic;
                        }}
                        
                        strong {{
                            color: white;
                            font-weight: 600;
                        }}
                        
                        code {{
                            font-family: 'Courier New', Courier, monospace;
                            background-color: var(--secondary-bg);
                            padding: 2px 4px;
                            border-radius: 3px;
                        }}
                        
                        pre {{
                            background-color: var(--secondary-bg);
                            padding: 15px;
                            border-radius: 8px;
                            overflow-x: auto;
                            border: 1px solid var(--border-color);
                        }}
                        
                        pre code {{
                            background-color: transparent;
                            padding: 0;
                        }}
                        
                        /* Responsive adjustments */
                        @media (max-width: 768px) {{
                            table {{
                                display: block;
                                overflow-x: auto;
                            }}
                            
                            body {{
                                padding: 10px;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """)
        
        return report_file
    
    def _write_directory_tree(self, file, path, prefix="", max_depth=3, current_depth=0):
        """
        Write a directory tree structure to the report file.
        
        Args:
            file: File object to write to
            path: Path to start from
            prefix: Prefix for the current line
            max_depth: Maximum depth to recurse
            current_depth: Current recursion depth
        """
        if current_depth > max_depth:
            file.write(f"{prefix}...\n")
            return
        
        try:
            entries = list(os.scandir(path))
            entries = [e for e in entries if not self.core.should_ignore(e.path)]
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
            
            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                connector = "└── " if is_last else "├── "
                
                file.write(f"{prefix}{connector}{entry.name}\n")
                
                if entry.is_dir():
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    try:
                        # Skip if we don't have access
                        if os.access(entry.path, os.R_OK):
                            self._write_directory_tree(file, entry.path, next_prefix, max_depth, current_depth + 1)
                        else:
                            file.write(f"{next_prefix}└── (No access)\n")
                    except PermissionError:
                        file.write(f"{next_prefix}└── (Permission denied)\n")
                    except Exception as e:
                        file.write(f"{next_prefix}└── (Error: {str(e)})\n")
        except PermissionError:
            file.write(f"{prefix}(Permission denied)\n")
        except Exception as e:
            file.write(f"{prefix}(Error: {str(e)})\n")








###############
##  Part 4   ##
###############





import os
import time
import concurrent.futures
from typing import List, Dict, Optional, Union, Any
import logging
from pathlib import Path


from framework_patterns import FRAMEWORK_PATTERNS

class ProjectAnalyzer:
    """
    Main class that combines core, scanner, and reporter functionality.
    This is the entry point for the analysis process.
    """
    
    def __init__(self, 
                 root_dir: str = '.', 
                 output_dir: str = './reports', 
                 ignore_patterns: Optional[List[str]] = None,
                 max_workers: int = 4,
                 max_depth: int = 3,
                 verbose: bool = False):
        """
        Initialize the project analyzer.
        
        Args:
            root_dir (str): Root directory to start scanning from
            output_dir (str): Directory to save reports to
            ignore_patterns (List[str], optional): Patterns to ignore
            max_workers (int): Maximum number of worker threads for parallel processing
            max_depth (int): Maximum depth to search for projects
            verbose (bool): Enable verbose logging
        """
        self.max_depth = max_depth
        
        # Initialize components
        self.core = ProjectAnalyzerCore(
            root_dir=root_dir,
            output_dir=output_dir,
            ignore_patterns=ignore_patterns,
            max_workers=max_workers,
            verbose=verbose
        )
        
        # Load framework patterns
        self.core.load_framework_patterns(FRAMEWORK_PATTERNS)
        
        # Initialize scanner and reporter
        self.scanner = ProjectAnalyzerScanner(self.core)
        self.reporter = ProjectAnalyzerReporter(self.core)
        
        # Store results
        self.projects = []
        self.report_paths = {}
        
        # Initialize logger
        self.logger = self.core.logger
        self.logger.info(f"ProjectAnalyzer initialized with max depth: {max_depth}")
    
    def scan_projects(self, callback=None):
        """
        Scan the root directory for projects and analyze them.
        
        Args:
            callback: Optional callback function to report progress
            
        Returns:
            List[dict]: List of analyzed projects
        """
        start_time = time.time()
        self.logger.info(f"Starting project analysis...")
        
        # Track statistics
        total_dirs_scanned = 0
        projects_found = 0
        
        # Projects list
        self.projects = []
        
        # Look for projects in root dir up to max depth
        root_path = Path(self.core.root_dir)
        
        # Process the root directory first
        self.logger.info(f"Analyzing root directory: {root_path}")
        project_info = self.scanner.analyze_directory(str(root_path))
        if project_info:
            self.projects.append(project_info)
            projects_found += 1
            
        # Now scan for additional directories using glob and filter
        # Get directories at each depth level
        for depth in range(1, self.max_depth + 1):
            self.logger.info(f"Scanning at depth {depth}...")
            
            # Use glob pattern to get directories at this depth
            pattern = '/'.join(['*'] * depth)
            dirs_at_depth = list(root_path.glob(pattern))
            
            # Filter out ignored directories
            dirs_to_process = [d for d in dirs_at_depth if d.is_dir() and not self.core.should_ignore(d)]
            
            self.logger.info(f"Found {len(dirs_to_process)} directories to process at depth {depth}")
            total_dirs_scanned += len(dirs_to_process)
            
            # Use ThreadPoolExecutor for parallel directory processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.core.max_workers) as executor:
                future_to_dir = {executor.submit(self.scanner.analyze_directory, str(d)): d for d in dirs_to_process}
                
                # Process results as they complete
                for i, future in enumerate(concurrent.futures.as_completed(future_to_dir)):
                    directory = future_to_dir[future]
                    try:
                        project_info = future.result()
                        if project_info:
                            self.projects.append(project_info)
                            projects_found += 1
                            
                            # Report progress if callback is provided
                            if callback:
                                progress = (i + 1) / len(dirs_to_process)
                                callback(progress, f"Analyzing {directory.name}")
                    except Exception as e:
                        self.logger.error(f"Error analyzing {directory}: {str(e)}")
        
        # Sort projects by name for consistent output
        self.projects = sorted(self.projects, key=lambda p: p['name'])
        
        # Report statistics
        elapsed_time = time.time() - start_time
        self.logger.info(f"Analysis completed in {elapsed_time:.2f} seconds")
        self.logger.info(f"Scanned {total_dirs_scanned} directories")
        self.logger.info(f"Found {projects_found} projects")
        
        return self.projects
    
    def generate_reports(self):
        """
        Generate reports for the analyzed projects.
        
        Returns:
            Dict: Paths to the generated reports
        """
        if not self.projects:
            self.logger.warning("No projects to generate reports for. Run scan_projects() first.")
            return {}
        
        self.logger.info("Generating reports...")
        self.report_paths = self.reporter.generate_reports(self.projects)
        return self.report_paths
    
    def run_analysis(self, callback=None):
        """
        Run the full analysis process: scan projects and generate reports.
        
        Args:
            callback: Optional callback function to report progress
            
        Returns:
            Dict: Analysis results including projects and report paths
        """
        self.scan_projects(callback)
        self.generate_reports()
        
        return {
            'projects': self.projects,
            'reports': self.report_paths
        }
    
    def get_project_types(self):
        """
        Get the count of different project types.
        
        Returns:
            Dict: Project type counts
        """
        from collections import Counter
        return Counter([p.get('project_type', 'unknown') for p in self.projects])
    
    def get_frameworks(self):
        """
        Get the count of different frameworks detected.
        
        Returns:
            Dict: Framework counts
        """
        from collections import Counter
        frameworks = Counter()
        
        for project in self.projects:
            for framework, score in project.get('framework_scores', {}).items():
                if score > 1.0:  # Threshold for counting
                    frameworks[framework] += 1
        
        return frameworks
    
    def get_languages(self):
        """
        Get the count of primary languages in projects.
        
        Returns:
            Dict: Language counts
        """
        from collections import Counter
        return Counter([p.get('primary_language', 'unknown') for p in self.projects])
    
    def get_summary_stats(self):
        """
        Get summary statistics for the analyzed projects.
        
        Returns:
            Dict: Summary statistics
        """
        if not self.projects:
            return {}
        
        from collections import Counter
        
        # Setup counters
        project_types = self.get_project_types()
        frameworks = self.get_frameworks()
        languages = self.get_languages()
        
        # Get confidence levels
        confidence_levels = Counter([p.get('confidence_text', 'Unknown') for p in self.projects])
        
        # Calculate total files
        total_files = sum(p.get('file_count', 0) for p in self.projects)
        
        # Return summary stats
        return {
            'total_projects': len(self.projects),
            'total_files': total_files,
            'project_types': dict(project_types),
            'frameworks': dict(frameworks),
            'languages': dict(languages),
            'confidence_levels': dict(confidence_levels),
            'analysis_date': time.strftime("%Y-%m-%d %H:%M:%S")
        }

