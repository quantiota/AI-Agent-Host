#!/usr/bin/env python3
"""
QuestDB Real-Time Stream Inserter
Handles individual message streaming to QuestDB for real-time conversation logging
"""

import psycopg2
import json
import sys
import argparse
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class QuestDBStreamInserter:
    """Lightweight inserter for real-time message streaming"""
    
    def __init__(self, host: str = '192.168.1.216', port: int = 8812, 
                 database: str = 'qdb', user: str = 'admin', password: str = 'quest'):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
    
    def connect(self) -> bool:
        """Establish connection to QuestDB"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.connection.autocommit = True
            return True
        except Exception:
            return False
    
    def disconnect(self):
        """Close QuestDB connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def create_table_if_not_exists(self) -> bool:
        """Create the chat table if it doesn't exist"""
        create_sql = """
        CREATE TABLE IF NOT EXISTS chat (
            timestamp TIMESTAMP,
            session_id SYMBOL CAPACITY 10000 CACHE,
            message_type SYMBOL CAPACITY 10 CACHE,
            content STRING,
            project_tag SYMBOL CAPACITY 1000 CACHE,
            tool_used SYMBOL CAPACITY 100 CACHE,
            file_modified STRING,
            context_tokens INT,
            response_quality DOUBLE,
            streaming BOOLEAN
        ) TIMESTAMP(timestamp) PARTITION BY DAY;
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_sql)
            return True
        except Exception:
            return False
    
    def fix_timestamp(self, timestamp) -> datetime:
        """Convert timestamp to timezone-naive for QuestDB"""
        if timestamp is None:
            return datetime.now()
        
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.replace(tzinfo=None)
            except:
                return datetime.now()
        
        if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo is not None:
            utc_dt = timestamp.astimezone(timezone.utc)
            return utc_dt.replace(tzinfo=None)
        
        return timestamp
    
    def detect_project_tag(self, content: str) -> Optional[str]:
        """Simple project detection for real-time streaming"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['python', 'pip', '.py']):
            return 'python'
        elif any(word in content_lower for word in ['docker', 'container']):
            return 'docker'
        elif any(word in content_lower for word in ['questdb', 'sql', 'database']):
            return 'database'
        elif any(word in content_lower for word in ['javascript', 'js', 'node']):
            return 'javascript'
        
        return None
    
    def assess_response_quality(self, content: str, message_type: str) -> Optional[float]:
        """Quick quality assessment for Claude responses"""
        if message_type != 'claude_response':
            return None
        
        base_score = 0.75
        
        if '✅' in content:
            base_score += 0.1
        if '❌' in content:
            base_score -= 0.2
        if 'successfully' in content.lower():
            base_score += 0.05
        if 'error' in content.lower():
            base_score -= 0.1
        
        return max(0.1, min(1.0, base_score))
    
    def stream_message(self, message_data: Dict[str, Any]) -> bool:
        """Stream a single message to QuestDB"""
        try:
            # Fix timestamp
            timestamp = self.fix_timestamp(message_data.get('timestamp'))
            
            # Extract/enhance data
            session_id = message_data.get('session_id', 'unknown')
            message_type = message_data.get('message_type', 'unknown')
            content = message_data.get('content', '')
            project_tag = message_data.get('project_tag') or self.detect_project_tag(content)
            tool_used = message_data.get('tool_used')
            file_modified = message_data.get('file_modified')
            context_tokens = message_data.get('context_tokens', len(content) // 4)
            response_quality = message_data.get('response_quality') or self.assess_response_quality(content, message_type)
            streaming = message_data.get('streaming', True)
            
            # Insert message
            insert_sql = """
            INSERT INTO chat (
                timestamp, session_id, message_type, content, project_tag,
                tool_used, file_modified, context_tokens, response_quality, streaming
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(insert_sql, (
                    timestamp,
                    session_id,
                    message_type,
                    content[:10000],  # Limit content size for streaming
                    project_tag,
                    tool_used,
                    file_modified,
                    context_tokens,
                    response_quality,
                    streaming
                ))
            
            return True
        except Exception as e:
            # Silent failure for streaming - don't interrupt conversation
            return False

def main():
    """Command line interface for streaming"""
    parser = argparse.ArgumentParser(description='Stream single message to QuestDB')
    parser.add_argument('--json-file', help='JSON file with message data')
    parser.add_argument('--json', help='JSON string with message data')
    parser.add_argument('--create-table', action='store_true', help='Create table if needed')
    parser.add_argument('--host', default='192.168.1.216', help='QuestDB host')
    parser.add_argument('--port', type=int, default=8812, help='QuestDB port')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    # Load message data
    message_data = None
    
    if args.json_file:
        try:
            with open(args.json_file, 'r') as f:
                message_data = json.load(f)
        except Exception:
            if not args.quiet:
                print("Error reading JSON file", file=sys.stderr)
            return 1
    
    elif args.json:
        try:
            message_data = json.loads(args.json)
        except Exception:
            if not args.quiet:
                print("Error parsing JSON", file=sys.stderr)
            return 1
    
    else:
        # Read from stdin
        try:
            message_data = json.load(sys.stdin)
        except Exception:
            if not args.quiet:
                print("Error reading JSON from stdin", file=sys.stderr)
            return 1
    
    if not message_data:
        return 1
    
    # Initialize inserter
    inserter = QuestDBStreamInserter(host=args.host, port=args.port)
    
    if not inserter.connect():
        return 1
    
    try:
        # Create table if needed
        if args.create_table:
            inserter.create_table_if_not_exists()
        
        # Stream the message
        success = inserter.stream_message(message_data)
        return 0 if success else 1
        
    finally:
        inserter.disconnect()

if __name__ == "__main__":
    sys.exit(main())