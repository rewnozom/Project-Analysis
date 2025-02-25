





###############
##  Part 1   ##
###############




import os
import re
import json
import datetime
import markdown
import logging
from collections import defaultdict
from typing import List, Dict, Optional, Tuple, Set, Any, Union
import concurrent.futures

class MicroserviceDetectorBase:
    """Base class for microservice detection providing core functionality."""
    
    def __init__(self, project_analyzer, max_workers: int = 4):
        """
        Initialize the microservice detector.
        
        Args:
            project_analyzer: ProjectAnalyzer instance
            max_workers (int): Maximum number of worker threads for parallel processing
        """
        self.analyzer = project_analyzer
        self.projects = project_analyzer.projects
        self.output_dir = project_analyzer.core.output_dir
        self.max_workers = max_workers
        
        # Set up logging
        self.logger = logging.getLogger("MicroserviceDetector")
        self.logger.setLevel(logging.INFO)
        
        # Microservice detection patterns
        self.microservice_patterns = {
            'docker': {
                'files': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
                'weight': 1.0
            },
            'kubernetes': {
                'files': ['k8s', 'kubernetes', 'deployment.yaml', 'service.yaml', 'ingress.yaml', 'values.yaml', 'helm'],
                'content_patterns': ['apiVersion:', 'kind: Deployment', 'kind: Service', 'kind: Ingress'],
                'weight': 1.0
            },
            'api_gateway': {
                'files': ['gateway', 'proxy', 'nginx.conf', 'traefik.toml', 'zuul', 'ambassador'],
                'content_patterns': ['proxy_pass', 'upstream', 'location', 'PathPrefix', 'routes'],
                'weight': 0.8
            },
            'service_discovery': {
                'files': ['consul', 'eureka', 'zookeeper', 'etcd', 'service-registry'],
                'content_patterns': ['service_name', 'service-name', 'discovery', 'registry'],
                'weight': 0.8
            },
            'message_queue': {
                'files': ['rabbitmq', 'kafka', 'redis', 'activemq', 'sqs', 'pubsub'],
                'imports': ['pika', 'kafka', 'redis', 'celery', 'amqp', 'nats'],
                'content_patterns': ['KAFKA_', 'RABBITMQ_', 'REDIS_', 'message broker', 'message queue', 'pub/sub'],
                'weight': 0.7
            },
            'microservice_config': {
                'files': ['.env', 'config.yaml', 'config.json', 'application.properties', 'application.yml'],
                'content_patterns': ['SERVICE_', 'ENDPOINT_', 'API_URL', 'service:', 'endpoints:'],
                'weight': 0.6
            },
            'health_check': {
                'files': ['health', 'healthcheck'],
                'content_patterns': ['/health', '/status', 'healthcheck', 'readiness', 'liveness'],
                'weight': 0.7
            },
            'containerization': {
                'files': ['container', 'pod', 'swarm', 'ecs', 'fargate'],
                'content_patterns': ['container_name', 'image:', 'containerPort'],
                'weight': 0.8
            },
            'service_boundary': {
                'files': ['boundary', 'domain', 'context'],
                'content_patterns': ['bounded context', 'domain-driven', 'service boundary'],
                'weight': 0.6
            }
        }
        
        # Communication patterns for detecting service interactions
        self.communication_patterns = {
            'rest_api': {
                'imports': ['requests', 'aiohttp', 'axios', 'fetch', 'HttpClient'],
                'content_patterns': ['@app.route', '@router.get', 'axios.get', 'fetch(', 'http.get', 'RestController'],
                'weight': 0.7
            },
            'grpc': {
                'files': ['.proto'],
                'imports': ['grpc'],
                'content_patterns': ['service', 'rpc', 'protobuf', 'proto3'],
                'weight': 0.9
            },
            'graphql': {
                'imports': ['graphql', 'apollo', 'gql'],
                'content_patterns': ['query {', 'type Query', 'gql`', 'graphql.executeQuery'],
                'weight': 0.8
            },
            'event_based': {
                'imports': ['pika', 'kafka', 'pubsub', 'eventbus', 'EventEmitter'],
                'content_patterns': ['publish', 'subscribe', 'emit', 'on(', 'event-driven'],
                'weight': 0.8
            },
            'soap': {
                'imports': ['soap', 'wsdl'],
                'content_patterns': ['<soap:', 'wsdl', 'SoapClient', 'SoapService'],
                'weight': 0.6
            },
            'websocket': {
                'imports': ['websocket', 'socket.io', 'ws'],
                'content_patterns': ['WebSocket', 'socket.on', 'socket.emit', 'ws.send'],
                'weight': 0.7
            }
        }
        
        # Results storage
        self.microservices = []
        self.relationships = []
    
    def detect_microservices(self, callback=None):
        """
        Detect microservice architecture and relationships between projects.
        
        Args:
            callback: Optional callback function for progress updates
        
        Returns:
            Dict: Microservice analysis results
        """
        if not self.projects:
            self.logger.warning("No projects to analyze. Run scan_projects() first.")
            return {}
        
        self.logger.info("Analyzing projects for microservice architecture...")
        
        # Reset results storage
        self.microservices = []
        self.relationships = []
        
        # Analyze projects for microservice patterns in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_project = {executor.submit(self._analyze_microservice_patterns, project): project 
                               for project in self.projects}
            
            # Process results as they complete
            for i, future in enumerate(concurrent.futures.as_completed(future_to_project)):
                project = future_to_project[future]
                try:
                    # Get the result (project is modified in-place)
                    future.result()
                    
                    # Report progress if callback is provided
                    if callback:
                        progress = (i + 1) / len(self.projects)
                        callback(progress, f"Analyzing {project['name']} for microservice patterns")
                except Exception as e:
                    self.logger.error(f"Error analyzing {project['name']}: {str(e)}")
        
        # Collect microservices
        self.microservices = [p for p in self.projects if p.get('is_microservice', False)]
        
        # Detect relationships between services
        self.relationships = self._detect_service_relationships()
        
        # Generate microservice architecture report
        report_path = self._generate_microservice_report()
        
        self.logger.info(f"Microservice analysis complete. Found {len(self.microservices)} microservices")
        
        return {
            'microservices': self.microservices,
            'relationships': self.relationships,
            'report': report_path
        }
    
    def _analyze_microservice_patterns(self, project: dict) -> None:
        """
        Analyze a project for microservice patterns.
        Modifies the project dictionary in-place.
        
        Args:
            project: Project dictionary to analyze
        """
        # Initialize microservice-specific attributes
        project['microservice_scores'] = defaultdict(float)
        project['communication_types'] = defaultdict(float)
        project['service_endpoints'] = []
        project['service_calls'] = []








