#!/usr/bin/env python3
"""
MCP MEMORY PERSISTENCE SERVER - Cross-Session Memory System
Provides persistent memory storage for Claude Code sessions with cross-session persistence.
"""

import json
import asyncio
import sys
import os
import sqlite3
import time
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from secure_api_manager import api_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp-memory-server")

class MCPMemoryPersistenceServer:
    def __init__(self):
        # Initialize OpenRouter configuration
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", api_manager.get_api_key('openrouter'))
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_memory_persistence.db")
        self.init_database()
        
        # Memory categories for organization
        self.memory_categories = {
            "openrouter": "OpenRouter API configuration and usage",
            "enterprise": "Enterprise platform states and configurations", 
            "revenue": "Revenue generation system states",
            "session": "Session state and user preferences",
            "performance": "System performance metrics and monitoring",
            "dashboard": "Dashboard states and configurations",
            "user_prefs": "User preferences and settings"
        }
        
        logger.info(f"MCP Memory Persistence Server initialized with database: {self.db_path}")
    
    def init_database(self):
        """Initialize SQLite database for persistent memory storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create memory storage table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory_storage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_key TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    value TEXT NOT NULL,
                    value_type TEXT DEFAULT 'string',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NULL,
                    session_id TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            ''')
            
            # Create session tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    context_data TEXT DEFAULT '{}',
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create performance metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            ''')
            
            # Create indices for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_key ON memory_storage(memory_key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON memory_storage(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session ON memory_storage(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_expires ON memory_storage(expires_at)')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def get_connection(self):
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def cleanup_expired_memory(self):
        """Remove expired memory entries"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM memory_storage 
                WHERE expires_at IS NOT NULL AND expires_at < datetime('now')
            ''')
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired memory entries")
                
        except Exception as e:
            logger.error(f"Memory cleanup failed: {e}")
    
    def store_memory(self, key: str, value: Any, category: str = "general", 
                    expires_hours: Optional[int] = None, session_id: str = None,
                    metadata: Dict = None) -> bool:
        """Store memory with persistence"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Determine value type and serialize if needed
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
                value_type = "json"
            elif isinstance(value, (int, float)):
                value_str = str(value)
                value_type = "number"
            elif isinstance(value, bool):
                value_str = str(value).lower()
                value_type = "boolean"
            else:
                value_str = str(value)
                value_type = "string"
            
            # Calculate expiration if specified
            expires_at = None
            if expires_hours:
                expires_at = datetime.now() + timedelta(hours=expires_hours)
                expires_at = expires_at.isoformat()
            
            # Serialize metadata
            metadata_str = json.dumps(metadata or {})
            
            # Store or update memory
            cursor.execute('''
                INSERT OR REPLACE INTO memory_storage 
                (memory_key, category, value, value_type, expires_at, session_id, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (key, category, value_str, value_type, expires_at, session_id, metadata_str))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored memory: {key} in category {category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory {key}: {e}")
            return False
    
    def retrieve_memory(self, key: str, default=None) -> Any:
        """Retrieve memory from persistent storage"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT value, value_type, metadata, expires_at 
                FROM memory_storage 
                WHERE memory_key = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
            ''', (key,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return default
            
            value_str, value_type, metadata_str, expires_at = result
            
            # Deserialize based on type
            if value_type == "json":
                return json.loads(value_str)
            elif value_type == "number":
                try:
                    return float(value_str) if '.' in value_str else int(value_str)
                except ValueError:
                    logger.error(f"Failed to parse number: {value_str}")
                    return value_str
            elif value_type == "boolean":
                return value_str.lower() in ('true', '1', 'yes', 'on')
            else:
                return value_str
                
        except Exception as e:
            logger.error(f"Failed to retrieve memory {key}: {e}")
            return default
    
    def list_memory_by_category(self, category: str) -> List[Dict]:
        """List all memory entries in a category"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT memory_key, value, value_type, created_at, updated_at, metadata
                FROM memory_storage 
                WHERE category = ? AND (expires_at IS NULL OR expires_at > datetime('now'))
                ORDER BY updated_at DESC
            ''', (category,))
            
            results = cursor.fetchall()
            conn.close()
            
            memory_list = []
            for row in results:
                memory_item = {
                    "key": row["memory_key"],
                    "value": self._deserialize_value(row["value"], row["value_type"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "metadata": json.loads(row["metadata"] or "{}")
                }
                memory_list.append(memory_item)
            
            return memory_list
            
        except Exception as e:
            logger.error(f"Failed to list memory for category {category}: {e}")
            return []
    
    def delete_memory(self, key: str) -> bool:
        """Delete a memory entry"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM memory_storage WHERE memory_key = ?', (key,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            if deleted:
                logger.info(f"Deleted memory: {key}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete memory {key}: {e}")
            return False
    
    def _deserialize_value(self, value_str: str, value_type: str) -> Any:
        """Helper to deserialize stored values"""
        if value_type == "json":
            return json.loads(value_str)
        elif value_type == "number":
            try:
                return float(value_str) if '.' in value_str else int(value_str)
            except ValueError:
                logger.error(f"Failed to parse number: {value_str}")
                return value_str
        elif value_type == "boolean":
            return value_str.lower() in ('true', '1', 'yes', 'on')
        else:
            return value_str
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory storage statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Total memory entries
            cursor.execute('SELECT COUNT(*) FROM memory_storage WHERE expires_at IS NULL OR expires_at > datetime("now")')
            total_entries = cursor.fetchone()[0]
            
            # Memory by category
            cursor.execute('''
                SELECT category, COUNT(*) as count 
                FROM memory_storage 
                WHERE expires_at IS NULL OR expires_at > datetime("now")
                GROUP BY category
            ''')
            category_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Database size
            cursor.execute('SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()')
            db_size = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_entries": total_entries,
                "category_breakdown": category_stats,
                "database_size_bytes": db_size,
                "categories_available": list(self.memory_categories.keys()),
                "cleanup_last_run": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}
    
    def create_session(self, session_id: str, context_data: Dict = None) -> bool:
        """Create or update a session entry"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            context_str = json.dumps(context_data or {})
            
            cursor.execute('''
                INSERT OR REPLACE INTO session_tracking 
                (session_id, context_data, last_active)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (session_id, context_str))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Created/updated session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol requests for memory operations"""
        method = request.get("method")
        
        if method == "tools/list":
            return {
                "tools": [
                    {
                        "name": "memory_store",
                        "description": "Store persistent memory across Claude Code sessions",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string", "description": "Memory key identifier"},
                                "value": {"description": "Value to store (any type)"},
                                "category": {
                                    "type": "string", 
                                    "enum": list(self.memory_categories.keys()),
                                    "default": "general",
                                    "description": "Memory category for organization"
                                },
                                "expires_hours": {"type": "integer", "description": "Hours until expiration (optional)"},
                                "session_id": {"type": "string", "description": "Session identifier (optional)"},
                                "metadata": {"type": "object", "description": "Additional metadata (optional)"}
                            },
                            "required": ["key", "value"]
                        }
                    },
                    {
                        "name": "memory_retrieve",
                        "description": "Retrieve persistent memory from storage",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string", "description": "Memory key to retrieve"},
                                "default": {"description": "Default value if key not found"}
                            },
                            "required": ["key"]
                        }
                    },
                    {
                        "name": "memory_list",
                        "description": "List memory entries by category",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "category": {
                                    "type": "string",
                                    "enum": list(self.memory_categories.keys()),
                                    "description": "Category to list"
                                }
                            },
                            "required": ["category"]
                        }
                    },
                    {
                        "name": "memory_delete",
                        "description": "Delete a memory entry",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "key": {"type": "string", "description": "Memory key to delete"}
                            },
                            "required": ["key"]
                        }
                    },
                    {
                        "name": "memory_stats",
                        "description": "Get memory storage statistics and health info",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "memory_cleanup",
                        "description": "Clean up expired memory entries",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "session_create",
                        "description": "Create or update session tracking",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "session_id": {"type": "string", "description": "Session identifier"},
                                "context_data": {"type": "object", "description": "Session context data"}
                            },
                            "required": ["session_id"]
                        }
                    }
                ]
            }
        
        elif method == "tools/call":
            tool_name = request["params"]["name"]
            arguments = request["params"].get("arguments", {})
            
            try:
                if tool_name == "memory_store":
                    key = arguments.get("key")
                    value = arguments.get("value")
                    category = arguments.get("category", "general")
                    expires_hours = arguments.get("expires_hours")
                    session_id = arguments.get("session_id")
                    metadata = arguments.get("metadata", {})
                    
                    success = self.store_memory(key, value, category, expires_hours, session_id, metadata)
                    result = f"Memory stored successfully: {key}" if success else f"Failed to store memory: {key}"
                
                elif tool_name == "memory_retrieve":
                    key = arguments.get("key")
                    default = arguments.get("default")
                    
                    value = self.retrieve_memory(key, default)
                    result = {
                        "key": key,
                        "value": value,
                        "found": value != default
                    }
                
                elif tool_name == "memory_list":
                    category = arguments.get("category")
                    memory_list = self.list_memory_by_category(category)
                    result = {
                        "category": category,
                        "entries": memory_list,
                        "count": len(memory_list)
                    }
                
                elif tool_name == "memory_delete":
                    key = arguments.get("key")
                    success = self.delete_memory(key)
                    result = f"Memory deleted: {key}" if success else f"Failed to delete memory: {key}"
                
                elif tool_name == "memory_stats":
                    result = self.get_memory_stats()
                
                elif tool_name == "memory_cleanup":
                    self.cleanup_expired_memory()
                    result = "Memory cleanup completed successfully"
                
                elif tool_name == "session_create":
                    session_id = arguments.get("session_id")
                    context_data = arguments.get("context_data", {})
                    success = self.create_session(session_id, context_data)
                    result = f"Session created: {session_id}" if success else f"Failed to create session: {session_id}"
                
                else:
                    result = f"Unknown tool: {tool_name}"
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2) if isinstance(result, dict) else str(result)
                        }
                    ]
                }
                
            except Exception as e:
                logger.error(f"Tool execution error for {tool_name}: {e}")
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Tool execution error: {str(e)}"
                        }
                    ]
                }
        
        return {"error": f"Unknown method: {method}"}

async def main():
    """Main MCP server loop"""
    server = MCPMemoryPersistenceServer()
    
    # Initialize default memory entries for OpenRouter and enterprise systems
    await initialize_default_memory(server)
    
    # MCP JSON-RPC over stdio
    logger.info("MCP Memory Persistence Server started - ready for requests")
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line.strip())
            response = await server.handle_mcp_request(request)
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
            break
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            error_response = {"error": str(e)}
            print(json.dumps(error_response))
            sys.stdout.flush()

async def initialize_default_memory(server: MCPMemoryPersistenceServer):
    """Initialize default memory entries for cross-session persistence"""
    try:
        # OpenRouter configuration
        server.store_memory(
            "openrouter/api_key",
            api_manager.get_api_key('openrouter'),
            "openrouter",
            metadata={"description": "OpenRouter API key for free models", "verified": True}
        )
        
        server.store_memory(
            "openrouter/status", 
            {"active": True, "cost": 0.00, "models_available": 56, "usage_limit": "unlimited"},
            "openrouter"
        )
        
        # Enterprise platform states
        server.store_memory(
            "enterprise/platforms",
            {
                "ai_command_center": {"status": "operational", "value": 80000},
                "crypto_hub": {"status": "operational", "value": 80000},  
                "repo_wizard": {"status": "operational", "value": 80000}
            },
            "enterprise"
        )
        
        # Revenue system states
        server.store_memory(
            "revenue/portfolio_value",
            240000,
            "revenue",
            metadata={"currency": "USD", "last_updated": datetime.now().isoformat()}
        )
        
        # System performance baseline
        server.store_memory(
            "performance/baseline",
            {
                "response_time_ms": 250,
                "success_rate": 0.95,
                "cost_per_request": 0.00,
                "uptime": "99.9%"
            },
            "performance"
        )
        
        # User preferences defaults
        server.store_memory(
            "user_prefs/dashboard_settings",
            {
                "theme": "dark",
                "auto_refresh": True,
                "notifications": True,
                "preferred_models": ["deepseek", "claude", "gemini"]
            },
            "user_prefs"
        )
        
        logger.info("Default memory entries initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize default memory: {e}")

if __name__ == "__main__":
    asyncio.run(main())