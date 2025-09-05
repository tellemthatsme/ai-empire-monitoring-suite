import json
import os
import subprocess
from datetime import datetime

class MonitoringAgent:
    def __init__(self):
        self.name = "MonitoringAgent"
        self.capabilities = ["monitor_performance", "log_metrics", "alert_on_issues", "generate_reports"]
        self.status = "idle"
        self.current_task = None
        self.last_updated = datetime.now().isoformat()
    
    def assign_task(self, task):
        """Assign a task to this agent."""
        self.current_task = task
        self.status = "working"
        self.last_updated = datetime.now().isoformat()
        print(f"[{self.name}] Assigned task: {task['name']}")
        
        # Process the task based on its name
        if task["name"] == "setup_performance_monitoring":
            self.setup_performance_monitoring()
        elif task["name"] == "implement_performance_monitoring":
            self.implement_performance_monitoring()
    
    def setup_performance_monitoring(self):
        """Set up basic logging for key components to track performance."""
        print(f"[{self.name}] Setting up performance monitoring...")
        
        # Create a monitoring directory
        if not os.path.exists("monitoring"):
            os.makedirs("monitoring")
        
        # Create a basic logging configuration
        log_config = """[loggers]
keys=root

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=INFO
formatter=simpleFormatter
args=('monitoring/app.log',)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=
"""
        
        with open("monitoring/logging.conf", "w") as f:
            f.write(log_config)
        
        # Create a simple performance monitoring script
        monitor_script = """import logging
import logging.config
import time
import psutil
import json
from datetime import datetime

# Load logging configuration
logging.config.fileConfig('monitoring/logging.conf')
logger = logging.getLogger()

def monitor_system():
    # Get system metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Create a metrics dictionary
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'disk_percent': (disk.used / disk.total) * 100,
        'memory_available': memory.available,
        'disk_available': disk.free
    }
    
    # Log the metrics
    logger.info(f"System Metrics: {json.dumps(metrics)}")
    
    # Check for alerts
    if cpu_percent > 80:
        logger.warning(f"High CPU usage: {cpu_percent}%")
    
    if memory.percent > 80:
        logger.warning(f"High memory usage: {memory.percent}%")
    
    if (disk.used / disk.total) > 0.8:
        logger.warning(f"Low disk space: {(disk.used / disk.total) * 100}% used")
    
    return metrics

def monitor_application():
    # This is a placeholder for application-specific monitoring
    # In a real implementation, you would monitor your application's specific metrics
    logger.info("Application monitoring placeholder")

if __name__ == "__main__":
    logger.info("Starting performance monitoring")
    
    try:
        while True:
            system_metrics = monitor_system()
            monitor_application()
            # Wait for 60 seconds before the next check
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Stopping performance monitoring")
"""
        
        with open("monitoring/performance_monitor.py", "w") as f:
            f.write(monitor_script)
        
        # Create a metrics dashboard template
        dashboard_template = """# Performance Metrics Dashboard

## System Metrics
| Metric | Value | Status |
|--------|-------|--------|
| CPU Usage | {cpu_percent}% | {cpu_status} |
| Memory Usage | {memory_percent}% | {memory_status} |
| Disk Usage | {disk_percent}% | {disk_status} |

## Application Metrics
| Component | Requests/sec | Avg Response Time | Error Rate |
|-----------|--------------|------------------|------------|
| API | - | - | - |
| Database | - | - | - |
| Cache | - | - | - |

## Alerts
{alerts}

## Historical Data
![Performance Trend](performance_trend.png)

*Note: This is a template. In a real implementation, this would be populated with live data.*
"""
        
        with open("monitoring/DASHBOARD_TEMPLATE.md", "w") as f:
            f.write(dashboard_template)
        
        # Create a monitoring report template
        monitor_report = """# Monitoring Report

## Report Period
From: 
To: 

## System Health
- Overall Status: 
- Peak CPU Usage: 
- Peak Memory Usage: 
- Disk Space Remaining: 

## Application Performance
- Uptime: 
- Average Response Time: 
- Error Rate: 

## Issues Detected
1. 
2. 
3. 

## Recommendations
"""
        
        with open("monitoring/MONITORING_REPORT_TEMPLATE.md", "w") as f:
            f.write(monitor_report)
        
        print(f"[{self.name}] Performance monitoring setup completed successfully.")
        self.complete_task()
    
    def implement_performance_monitoring(self):
        """Implement performance monitoring in the application."""
        print(f"[{self.name}] Implementing performance monitoring...")
        
        # Create a more comprehensive monitoring script
        monitor_script = """import logging
import logging.config
import time
import psutil
import json
import os
from datetime import datetime

# Load logging configuration
if os.path.exists('monitoring/logging.conf'):
    logging.config.fileConfig('monitoring/logging.conf')
else:
    # Fallback to basic configuration
    logging.basicConfig(level=logging.INFO)
    
logger = logging.getLogger()

class PerformanceMonitor:
    def __init__(self, config_file='monitoring/monitor_config.json'):
        self.config = self.load_config(config_file)
        self.metrics_history = []
    
    def load_config(self, config_file):
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "monitoring_interval": 60,
                "alert_thresholds": {
                    "cpu_percent": 80,
                    "memory_percent": 80,
                    "disk_percent": 80
                }
            }
    
    def monitor_system(self):
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Create a metrics dictionary
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': (disk.used / disk.total) * 100,
            'memory_available': memory.available,
            'disk_available': disk.free
        }
        
        # Add to history
        self.metrics_history.append(metrics)
        
        # Keep only the last 100 metrics
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
        
        # Log the metrics
        logger.info(f"System Metrics: {json.dumps(metrics)}")
        
        # Check for alerts
        self.check_alerts(metrics)
        
        return metrics
    
    def check_alerts(self, metrics):
        thresholds = self.config.get('alert_thresholds', {})
        
        if metrics['cpu_percent'] > thresholds.get('cpu_percent', 80):
            logger.warning(f"High CPU usage: {metrics['cpu_percent']}%")
        
        if metrics['memory_percent'] > thresholds.get('memory_percent', 80):
            logger.warning(f"High memory usage: {metrics['memory_percent']}%")
        
        if metrics['disk_percent'] > thresholds.get('disk_percent', 80):
            logger.warning(f"Low disk space: {metrics['disk_percent']}% used")
    
    def monitor_application(self):
        # This is a placeholder for application-specific monitoring
        # In a real implementation, you would monitor your application's specific metrics
        logger.info("Application monitoring placeholder")
    
    def generate_report(self):
        if not self.metrics_history:
            return "No metrics data available"
        
        # Generate a simple report
        latest = self.metrics_history[-1]
        report = f"# Performance Report\nGenerated at: {latest['timestamp']}\n\n## System Metrics\n- CPU Usage: {latest['cpu_percent']}%\n- Memory Usage: {latest['memory_percent']}%\n- Disk Usage: {latest['disk_percent']}%\n\n## Historical Data Points\nTotal data points: {len(self.metrics_history)}\n"
        
        return report

def main():
    logger.info("Starting performance monitoring")
    
    monitor = PerformanceMonitor()
    
    try:
        while True:
            system_metrics = monitor.monitor_system()
            monitor.monitor_application()
            
            # Every 10 iterations, generate a report
            if len(monitor.metrics_history) % 10 == 0:
                report = monitor.generate_report()
                logger.info(f"Performance Report:
{report}")
            
            # Wait for the configured interval before the next check
            time.sleep(monitor.config.get('monitoring_interval', 60))
    except KeyboardInterrupt:
        logger.info("Stopping performance monitoring")

if __name__ == "__main__":
    main()
"""
        
        with open("monitoring/performance_monitor.py", "w") as f:
            f.write(monitor_script)
        
        # Create a monitoring configuration file
        monitor_config = {
            "monitoring_interval": 60,
            "alert_thresholds": {
                "cpu_percent": 80,
                "memory_percent": 80,
                "disk_percent": 80
            }
        }
        
        with open("monitoring/monitor_config.json", "w") as f:
            json.dump(monitor_config, f, indent=2)
        
        print(f"[{self.name}] Performance monitoring implemented successfully.")
        self.complete_task()
    
    def complete_task(self):
        """Mark the current task as complete."""
        if self.current_task:
            print(f"[{self.name}] Completed task: {self.current_task['name']}")
            self.current_task = None
            self.status = "idle"
            self.last_updated = datetime.now().isoformat()

def main():
    # Create and run the Monitoring Agent
    agent = MonitoringAgent()
    
    # Example task (in a real scenario, this would come from the orchestrator)
    task = {
        "name": "implement_performance_monitoring",
        "priority": "medium_term",
        "status": "pending"
    }
    
    agent.assign_task(task)

if __name__ == "__main__":
    main()