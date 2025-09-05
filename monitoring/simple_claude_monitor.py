#!/usr/bin/env python3
"""
Simple Claude Code Monitor
Lightweight monitoring without Docker - tracks usage and costs
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import threading

class SimpleClaudeMonitor:
    """Simple monitoring for Claude Code usage without Docker requirements"""
    
    def __init__(self):
        self.init_monitoring_database()
        self.start_time = datetime.now()
        
        # Claude usage tracking
        self.usage_stats = {
            "session_start": self.start_time.isoformat(),
            "total_requests": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
            "tools_used": {},
            "session_duration": 0
        }
        
        print("[MONITOR] Simple Claude Code Monitor Started")
        print("=" * 50)
        
    def init_monitoring_database(self):
        """Initialize lightweight monitoring database"""
        self.conn = sqlite3.connect('claude_usage.db', check_same_thread=False)
        self.lock = threading.Lock()
        
        cursor = self.conn.cursor()
        
        # Usage sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_start TIMESTAMP,
                session_end TIMESTAMP,
                total_requests INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                estimated_cost REAL DEFAULT 0.0,
                tools_used TEXT,
                productivity_score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Daily usage summary
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                total_requests INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                estimated_cost REAL DEFAULT 0.0,
                session_count INTEGER DEFAULT 0,
                avg_session_duration REAL DEFAULT 0,
                top_tools TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tool usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT,
                usage_count INTEGER DEFAULT 1,
                total_execution_time REAL DEFAULT 0,
                success_rate REAL DEFAULT 100,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print("[OK] Simple monitoring database initialized")
        
    def track_request(self, tool_name: str = "unknown", tokens: int = 0, cost: float = 0.0):
        """Track a Claude Code request"""
        with self.lock:
            self.usage_stats["total_requests"] += 1
            self.usage_stats["total_tokens"] += tokens
            self.usage_stats["estimated_cost"] += cost
            
            if tool_name in self.usage_stats["tools_used"]:
                self.usage_stats["tools_used"][tool_name] += 1
            else:
                self.usage_stats["tools_used"][tool_name] = 1
            
            # Update tool usage in database
            cursor = self.conn.cursor()
            # Check if tool exists and update or insert
            cursor.execute('SELECT usage_count FROM tool_usage WHERE tool_name = ?', (tool_name,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE tool_usage 
                    SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
                    WHERE tool_name = ?
                ''', (tool_name,))
            else:
                cursor.execute('''
                    INSERT INTO tool_usage (tool_name, usage_count, last_used)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                ''', (tool_name,))
            
            self.conn.commit()
    
    def get_session_summary(self) -> Dict:
        """Get current session summary"""
        current_time = datetime.now()
        session_duration = (current_time - self.start_time).total_seconds() / 60  # Minutes
        
        return {
            "session_duration_minutes": round(session_duration, 1),
            "total_requests": self.usage_stats["total_requests"],
            "total_tokens": self.usage_stats["total_tokens"],
            "estimated_cost": round(self.usage_stats["estimated_cost"], 4),
            "requests_per_minute": round(self.usage_stats["total_requests"] / session_duration, 2) if session_duration > 0 else 0,
            "tools_used": self.usage_stats["tools_used"],
            "cost_per_request": round(self.usage_stats["estimated_cost"] / self.usage_stats["total_requests"], 4) if self.usage_stats["total_requests"] > 0 else 0
        }
    
    def get_daily_stats(self) -> Dict:
        """Get daily usage statistics"""
        with self.lock:
            cursor = self.conn.cursor()
            
            # Get today's stats
            today = datetime.now().date()
            cursor.execute('''
                SELECT 
                    SUM(total_requests) as requests,
                    SUM(total_tokens) as tokens,
                    SUM(estimated_cost) as cost,
                    COUNT(*) as sessions
                FROM usage_sessions 
                WHERE DATE(session_start) = ?
            ''', (today,))
            
            daily_stats = cursor.fetchone()
            
            # Get top tools
            cursor.execute('''
                SELECT tool_name, SUM(usage_count) as total_usage
                FROM tool_usage 
                WHERE DATE(last_used) = ?
                GROUP BY tool_name
                ORDER BY total_usage DESC
                LIMIT 5
            ''', (today,))
            
            top_tools = cursor.fetchall()
            
            return {
                "date": today.isoformat(),
                "total_requests": daily_stats[0] or 0,
                "total_tokens": daily_stats[1] or 0,
                "estimated_cost": daily_stats[2] or 0.0,
                "session_count": daily_stats[3] or 0,
                "avg_session_duration": 0,  # Simplified for now
                "top_tools": [{"tool": tool[0], "usage": tool[1]} for tool in top_tools]
            }
    
    def generate_usage_report(self) -> str:
        """Generate formatted usage report"""
        session_summary = self.get_session_summary()
        daily_stats = self.get_daily_stats()
        
        report = f"""
