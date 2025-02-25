#!/usr/bin/env python3
"""
Project Analysis Tool 
---------------------
A comprehensive tool for analyzing project structures, 
detecting frameworks, and identifying microservice architecture.
"""

import os
import sys
import argparse
import time
from pathlib import Path
from project_analyzer import ProjectAnalyzer
from microservice_detector import MicroserviceDetector

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Analyze project directories, frameworks, and microservice architecture.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--root', '-r', 
        default='.', 
        help='Root directory to scan for projects (default: current directory)'
    )
    
    parser.add_argument(
        '--output', '-o', 
        default='./reports', 
        help='Output directory for reports (default: ./reports)'
    )
    
    parser.add_argument(
        '--ignore', '-i', 
        nargs='+', 
        help='Additional patterns to ignore (e.g. --ignore build dist temp)'
    )
    
    parser.add_argument(
        '--depth', '-d', 
        type=int, 
        default=3, 
        help='Maximum depth to search for projects (default: 3)'
    )
    
    parser.add_argument(
        '--microservices', '-m', 
        action='store_true', 
        help='Enable microservice architecture detection'
    )
    
    parser.add_argument(
        '--verbose', '-v', 
        action='store_true', 
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--skip-home-dir', 
        action='store_true',
        help='Skip scanning user home directory related folders (recommended)'
    )
    
    return parser.parse_args()

def main():
    """Main function to run the analysis."""
    args = parse_arguments()
    
    start_time = time.time()
    
    # Print header
    print("\n" + "="*80)
    print(" PROJECT ANALYSIS TOOL ".center(80, '='))
    print("="*80 + "\n")
    
    # Validate directories
    if not os.path.isdir(args.root):
        print(f"ERROR: Root directory '{args.root}' does not exist!")
        return 1
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Set up ignore patterns
    ignore_patterns = args.ignore or []
    
    # Add home directory related folders to ignore if requested
    if args.skip_home_dir:
        home_dir_patterns = [
            '.cache', '.config', '.azure', '.aws', '.android', 
            '.vscode', '.idea', '.git', '.svn', 'node_modules',
            'site-packages', '__pycache__', '.ipynb_checkpoints',
            'AppData', 'Local Settings', 'Application Data',
            'Temporary Internet Files', 'Temp', 'tmp',
            '.gradle', '.nuget', '.m2', '.npm', '.yarn',
            'Downloads', 'Documents', 'Pictures', 'Music', 'Videos',
            'OneDrive', 'Dropbox', 'Google Drive', 'iCloud'
        ]
        ignore_patterns.extend(home_dir_patterns)
        if args.verbose:
            print(f"Skipping home directory related folders: {', '.join(home_dir_patterns)}")
    
    # Initialize analyzer
    print(f"Initializing Project Analyzer...")
    print(f"Root directory: {os.path.abspath(args.root)}")
    print(f"Output directory: {os.path.abspath(args.output)}")
    print(f"Maximum search depth: {args.depth}")
    if ignore_patterns:
        print(f"Ignore patterns: {', '.join(ignore_patterns)}")
    print()
    
    analyzer = ProjectAnalyzer(
        root_dir=args.root, 
        output_dir=args.output, 
        ignore_patterns=ignore_patterns
    )
    
    # Analyze projects
    print("Scanning for projects and analyzing their structure...")
    analyzer.scan_projects()
    
    # Print project summary
    projects_found = len(analyzer.projects)
    if projects_found == 0:
        print("\nNo projects found in the specified directory.")
        return 0
    
    print(f"\nFound {projects_found} project(s):")
    for i, project in enumerate(analyzer.projects, 1):
        print(f"  {i}. {project['name']} ({project['project_type']}, {project['confidence']*100:.0f}% confidence)")
    
    # Generate basic reports
    print("\nGenerating project reports...")
    analyzer.generate_reports()
    
    # Analyze for microservices if requested
    if args.microservices:
        print("\nAnalyzing microservice architecture...")
        microservice_detector = MicroserviceDetector(analyzer)
        relationships = microservice_detector.detect_microservices()
        
        microservices = [p for p in analyzer.projects if p.get('is_microservice', False)]
        print(f"\nDetected {len(microservices)} microservice(s):")
        for i, service in enumerate(microservices, 1):
            print(f"  {i}. {service['name']} ({service['microservice_probability']*100:.0f}% confidence)")
        
        if relationships:
            print(f"\nDetected {len(relationships)} service relationships")
    
    # Show execution time
    elapsed_time = time.time() - start_time
    print(f"\nAnalysis completed in {elapsed_time:.2f} seconds")
    print(f"Reports generated in: {os.path.abspath(args.output)}")
    print("\nAvailable reports:")
    print(f"  - Summary: {os.path.join(args.output, 'summary_report.md')}")
    if args.microservices:
        print(f"  - Microservices: {os.path.join(args.output, 'microservice_report.md')}")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())