###############
##  Part 2   ##
###############





class MicroserviceAnalyzer(MicroserviceDetectorBase):
    """Handles analyzing individual files and extracting endpoints and service calls."""
    
    def __init__(self, project_analyzer, max_workers=4):
        """Initialize the microservice analyzer."""
        super().__init__(project_analyzer, max_workers)
    
    def _analyze_microservice_patterns(self, project: dict) -> None:
        """Analyze a project for microservice patterns."""
        super()._analyze_microservice_patterns(project)
        
        # Scan files for microservice patterns
        for file_info in project.get('files', []):
            file_path = file_info.get('full_path')
            file_name = os.path.basename(file_path)
            
            # Skip if file doesn't exist or we can't access it
            if not file_path or not os.path.isfile(file_path) or not os.access(file_path, os.R_OK):
                continue
            
            # Check for microservice indicator files
            for pattern_type, patterns in self.microservice_patterns.items():
                if 'files' in patterns:
                    for file_pattern in patterns['files']:
                        if file_pattern in file_name or file_pattern in file_path:
                            project['microservice_scores'][pattern_type] += patterns['weight']
            
            # Check file content for microservice patterns
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Check for pattern matches in content
                    for pattern_type, patterns in self.microservice_patterns.items():
                        if 'content_patterns' in patterns:
                            for content_pattern in patterns['content_patterns']:
                                if content_pattern in content:
                                    project['microservice_scores'][pattern_type] += patterns['weight']
                    
                    # Check for communication patterns
                    for comm_type, patterns in self.communication_patterns.items():
                        if 'content_patterns' in patterns:
                            for content_pattern in patterns['content_patterns']:
                                if content_pattern in content:
                                    project['communication_types'][comm_type] += patterns['weight']
                    
                    # Extract API endpoints (for APIs)
                    if file_path.endswith(('.py', '.js', '.ts', '.java', '.kt', '.scala', '.rb', '.php')):
                        self._extract_endpoints(project, file_path, content)
                        
                    # Extract service calls (looking for URLs, API calls)
                    if file_path.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.kt', '.scala', '.rb', '.php')):
                        self._extract_service_calls(project, file_path, content)
            except Exception as e:
                self.logger.debug(f"Error analyzing file {file_path}: {str(e)}")
        
        # Calculate overall microservice probability
        total_score = sum(project['microservice_scores'].values())
        threshold = 2.0  # Minimum score to be considered a microservice
        
        # Adjust threshold based on project size
        if project.get('file_count', 0) < 5:
            # Small projects need more evidence to be considered microservices
            threshold = 3.0
        
        project['is_microservice'] = total_score > threshold
        project['microservice_probability'] = min(total_score / 5.0, 0.95)  # Normalize
        
        # Determine primary communication style
        if project['communication_types']:
            project['primary_communication'] = max(
                project['communication_types'].items(), 
                key=lambda x: x[1]
            )[0]
        else:
            project['primary_communication'] = 'unknown'
    
    def _extract_endpoints(self, project: dict, file_path: str, content: str) -> None:
        """
        Extract API endpoints from code files.
        
        Args:
            project: Project dictionary to update
            file_path: Path to the file
            content: File content
        """
        endpoints = []
        
        # Expanded patterns for various frameworks
        endpoint_patterns = {
            # Flask patterns
            'flask': [
                r'@app\.route\([\'"]([^\'"]+)[\'"]',
                r'@blueprint\.route\([\'"]([^\'"]+)[\'"]',
                r'@api\.route\([\'"]([^\'"]+)[\'"]'
            ],
            # FastAPI patterns
            'fastapi': [
                r'@app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
                r'@router\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
                r'@api\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]'
            ],
            # Express.js patterns
            'express': [
                r'app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
                r'router\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]'
            ],
            # Spring patterns
            'spring': [
                r'@RequestMapping\([\'"]([^\'"]+)[\'"]',
                r'@GetMapping\([\'"]([^\'"]+)[\'"]',
                r'@PostMapping\([\'"]([^\'"]+)[\'"]',
                r'@PutMapping\([\'"]([^\'"]+)[\'"]',
                r'@DeleteMapping\([\'"]([^\'"]+)[\'"]'
            ],
            # Django patterns
            'django': [
                r'path\([\'"]([^\'"]+)[\'"]',
                r'url\([\'"]([^\'"]+)[\'"]',
                r're_path\([\'"]([^\'"]+)[\'"]'
            ],
            # Ruby on Rails patterns
            'rails': [
                r'get [\'"]([^\'"]+)[\'"]',
                r'post [\'"]([^\'"]+)[\'"]',
                r'put [\'"]([^\'"]+)[\'"]',
                r'delete [\'"]([^\'"]+)[\'"]'
            ],
            # Generic patterns
            'generic': [
                r'api/([a-zA-Z0-9/_-]+)',
                r'endpoint[s]?[\'"]?\s*[=:]\s*[\'"]([^\'"]+)[\'"]',
                r'route[s]?[\'"]?\s*[=:]\s*[\'"]([^\'"]+)[\'"]'
            ]
        }
        
        # Process all patterns
        for framework, patterns in endpoint_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Handle different match structures
                    if isinstance(match, tuple):
                        # For patterns that capture method and path (like fastapi)
                        if len(match) == 2 and match[0] in ('get', 'post', 'put', 'delete', 'patch'):
                            path = match[1]
                            method = match[0].upper()
                        else:
                            # Just use the last item in the tuple
                            path = match[-1]
                            method = 'UNKNOWN'
                    else:
                        path = match
                        method = 'UNKNOWN'
                    
                    # Clean the path
                    if not path.startswith('/') and not path.startswith('http'):
                        path = '/' + path
                    
                    endpoint = {
                        'path': path,
                        'method': method,
                        'file': os.path.basename(file_path),
                        'framework': framework,
                        'type': self._determine_endpoint_type(path)
                    }
                    endpoints.append(endpoint)
        
        # Add unique endpoints to project
        for endpoint in endpoints:
            if endpoint not in project['service_endpoints']:
                project['service_endpoints'].append(endpoint)
    
    def _extract_service_calls(self, project: dict, file_path: str, content: str) -> None:
        """
        Extract service calls (API requests to other services).
        
        Args:
            project: Project dictionary to update
            file_path: Path to the file
            content: File content
        """
        service_calls = []
        
        # Expanded HTTP request patterns
        request_patterns = {
            # Python requests
            'python': [
                r'requests\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
                r'aiohttp\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
            ],
            # JavaScript fetch/axios
            'javascript': [
                r'fetch\([\'"]([^\'"]+)[\'"]',
                r'axios\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
                r'http\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]',
            ],
            # Java patterns
            'java': [
                r'RestTemplate\(\)\..*\([\'"]([^\'"]+)[\'"]',
                r'webClient\.(get|post|put|delete)\(\)\.(uri|url)\([\'"]([^\'"]+)[\'"]',
                r'HttpClient\..*\([\'"]([^\'"]+)[\'"]',
            ],
            # URLs in strings
            'urls': [
                r'[\'"]https?://([^/\'"]+)([^\'"]+)[\'"]',
                r'[\'"]http://localhost[:]?\d*([^\'"]+)[\'"]',
                r'[\'"]127.0.0.1[:]?\d*([^\'"]+)[\'"]',
            ]
        }
        
        # Process all patterns
        for language, patterns in request_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Handle different match structures
                    url = None
                    
                    if isinstance(match, tuple):
                        if language == 'urls':
                            # URL pattern (domain, path)
                            host = match[0]
                            path = match[1] if len(match) > 1 else ''
                            url = f"http://{host}{path}"
                        elif len(match) == 2 and match[0] in ('get', 'post', 'put', 'delete', 'patch'):
                            # Method and URL
                            url = match[1]
                        else:
                            # Take the last part as the URL
                            url = match[-1]
                    else:
                        # Just a URL string
                        url = match
                    
                    # Make sure we have a URL
                    if not url:
                        continue
                    
                    # Filter out common non-service URLs
                    if self._is_likely_service_url(url):
                        service_call = {
                            'url': url,
                            'file': os.path.basename(file_path),
                            'language': language
                        }
                        service_calls.append(service_call)
        
        # Add unique service calls to project
        for call in service_calls:
            if call not in project['service_calls']:
                project['service_calls'].append(call)
    
    def _is_likely_service_url(self, url: Union[str, Tuple]) -> bool:
        """
        Filter out non-service URLs like CDNs, external APIs.
        
        Args:
            url: URL string or tuple
            
        Returns:
            bool: True if the URL is likely a service URL
        """
        if isinstance(url, tuple):
            url = url[0]
        
        url_str = str(url).lower()
        
        # Skip common external URLs and resources
        skip_domains = [
            'googleapis.com', 'amazonaws.com', 'github.com', 'gitlab.com',
            'cdn', 'fonts.', 'maps.', 'static.', 'assets.', 'images.', 'img.',
            'jquery', 'bootstrap', 'fontawesome', 'polyfill', 'gtag',
            '.png', '.jpg', '.gif', '.css', '.js', '.ico', '.svg', '.woff'
        ]
        
        for domain in skip_domains:
            if domain in url_str:
                return False
        
        # Look for internal service indicators
        service_indicators = [
            'api', 'service', 'srv', 'microservice', 'micro-service',
            'gateway', 'http://localhost', '127.0.0.1', 'internal', 'endpoint',
            '/v1/', '/v2/', '/v3/', '/rest/', '/graphql', 'grpc://'
        ]
        
        for indicator in service_indicators:
            if indicator in url_str:
                return True
        
        # Look for URL paths that suggest an API endpoint
        api_path_patterns = [
            r'/api/',
            r'/v\d+/',
            r'/services?/',
            r'/\w+/\w+/',  # Usually suggests resource/subresource pattern
            r'/graphql',
            r'/rest/'
        ]
        
        for pattern in api_path_patterns:
            if re.search(pattern, url_str):
                return True
                
        # By default, consider it not a service URL
        return False
    
    def _determine_endpoint_type(self, path: str) -> str:
        """
        Determine the type of API endpoint based on its path.
        
        Args:
            path: API endpoint path
            
        Returns:
            str: Endpoint type
        """
        path_lower = path.lower()
        
        # Health and status endpoints
        if any(term in path_lower for term in ['/health', '/ping', '/status', '/heartbeat', '/alive']):
            return 'health'
        
        # Metrics and monitoring endpoints
        elif any(term in path_lower for term in ['/metrics', '/stats', '/telemetry', '/monitor']):
            return 'metrics'
        
        # Authentication and authorization endpoints
        elif any(term in path_lower for term in ['/auth', '/login', '/token', '/oauth', '/session']):
            return 'auth'
        
        # Webhook and callback endpoints
        elif 'webhook' in path_lower or 'callback' in path_lower:
            return 'webhook'
        
        # Configuration endpoints
        elif any(term in path_lower for term in ['/config', '/settings', '/properties']):
            return 'config'
        
        # Admin endpoints
        elif '/admin' in path_lower:
            return 'admin'
        
        # Check if it's likely a REST resource by checking for path parameters
        # and resource-like structure
        elif re.search(r'(/\w+)(/\{[^}]+\}|/:\w+)?(/\w+)?', path):
            return 'resource'
        
        # Default to other if we can't determine
        else:
            return 'other'