[REPORT] CLAUDE CODE USAGE REPORT
============================

[SESSION] Current Session:
   Duration: {session_summary['session_duration_minutes']} minutes
   Requests: {session_summary['total_requests']}
   Tokens: {session_summary['total_tokens']}
   Cost: ${session_summary['estimated_cost']:.4f}
   Rate: {session_summary['requests_per_minute']} requests/min

[DAILY] Daily Summary ({daily_stats['date']}):
   Total Requests: {daily_stats['total_requests']}
   Total Tokens: {daily_stats['total_tokens']}
   Total Cost: ${daily_stats['estimated_cost']:.4f}
   Sessions: {daily_stats['session_count']}
   Avg Session: {daily_stats['avg_session_duration']} minutes

[TOOLS] Tools Used This Session:
"""
        
        for tool, count in session_summary['tools_used'].items():
            report += f"   {tool}: {count} times\n"
        
        if daily_stats['top_tools']:
            report += f"\n[TOP] Top Tools Today:\n"
            for tool_data in daily_stats['top_tools']:
                report += f"   {tool_data['tool']}: {tool_data['usage']} uses\n"
        
        return report
    
    def save_session(self):
        """Save current session to database"""
        with self.lock:
            cursor = self.conn.cursor()
            session_duration = (datetime.now() - self.start_time).total_seconds() / 60
            
            cursor.execute('''
                INSERT INTO usage_sessions 
                (session_start, session_end, total_requests, total_tokens, 
                 estimated_cost, tools_used, productivity_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.start_time, datetime.now(),
                self.usage_stats["total_requests"],
                self.usage_stats["total_tokens"], 
                self.usage_stats["estimated_cost"],
                json.dumps(self.usage_stats["tools_used"]),
                85  # Default productivity score
            ))
            
            self.conn.commit()

# Global monitor instance
monitor = SimpleClaudeMonitor()

def track_usage(tool_name: str = "claude", tokens: int = 1000, cost: float = 0.01):
    """Simple function to track Claude usage"""
    monitor.track_request(tool_name, tokens, cost)
    return monitor.get_session_summary()

def show_usage_report():
    """Display current usage report"""
    print(monitor.generate_usage_report())
    return monitor.get_session_summary()

def save_session():
    """Save current session"""
    monitor.save_session()
    print("[OK] Session saved to database")

if __name__ == "__main__":
    # Simulate some usage for demonstration
    print("[START] Starting Claude Code monitoring simulation...")
    
    # Simulate various tool usage
    tools = ["Read", "Write", "Edit", "Bash", "WebFetch", "Grep", "Glob"]
    
    import random
    
    for i in range(10):
        tool = tools[i % len(tools)]
        tokens = random.randint(500, 2000)
        cost = tokens * 0.000015  # Approximate cost per token
        
        track_usage(tool, tokens, cost)
        time.sleep(0.1)  # Small delay
    
    # Show final report
    show_usage_report()
    save_session()