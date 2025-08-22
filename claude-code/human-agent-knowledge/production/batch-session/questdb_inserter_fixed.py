#!/usr/bin/env python3
"""
QuestDB Inserter - Fixed version for timezone issues
"""

import psycopg2
import psycopg2.extras
import json
import sys
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

# Import from our clean parser
sys.path.append('/home/quant/AI-Agent-Host/claude-code/chat-history')
from conversation_parser_clean import ConversationMessage, ConversationParser

class QuestDBInserter:
    """Fixed QuestDB inserter that handles timezone issues"""
    
    def __init__(self, host: str = '192.168.1.216', port: int = 8812, 
                 database: str = 'qdb', user: str = 'admin', password: str = 'quest'):
        self.host = host
        self.port = port 
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.stats = {
            'total_inserts': 0,
            'successful_inserts': 0,
            'failed_inserts': 0,
            'start_time': None,
            'end_time': None
        }
    
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
        except Exception as e:
            print(f"Failed to connect to QuestDB: {e}", file=sys.stderr)
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
        except Exception as e:
            print(f"Failed to create table: {e}", file=sys.stderr)
            return False
    
    def fix_timestamp(self, timestamp) -> datetime:
        """Convert timezone-aware timestamp to timezone-naive for QuestDB"""
        if timestamp is None:
            return datetime.now()
        
        if isinstance(timestamp, str):
            # Parse ISO string and remove timezone
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None)
        
        if hasattr(timestamp, 'tzinfo') and timestamp.tzinfo is not None:
            # Convert to UTC and remove timezone info
            utc_dt = timestamp.astimezone(timezone.utc)
            return utc_dt.replace(tzinfo=None)
        
        return timestamp
    
    def validate_message(self, message: ConversationMessage) -> Tuple[bool, Optional[str]]:
        """Validate a message before insertion"""
        if not message.timestamp:
            return False, "Missing timestamp"
        
        if not message.session_id:
            return False, "Missing session_id"
        
        if not message.message_type:
            return False, "Missing message_type"
        
        if not message.content or not message.content.strip():
            return False, "Empty content"
        
        valid_types = ['user_input', 'claude_response', 'tool_usage', 'system_info']
        if message.message_type not in valid_types:
            return False, f"Invalid message_type: {message.message_type}"
        
        if len(message.content) > 100000:  # Reduced from 1MB to 100KB for safety
            return False, "Content too large (>100KB)"
        
        if message.response_quality is not None:
            if not (0 <= message.response_quality <= 1.0):
                return False, f"Invalid response_quality: {message.response_quality}"
        
        return True, None
    
    def insert_message(self, message: ConversationMessage, 
                      validate: bool = True) -> Tuple[bool, Optional[str]]:
        """Insert a single message into QuestDB"""
        if validate:
            is_valid, error_msg = self.validate_message(message)
            if not is_valid:
                return False, error_msg
        
        insert_sql = """
        INSERT INTO chat (
            timestamp, session_id, message_type, content, project_tag,
            tool_used, file_modified, context_tokens, response_quality, streaming
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            # Fix timestamp before insertion
            fixed_timestamp = self.fix_timestamp(message.timestamp)
            
            with self.connection.cursor() as cursor:
                cursor.execute(insert_sql, (
                    fixed_timestamp,
                    message.session_id,
                    message.message_type,
                    message.content,
                    message.project_tag,
                    message.tool_used,
                    message.file_modified,
                    message.context_tokens,
                    message.response_quality,
                    False  # streaming = False for batch processing
                ))
            return True, None
        except Exception as e:
            return False, str(e)
    
    def insert_messages_batch(self, messages: List[ConversationMessage],
                             batch_size: int = 100, validate: bool = True) -> Dict[str, Any]:
        """Insert multiple messages in batches with comprehensive error handling"""
        self.stats['start_time'] = datetime.now()
        self.stats['total_inserts'] = len(messages)
        
        successful_messages = []
        failed_messages = []
        
        for i, message in enumerate(messages):
            success, error = self.insert_message(message, validate)
            if success:
                successful_messages.append(message)
            else:
                failed_messages.append({
                    'message': message,
                    'error': error,
                    'timestamp': str(message.timestamp) if message.timestamp else 'unknown'
                })
            
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(messages)} messages", file=sys.stderr)
        
        self.stats['successful_inserts'] = len(successful_messages)
        self.stats['failed_inserts'] = len(failed_messages)
        self.stats['end_time'] = datetime.now()
        
        # Show first few errors for debugging
        if failed_messages:
            print(f"\n❌ First few errors:", file=sys.stderr)
            for i, failure in enumerate(failed_messages[:3]):
                print(f"   Error {i+1}: {failure['error']}", file=sys.stderr)
        
        return {
            'total_processed': len(messages),
            'successful_count': len(successful_messages),
            'failed_count': len(failed_messages),
            'successful_messages': successful_messages,
            'failed_messages': failed_messages,
            'stats': self.stats
        }
    
    def get_insertion_stats(self) -> Dict[str, Any]:
        """Get detailed statistics about the insertion process"""
        stats = self.stats.copy()
        
        if stats['start_time'] and stats['end_time']:
            duration = (stats['end_time'] - stats['start_time']).total_seconds()
            stats['duration_seconds'] = duration
            
            if stats['successful_inserts'] > 0 and duration > 0:
                stats['messages_per_second'] = stats['successful_inserts'] / duration
            else:
                stats['messages_per_second'] = 0
        
        return stats
    
    def verify_insertion(self, session_id: str) -> Dict[str, Any]:
        """Verify that messages were successfully inserted for a session"""
        verify_sql = """
        SELECT 
            COUNT(*) as total_messages,
            MIN(timestamp) as earliest_message,
            MAX(timestamp) as latest_message,
            COUNT(DISTINCT message_type) as message_types,
            COUNT(DISTINCT project_tag) as project_tags
        FROM chat 
        WHERE session_id = %s
        """
        
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(verify_sql, (session_id,))
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            print(f"Verification failed: {e}", file=sys.stderr)
            return {}

def main():
    """Command line interface for QuestDB insertion"""
    parser = argparse.ArgumentParser(description='Insert Claude Code conversation data into QuestDB (Fixed)')
    parser.add_argument('session_log', help='Path to session log file')
    parser.add_argument('timing_log', help='Path to timing log file')
    parser.add_argument('meta_file', help='Path to metadata JSON file')
    
    # QuestDB connection options
    parser.add_argument('--host', default='192.168.1.216', help='QuestDB host (default: 192.168.1.216)')
    parser.add_argument('--port', type=int, default=8812, help='QuestDB port (default: 8812)')
    parser.add_argument('--database', default='qdb', help='Database name (default: qdb)')
    parser.add_argument('--user', default='admin', help='Username (default: admin)')
    parser.add_argument('--password', default='quest', help='Password (default: quest)')
    
    # Processing options
    parser.add_argument('--create-table', action='store_true',
                        help='Create table if it does not exist')
    parser.add_argument('--verify', action='store_true',
                        help='Verify insertion after completion')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quiet', action='store_true', help='Suppress output')
    
    args = parser.parse_args()
    
    # Initialize QuestDB inserter first
    inserter = QuestDBInserter(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password
    )
    
    # Connect to QuestDB
    if not inserter.connect():
        return 1
    
    try:
        # Create table if requested (independent of log parsing)
        if args.create_table:
            if not inserter.create_table_if_not_exists():
                return 1
            # If only creating table, exit successfully
            if args.session_log == '/tmp/dummy.log':
                return 0
    
        # Parse conversation data only for real sessions
        if args.verbose and not args.quiet:
            print("Parsing conversation data...", file=sys.stderr)
        
        parser_instance = ConversationParser()
        try:
            messages = parser_instance.parse_session_to_messages(
                args.session_log, args.timing_log, args.meta_file
            )
            
            if not messages:
                if not args.quiet:
                    print("Error: No messages to insert", file=sys.stderr)
                return 1
            
            if args.verbose and not args.quiet:
                print(f"Parsed {len(messages)} messages", file=sys.stderr)
                
        except Exception as e:
            if not args.quiet:
                print(f"Error parsing conversation: {e}", file=sys.stderr)
            return 1
        
        # Get session ID for operations
        session_id = messages[0].session_id if messages else 'unknown'
        
        # Insert messages
        if args.verbose and not args.quiet:
            print(f"Inserting {len(messages)} messages into QuestDB...", file=sys.stderr)
        
        result = inserter.insert_messages_batch(messages)
        
        # Report results
        stats = inserter.get_insertion_stats()
        
        if not args.quiet:
            print(f"\n✅ Insertion Results:", file=sys.stderr)
            print(f"  Total processed: {result['total_processed']}", file=sys.stderr)
            print(f"  Successful: {result['successful_count']}", file=sys.stderr)
            print(f"  Failed: {result['failed_count']}", file=sys.stderr)
            print(f"  Duration: {stats.get('duration_seconds', 0):.2f} seconds", file=sys.stderr)
            print(f"  Rate: {stats.get('messages_per_second', 0):.1f} messages/sec", file=sys.stderr)
        
        # Verify insertion if requested
        if args.verify:
            if args.verbose and not args.quiet:
                print(f"Verifying insertion for session {session_id}...", file=sys.stderr)
            verification = inserter.verify_insertion(session_id)
            if verification and not args.quiet:
                print(f"\n✅ Verification Results:", file=sys.stderr)
                for key, value in verification.items():
                    print(f"  {key}: {value}", file=sys.stderr)
        
        # Return appropriate exit code
        return 0 if result['failed_count'] == 0 else 2
        
    finally:
        inserter.disconnect()

if __name__ == "__main__":
    sys.exit(main())