###############
##  Part 3   ##
###############



class MicroserviceDetector(MicroserviceAnalyzer):
    """
    Main microservice detector class that handles service relationships and reporting.
    """
    
    def _detect_service_relationships(self) -> List[Dict[str, Any]]:
        """
        Detect relationships between services based on service calls.
        
        Returns:
            List[Dict]: List of service relationships
        """
        relationships = []
        
        # Map service URLs to projects
        service_map = self._build_service_map()
        
        # Detect calls between services
        for source_project in self.microservices:
            source_name = source_project['name']
            
            for call in source_project.get('service_calls', []):
                url = call.get('url')
                if not url:
                    continue
                
                # If it's a tuple, get the first element
                if isinstance(url, tuple):
                    url = url[0]
                
                # Skip if not a string (could happen with malformed URLs)
                if not isinstance(url, str):
                    continue
                    
                target_service = self._find_target_service(url, service_map, source_name)
                
                if target_service and target_service != source_name:
                    # Create relationship object
                    relationship = {
                        'source': source_name,
                        'target': target_service,
                        'type': self._determine_relationship_type(source_project, url),
                        'url': url,
                        'file': call.get('file', '')
                    }
                    
                    # Check if this relationship is already recorded
                    if not any(r['source'] == relationship['source'] and 
                              r['target'] == relationship['target'] and
                              r['type'] == relationship['type'] for r in relationships):
                        relationships.append(relationship)
        
        return relationships
    
    def _build_service_map(self) -> Dict[str, str]:
        """
        Build a map of service URLs to project names.
        
        Returns:
            Dict[str, str]: Map of URL patterns to service names
        """
        service_map = {}
        
        for project in self.microservices:
            project_name = project['name']
            
            # Map endpoints to this service
            for endpoint in project.get('service_endpoints', []):
                path = endpoint.get('path', '')
                
                if not path:
                    continue
                
                # Clean up path parameters
                clean_path = re.sub(r'[<{][^>}]+[>}]', '*', path)
                
                # Create possible URL patterns for this endpoint
                service_patterns = [
                    f"{project_name}{clean_path}",
                    f"{project_name.lower()}{clean_path}",
                    clean_path,
                    re.sub(r'^/', '', clean_path),  # Path without leading slash
                ]
                
                # Add domain-based patterns
                for domain in ['localhost', '127.0.0.1']:
                    service_patterns.append(f"{domain}/{project_name}{clean_path}")
                    service_patterns.append(f"{domain}{clean_path}")
                
                # Map each pattern to this service
                for pattern in service_patterns:
                    service_map[pattern] = project_name
            
            # Also map the service name itself
            service_map[project_name] = project_name
            service_map[project_name.lower()] = project_name
        
        return service_map
    
    def _find_target_service(self, url: str, service_map: Dict[str, str], source_name: str) -> Optional[str]:
        """
        Find the target service for a given URL.
        
        Args:
            url: URL to check
            service_map: Map of URL patterns to service names
            source_name: Name of the source service
            
        Returns:
            Optional[str]: Target service name or None
        """
        # Clean URL for matching
        url_lower = url.lower()
        
        # First try direct matching with the service map
        for pattern, service_name in service_map.items():
            if pattern in url_lower:
                return service_name
        
        # Try to extract service name from URL path
        url_parts = url_lower.split('/')
        for part in url_parts:
            if part in service_map:
                return service_map[part]
            
            # Check for service names with hyphens/underscores
            part_variants = [
                part,
                part.replace('-', ''),
                part.replace('_', ''),
                part.replace('-', '_'),
                part.replace('_', '-')
            ]
            
            for variant in part_variants:
                if variant in service_map:
                    return service_map[variant]
        
        # Try to extract service name from URL host
        if '://' in url:
            host = url.split('://', 1)[1].split('/', 1)[0].split(':', 1)[0]
            if host in service_map:
                return service_map[host]
            
            # Check subdomains
            domain_parts = host.split('.')
            for part in domain_parts:
                if part in service_map:
                    return service_map[part]
        
        # If all else fails, return None
        return None
    
    def _determine_relationship_type(self, source_project: Dict[str, Any], url: str) -> str:
        """
        Determine the type of relationship between services.
        
        Args:
            source_project: Source project dictionary
            url: URL of the service call
            
        Returns:
            str: Type of relationship (REST, gRPC, GraphQL, etc.)
        """
        # Check the communication type of the source project
        primary_communication = source_project.get('primary_communication', 'unknown')
        
        # If known, use it
        if primary_communication != 'unknown':
            if primary_communication == 'rest_api':
                return 'REST'
            elif primary_communication == 'grpc':
                return 'gRPC'
            elif primary_communication == 'graphql':
                return 'GraphQL'
            elif primary_communication == 'event_based':
                return 'Event-based'
            elif primary_communication == 'soap':
                return 'SOAP'
            elif primary_communication == 'websocket':
                return 'WebSocket'
        
        # Check the URL for clues
        url_lower = url.lower()
        if 'graphql' in url_lower:
            return 'GraphQL'
        elif 'grpc://' in url_lower:
            return 'gRPC'
        elif 'soap' in url_lower or 'wsdl' in url_lower:
            return 'SOAP'
        elif 'ws://' in url_lower or 'wss://' in url_lower:
            return 'WebSocket'
        
        # Default to REST for HTTP URLs
        if url_lower.startswith(('http://', 'https://')):
            return 'REST'
        
        # Default to HTTP for unknown communication types
        return 'HTTP'
    
    def _generate_microservice_report(self) -> str:
        """
        Generate a report of the microservice architecture.
        
        Returns:
            str: Path to the generated report
        """
        report_file = os.path.join(self.output_dir, 'microservice_report.md')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Microservice Architecture Analysis\n\n")
            f.write(f"*Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # List microservices
            f.write("## Detected Microservices\n\n")
            
            if not self.microservices:
                f.write("No microservices detected in the projects.\n\n")
            else:
                f.write("| Service | Confidence | Primary Communication | Endpoints | Service Calls |\n")
                f.write("|---------|------------|------------------------|-----------|---------------|\n")
                
                for service in sorted(self.microservices, key=lambda x: x['name']):
                    endpoints_count = len(service.get('service_endpoints', []))
                    service_calls_count = len(service.get('service_calls', []))
                    confidence = service.get('microservice_probability', 0) * 100
                    f.write(f"| {service['name']} | {confidence:.0f}% | {service.get('primary_communication', 'Unknown')} | {endpoints_count} | {service_calls_count} |\n")
                
                f.write("\n")
            
            # Service relationships
            if self.relationships:
                f.write("## Service Relationships\n\n")
                f.write("| Source | Target | Type | Reference |\n")
                f.write("|--------|--------|------|----------|\n")
                
                for rel in sorted(self.relationships, key=lambda x: (x['source'], x['target'])):
                    f.write(f"| {rel['source']} | {rel['target']} | {rel['type']} | {rel['file']} |\n")
                
                f.write("\n")
                
                # Generate mermaid diagram
                f.write("## Architecture Diagram\n\n")
                f.write("```mermaid\nflowchart TD\n")
                
                # Add nodes for each service
                for service in sorted(self.microservices, key=lambda x: x['name']):
                    service_name = service['name']
                    # Clean name for mermaid compatibility
                    mermaid_name = re.sub(r'[^a-zA-Z0-9]', '_', service_name)
                    f.write(f"    {mermaid_name}[\"{service_name}\"]\n")
                
                # Add relationships
                for i, rel in enumerate(sorted(self.relationships, key=lambda x: (x['source'], x['target']))):
                    source = re.sub(r'[^a-zA-Z0-9]', '_', rel['source'])
                    target = re.sub(r'[^a-zA-Z0-9]', '_', rel['target'])
                    
                    # Select arrow type based on relationship type
                    arrow_type = "-->"
                    if rel['type'] == 'Event-based':
                        arrow_type = "-.->|event|"
                    elif rel['type'] == 'gRPC':
                        arrow_type = "===>|gRPC|"
                    elif rel['type'] == 'GraphQL':
                        arrow_type = "--o|GraphQL|"
                    
                    f.write(f"    {source} {arrow_type} {target}\n")
                
                f.write("```\n\n")
            
            # Detailed service information
            f.write("## Service Details\n\n")
            
            for service in sorted(self.microservices, key=lambda x: x['name']):
                f.write(f"### {service['name']}\n\n")
                f.write(f"- **Path**: {service['path']}\n")
                f.write(f"- **Project Type**: {service['project_type']}\n")
                f.write(f"- **Primary Language**: {service.get('primary_language', 'Unknown')}\n")
                f.write(f"- **Microservice Probability**: {service['microservice_probability']*100:.0f}%\n")
                f.write(f"- **Communication Style**: {service.get('primary_communication', 'Unknown')}\n\n")
                
                # Microservice indicators
                if service.get('microservice_scores'):
                    f.write("#### Microservice Indicators\n\n")
                    for indicator, score in sorted(service['microservice_scores'].items(), key=lambda x: x[1], reverse=True):
                        f.write(f"- {indicator}: {score:.1f}\n")
                    f.write("\n")
                
                # API Endpoints
                if service.get('service_endpoints'):
                    f.write("#### API Endpoints\n\n")
                    f.write("| Method | Path | Type | File |\n")
                    f.write("|--------|------|------|------|\n")
                    
                    for endpoint in sorted(service.get('service_endpoints', []), key=lambda x: x.get('path', '')):
                        method = endpoint.get('method', 'UNKNOWN')
                        path = endpoint.get('path', '')
                        ep_type = endpoint.get('type', 'unknown')
                        file = endpoint.get('file', '')
                        f.write(f"| {method} | {path} | {ep_type} | {file} |\n")
                    
                    f.write("\n")
                
                # External Service Calls
                if service.get('service_calls'):
                    f.write("#### External Service Calls\n\n")
                    f.write("| URL | Target Service | File |\n")
                    f.write("|-----|---------------|------|\n")
                    
                    for call in sorted(service.get('service_calls', []), key=lambda x: str(x.get('url', ''))):
                        url = call.get('url', '')
                        if isinstance(url, tuple):
                            url = url[0]
                        
                        # Find target service
                        target = "Unknown"
                        for rel in self.relationships:
                            if rel['source'] == service['name'] and rel['url'] == url:
                                target = rel['target']
                                break
                        
                        file = call.get('file', '')
                        f.write(f"| {url} | {target} | {file} |\n")
                    
                    f.write("\n")
        
        # Also generate HTML version
        html_file = os.path.join(self.output_dir, 'microservice_report.html')
        
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
                    <title>Microservice Architecture Analysis</title>
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
                        
                        /* Mermaid diagram styling */
                        .mermaid {{
                            background-color: var(--secondary-bg);
                            padding: 20px;
                            border-radius: 8px;
                            text-align: center;
                            margin: 20px 0;
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
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/9.3.0/mermaid.min.js"></script>
                    <script>
                        document.addEventListener('DOMContentLoaded', function() {{
                            mermaid.initialize({{
                                theme: 'dark', 
                                startOnLoad: true,
                                securityLevel: 'loose'
                            }});
                        }});
                    </script>
                </head>
                <body>
                    {html_content}
                </body>
                </html>
                """)
        
        self.logger.info(f"Microservice report generated: {report_file}")
        return report_file



