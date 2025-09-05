#!/usr/bin/env python3
"""
COMPREHENSIVE PROJECT AUDITOR
OpenRouter-integrated multi-agent audit system for practical project testing
"""

import json
import os
import sys
import subprocess
import time
import asyncio
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import traceback
from pathlib import Path
from secure_api_manager import api_manager

# Import the agents
try:
    from CodeReviewAgent import CodeReviewAgent
    from TestingAgent import TestingAgent
    from MonitoringAgent import MonitoringAgent
    from DocumentationAgent import DocumentationAgent
    from ENHANCED_MULTI_AGENT_ORCHESTRATOR import EnhancedMultiAgentOrchestrator
except ImportError as e:
    print(f"Warning: Could not import agent: {e}")

@dataclass
class AuditFinding:
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "functionality", "dependencies", "security", "performance", "documentation"
    description: str
    file_path: str
    line_number: Optional[int] = None
    recommendation: str = ""
    estimated_fix_time: str = "1-2 hours"

@dataclass
class ProjectStatus:
    name: str
    path: str
    is_executable: bool
    has_dependencies: bool
    has_tests: bool
    has_documentation: bool
    last_modified: str
    size_bytes: int
    findings: List[AuditFinding]
    completion_status: str  # "complete", "incomplete", "broken", "untested"

class OpenRouterClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = api_manager.get_base_url('openrouter')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def test_connection(self):
        """Test the OpenRouter API connection"""
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers, timeout=10)
            if response.status_code == 200:
                models = response.json()
                free_models = [m for m in models.get('data', []) if m.get('pricing', {}).get('prompt', 0) == 0]
                return True, f"Connected successfully. Found {len(free_models)} free models available."
            else:
                return False, f"API Error: {response.status_code} - {response.text}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def analyze_code(self, code: str, file_path: str, analysis_type: str = "comprehensive"):
        """Use OpenRouter to analyze code for issues"""
        try:
            prompt = f"""Analyze the following {analysis_type} for the file {file_path}:

{code}

Please provide a JSON response with:
1. "issues": List of potential problems (bugs, security, performance)
2. "completeness": Assessment of whether code appears complete or incomplete
3. "dependencies": Any missing dependencies or imports
4. "suggestions": Specific recommendations for improvements
5. "severity_score": Overall severity from 1-10 (10 being most critical)

Focus on practical issues that would prevent the code from working properly."""

            payload = {
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(f"{self.base_url}/chat/completions", 
                                   headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                try:
                    return json.loads(content)
                except:
                    return {"analysis": content, "parsed": False}
            else:
                return {"error": f"API Error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

class ComprehensiveProjectAuditor:
    def __init__(self, openrouter_api_key: str):
        self.openrouter = OpenRouterClient(openrouter_api_key)
        self.project_root = Path.cwd()
        self.agents = {}
        self.audit_results = {}
        self.findings = []
        self.project_statuses = []
        
        # Initialize agents
        try:
            self.agents = {
                "code_review": CodeReviewAgent(),
                "testing": TestingAgent(),
                "monitoring": MonitoringAgent(),
                "documentation": DocumentationAgent()
            }
        except Exception as e:
            print(f"Warning: Could not initialize all agents: {e}")
    
    def run_comprehensive_audit(self):
        """Run comprehensive project audit"""
        print("COMPREHENSIVE PROJECT AUDITOR")
        print("=" * 80)
        print(f"Starting audit at: {datetime.now()}")
        print(f"Project root: {self.project_root}")
        
        # Test OpenRouter connection
        success, message = self.openrouter.test_connection()
        print(f"OpenRouter Status: {'OK' if success else 'FAIL'} {message}")
        
        if not success:
            print("WARNING: OpenRouter connection failed. Proceeding with local analysis only.")
        
        # Phase 1: Discover and categorize files
        print("\nPhase 1: Project Discovery")
        print("-" * 40)
        python_files = self.discover_python_files()
        print(f"Found {len(python_files)} Python files to analyze")
        
        # Phase 2: Analyze each file
        print("\nPhase 2: File Analysis")
        print("-" * 40)
        for file_path in python_files:
            self.analyze_file(file_path)
        
        # Phase 3: Test functionality
        print("\nPhase 3: Functionality Testing")
        print("-" * 40)
        self.test_file_functionality()
        
        # Phase 4: Check dependencies
        print("\nPhase 4: Dependency Analysis")
        print("-" * 40)
        self.analyze_dependencies()
        
        # Phase 5: Generate report
        print("\nPhase 5: Report Generation")
        print("-" * 40)
        report = self.generate_audit_report()
        
        return report
    
    def discover_python_files(self):
        """Discover all Python files in the project"""
        python_files = []
        
        # Get all .py files, excluding common directories to ignore
        ignore_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', 'node_modules'}
        
        for root, dirs, files in os.walk(self.project_root):
            # Remove ignore directories from dirs list
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    file_path = Path(root) / file
                    python_files.append(file_path)
        
        return sorted(python_files)
    
    def analyze_file(self, file_path: Path):
        """Analyze a specific file for issues"""
        try:
            print(f"Analyzing: {file_path.name}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic analysis
            findings = []
            file_size = os.path.getsize(file_path)
            last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            # Check for obvious issues
            if len(content.strip()) == 0:
                findings.append(AuditFinding(
                    severity="high",
                    category="functionality",
                    description="File is empty",
                    file_path=str(file_path),
                    recommendation="Add implementation or remove file"
                ))
            
            # Check for incomplete functions
            if "TODO" in content or "FIXME" in content or "pass" in content:
                findings.append(AuditFinding(
                    severity="medium",
                    category="functionality",
                    description="File contains TODO/FIXME comments or placeholder implementations",
                    file_path=str(file_path),
                    recommendation="Complete implementation"
                ))
            
            # Check for imports
            has_imports = "import " in content
            if not has_imports and len(content) > 100:
                findings.append(AuditFinding(
                    severity="low",
                    category="dependencies",
                    description="No imports found in substantial file",
                    file_path=str(file_path),
                    recommendation="Review if imports are needed"
                ))
            
            # Try syntax check
            try:
                compile(content, str(file_path), 'exec')
            except SyntaxError as e:
                findings.append(AuditFinding(
                    severity="critical",
                    category="functionality",
                    description=f"Syntax error: {str(e)}",
                    file_path=str(file_path),
                    line_number=e.lineno,
                    recommendation="Fix syntax error"
                ))
            
            # OpenRouter analysis (if available)
            if len(content) > 50:  # Only analyze substantial files
                success, _ = self.openrouter.test_connection()
                if success:
                    analysis = self.openrouter.analyze_code(content, str(file_path))
                    if "error" not in analysis and "issues" in analysis:
                        for issue in analysis.get("issues", []):
                            findings.append(AuditFinding(
                                severity="medium",
                                category="functionality",
                                description=f"AI Analysis: {issue}",
                                file_path=str(file_path),
                                recommendation="Review and address AI-identified issue"
                            ))
            
            # Determine completion status
            completion_status = "complete"
            if any(f.severity == "critical" for f in findings):
                completion_status = "broken"
            elif any("TODO" in f.description or "incomplete" in f.description.lower() for f in findings):
                completion_status = "incomplete"
            elif not findings:
                completion_status = "complete"
            else:
                completion_status = "incomplete"
            
            # Create project status
            project_status = ProjectStatus(
                name=file_path.name,
                path=str(file_path),
                is_executable=content.startswith('#!/'),
                has_dependencies=has_imports,
                has_tests=False,  # Will be updated later
                has_documentation="\"\"\"" in content or "'''" in content,
                last_modified=last_modified.isoformat(),
                size_bytes=file_size,
                findings=findings,
                completion_status=completion_status
            )
            
            self.project_statuses.append(project_status)
            self.findings.extend(findings)
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            error_finding = AuditFinding(
                severity="high",
                category="functionality",
                description=f"Could not analyze file: {str(e)}",
                file_path=str(file_path),
                recommendation="Investigate file access or encoding issues"
            )
            self.findings.append(error_finding)
    
    def test_file_functionality(self):
        """Test if files can be imported and basic functionality works"""
        print("Testing file functionality...")
        
        for status in self.project_statuses:
            if status.completion_status != "broken":
                try:
                    # Try to import the module
                    file_path = Path(status.path)
                    if file_path.name.endswith('.py') and file_path.name != '__init__.py':
                        module_name = file_path.stem
                        
                        # Simple import test
                        import_cmd = f"python -c \"import {module_name}; print('Import successful')\""
                        result = subprocess.run(import_cmd, shell=True, capture_output=True, text=True, timeout=10)
                        
                        if result.returncode != 0:
                            finding = AuditFinding(
                                severity="high",
                                category="functionality",
                                description=f"Import failed: {result.stderr.strip()}",
                                file_path=status.path,
                                recommendation="Fix import errors and dependencies"
                            )
                            status.findings.append(finding)
                            self.findings.append(finding)
                            if status.completion_status == "complete":
                                status.completion_status = "broken"
                        else:
                            print(f"OK {status.name} imports successfully")
                            
                except subprocess.TimeoutExpired:
                    finding = AuditFinding(
                        severity="medium",
                        category="performance",
                        description="Import test timed out",
                        file_path=status.path,
                        recommendation="Check for infinite loops or blocking operations on import"
                    )
                    status.findings.append(finding)
                    self.findings.append(finding)
                except Exception as e:
                    finding = AuditFinding(
                        severity="medium",
                        category="functionality",
                        description=f"Could not test import: {str(e)}",
                        file_path=status.path,
                        recommendation="Manual testing required"
                    )
                    status.findings.append(finding)
                    self.findings.append(finding)
    
    def analyze_dependencies(self):
        """Analyze project dependencies"""
        print("Analyzing dependencies...")
        
        # Check for requirements.txt
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    requirements = f.read().strip().split('\n')
                print(f"Found requirements.txt with {len(requirements)} dependencies")
                
                # Check if requirements are installed
                for req in requirements:
                    if req.strip() and not req.startswith('#'):
                        package = req.split('==')[0].split('>=')[0].split('<=')[0].strip()
                        try:
                            __import__(package)
                        except ImportError:
                            finding = AuditFinding(
                                severity="high",
                                category="dependencies",
                                description=f"Required package not installed: {package}",
                                file_path="requirements.txt",
                                recommendation=f"Install package: pip install {package}"
                            )
                            self.findings.append(finding)
            except Exception as e:
                finding = AuditFinding(
                    severity="medium",
                    category="dependencies",
                    description=f"Could not process requirements.txt: {str(e)}",
                    file_path="requirements.txt",
                    recommendation="Review requirements.txt format"
                )
                self.findings.append(finding)
        else:
            # Look for common imports that might be missing
            common_packages = ['requests', 'numpy', 'pandas', 'flask', 'django', 'fastapi', 'psutil']
            missing_packages = []
            
            for package in common_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                finding = AuditFinding(
                    severity="low",
                    category="dependencies",
                    description=f"Common packages not available: {', '.join(missing_packages)}",
                    file_path="project",
                    recommendation="Consider creating requirements.txt if these packages are needed"
                )
                self.findings.append(finding)
    
    def generate_audit_report(self):
        """Generate comprehensive audit report"""
        print("Generating audit report...")
        
        # Categorize findings by severity
        critical_findings = [f for f in self.findings if f.severity == "critical"]
        high_findings = [f for f in self.findings if f.severity == "high"]
        medium_findings = [f for f in self.findings if f.severity == "medium"]
        low_findings = [f for f in self.findings if f.severity == "low"]
        
        # Categorize projects by status
        broken_projects = [p for p in self.project_statuses if p.completion_status == "broken"]
        incomplete_projects = [p for p in self.project_statuses if p.completion_status == "incomplete"]
        complete_projects = [p for p in self.project_statuses if p.completion_status == "complete"]
        
        # Calculate metrics
        total_files = len(self.project_statuses)
        total_findings = len(self.findings)
        
        report = {
            "audit_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_files_analyzed": total_files,
                "total_findings": total_findings,
                "critical_issues": len(critical_findings),
                "high_priority_issues": len(high_findings),
                "medium_priority_issues": len(medium_findings),
                "low_priority_issues": len(low_findings)
            },
            "project_status_overview": {
                "broken_projects": len(broken_projects),
                "incomplete_projects": len(incomplete_projects),
                "complete_projects": len(complete_projects),
                "completion_percentage": round((len(complete_projects) / total_files * 100), 2) if total_files > 0 else 0
            },
            "critical_issues": [asdict(f) for f in critical_findings],
            "high_priority_issues": [asdict(f) for f in high_findings],
            "broken_projects_detail": [
                {
                    "name": p.name,
                    "path": p.path,
                    "issues": [asdict(f) for f in p.findings if f.severity in ["critical", "high"]]
                } 
                for p in broken_projects
            ],
            "incomplete_projects_detail": [
                {
                    "name": p.name,
                    "path": p.path,
                    "completion_status": p.completion_status,
                    "key_issues": [f.description for f in p.findings if f.severity in ["medium", "high"]]
                }
                for p in incomplete_projects
            ],
            "recommendations": {
                "immediate_actions": [
                    f.recommendation for f in critical_findings + high_findings
                ],
                "priority_completion_order": [
                    {
                        "project": p.name,
                        "priority": "high" if p.completion_status == "broken" else "medium",
                        "estimated_effort": "2-4 hours" if len(p.findings) <= 3 else "1-2 days",
                        "key_issues": [f.description for f in p.findings[:3]]
                    }
                    for p in broken_projects + incomplete_projects
                ]
            },
            "detailed_findings": [asdict(f) for f in self.findings],
            "project_details": [asdict(p) for p in self.project_statuses]
        }
        
        # Save report
        report_file = self.project_root / f"COMPREHENSIVE_AUDIT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Audit report saved to: {report_file}")
        
        # Print summary
        self.print_audit_summary(report)
        
        return report
    
    def print_audit_summary(self, report):
        """Print audit summary to console"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE PROJECT AUDIT REPORT")
        print("=" * 80)
        
        summary = report["audit_summary"]
        status = report["project_status_overview"]
        
        print(f"Files Analyzed: {summary['total_files_analyzed']}")
        print(f"Total Issues Found: {summary['total_findings']}")
        print(f"Project Completion: {status['completion_percentage']}%")
        
        print(f"\nIssue Breakdown:")
        print(f"  Critical: {summary['critical_issues']}")
        print(f"  High:     {summary['high_priority_issues']}")
        print(f"  Medium:   {summary['medium_priority_issues']}")
        print(f"  Low:      {summary['low_priority_issues']}")
        
        print(f"\nProject Status:")
        print(f"  Complete:   {status['complete_projects']}")
        print(f"  Incomplete: {status['incomplete_projects']}")
        print(f"  Broken:     {status['broken_projects']}")
        
        if report["broken_projects_detail"]:
            print(f"\nBROKEN PROJECTS (Immediate attention required):")
            for project in report["broken_projects_detail"][:5]:
                print(f"  • {project['name']}")
                for issue in project['issues'][:2]:
                    print(f"    - {issue['description']}")
        
        if report["incomplete_projects_detail"]:
            print(f"\nINCOMPLETE PROJECTS (Needs completion):")
            for project in report["incomplete_projects_detail"][:5]:
                print(f"  • {project['name']}")
                for issue in project['key_issues'][:2]:
                    print(f"    - {issue}")
        
        print(f"\nNEXT ACTIONS:")
        for i, action in enumerate(report["recommendations"]["immediate_actions"][:5], 1):
            print(f"  {i}. {action}")
        
        print("=" * 80)

def main():
    """Main execution function"""
    # OpenRouter API key
    api_key = api_manager.get_api_key('openrouter')
    
    # Create auditor
    auditor = ComprehensiveProjectAuditor(api_key)
    
    # Run comprehensive audit
    try:
        report = auditor.run_comprehensive_audit()
        
        print(f"\nAudit completed successfully!")
        print(f"Report saved with {len(auditor.findings)} total findings")
        
        return report
        
    except Exception as e:
        print(f"Audit failed with error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    report = main()