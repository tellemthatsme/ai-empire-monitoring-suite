import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any
from metrics import AGENTS_GAUGE, TASKS_GAUGE, COMPLETED_TASKS_COUNTER

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Agent:
    """Represents an agent in the multi-agent system."""

    def __init__(self, name: str, capabilities: List[str]):
        """Initializes an Agent.

        Args:
            name: The name of the agent.
            capabilities: A list of capabilities that the agent has.
        """
        self.name = name
        self.capabilities = capabilities
        self.status = "idle"
        self.current_task = None
        self.last_updated = datetime.now().isoformat()

    def assign_task(self, task: Dict[str, Any]):
        """Assigns a task to this agent.

        Args:
            task: The task to assign.
        """
        self.current_task = task
        self.status = "working"
        self.last_updated = datetime.now().isoformat()
        logging.info(f"Agent {self.name} assigned task: {task['name']}")

    def complete_task(self):
        """Marks the current task as complete."""
        if self.current_task:
            logging.info(f"Agent {self.name} completed task: {self.current_task['name']}")
            self.current_task = None
            self.status = "idle"
            self.last_updated = datetime.now().isoformat()
            COMPLETED_TASKS_COUNTER.inc()

    def get_status(self) -> Dict[str, Any]:
        """Gets the current status of the agent.

        Returns:
            A dictionary containing the agent's status.
        """
        return {
            "name": self.name,
            "status": self.status,
            "current_task": self.current_task,
            "last_updated": self.last_updated
        }

class MultiAgentOrchestrator:
    """Orchestrates multiple agents to perform tasks."""

    def __init__(self, config_file="enhanced_orchestration_config.json"):
        """Initializes the MultiAgentOrchestrator.

        Args:
            config_file: The path to the configuration file.
        """
        self.config_file = config_file
        self.agents: List[Agent] = []
        self.tasks: List[Dict[str, Any]] = []
        self.load_configuration()
        self.initialize_agents()

    def load_configuration(self):
        """Loads the orchestration configuration from a file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                logging.warning(f"Configuration file not found at {self.config_file}. Creating a default configuration.")
                self.config = self._get_default_config()
                self.save_configuration()
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from {self.config_file}. Using default configuration.")
            self.config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Returns the default configuration.

        Returns:
            A dictionary containing the default configuration.
        """
        return {
            "agents": [
                {"name": "DocumentationAgent", "capabilities": ["create_documentation", "update_templates"]},
                {"name": "CodeReviewAgent", "capabilities": ["review_code", "enforce_standards"]},
                {"name": "TestingAgent", "capabilities": ["create_tests", "run_tests", "analyze_coverage"]},
                {"name": "MonitoringAgent", "capabilities": ["monitor_performance", "log_metrics"]}
            ],
            "task_priorities": {
                "immediate": ["create_documentation_framework", "establish_code_review_process"],
                "short_term": ["implement_basic_testing", "setup_performance_monitoring"],
                "medium_term": ["expand_documentation", "formalize_code_review", "improve_test_coverage"]
            },
            "capability_map": {
                "create_documentation_framework": "create_documentation",
                "establish_code_review_process": "review_code",
                "implement_basic_testing": "create_tests",
                "setup_performance_monitoring": "monitor_performance"
            }
        }

    def save_configuration(self):
        """Saves the orchestration configuration to a file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            logging.error(f"Error saving configuration to {self.config_file}: {e}")

    def initialize_agents(self):
        """Initializes agents based on the configuration."""
        for agent_config in self.config.get("agents", []):
            agent = Agent(agent_config["name"], agent_config["capabilities"])
            self.agents.append(agent)
        logging.info(f"Initialized {len(self.agents)} agents")
        AGENTS_GAUGE.set(len(self.agents))

    def add_task(self, task: Dict[str, Any]):
        """Adds a task to the task queue.

        Args:
            task: The task to add.
        """
        self.tasks.append(task)
        logging.info(f"Added task: {task['name']}")
        TASKS_GAUGE.inc()

    def get_available_agent(self, required_capability: str) -> Agent | None:
        """Gets an available agent with the required capability.

        Args:
            required_capability: The capability required for the task.

        Returns:
            An available agent, or None if no agent is available.
        """
        for agent in self.agents:
            if agent.status == "idle" and required_capability in agent.capabilities:
                return agent
        return None

    def orchestrate(self):
        """Runs the main orchestration loop."""
        logging.info("Starting multi-agent orchestration...")
        self._add_priority_tasks()
        self._assign_tasks()
        self.report_status()

    def _add_priority_tasks(self):
        """Adds priority tasks to the task queue."""
        for task_name in self.config.get("task_priorities", {}).get("immediate", []):
            task = {
                "name": task_name,
                "priority": "immediate",
                "status": "pending"
            }
            self.add_task(task)

    def _assign_tasks(self):
        """Assigns pending tasks to available agents."""
        capability_map = self.config.get("capability_map", {})
        for task in self.tasks:
            if task["status"] == "pending":
                required_capability = capability_map.get(task["name"])
                if required_capability:
                    agent = self.get_available_agent(required_capability)
                    if agent:
                        agent.assign_task(task)
                        task["status"] = "assigned"
                        task["assigned_agent"] = agent.name
                    else:
                        logging.warning(f"No available agent for task: {task['name']}")
                else:
                    logging.warning(f"Unknown capability for task: {task['name']}")

    def report_status(self):
        """Reports the status of all agents and tasks."""
        logging.info("\n=== Agent Status Report ===")
        for agent in self.agents:
            status = agent.get_status()
            logging.info(f"Agent: {status['name']}")
            logging.info(f"  Status: {status['status']}")
            logging.info(f"  Current Task: {status['current_task']['name'] if status['current_task'] else 'None'}")
            logging.info(f"  Last Updated: {status['last_updated']}")

        logging.info("\n=== Task Status Report ===")
        for task in self.tasks:
            logging.info(f"Task: {task['name']}")
            logging.info(f"  Priority: {task['priority']}")
            logging.info(f"  Status: {task['status']}")
            logging.info(f"  Assigned Agent: {task.get('assigned_agent', 'None')}")

def main():
    """Initializes and runs the orchestrator."""
    orchestrator = MultiAgentOrchestrator()
    orchestrator.orchestrate()

if __name__ == "__main__":
    main()
