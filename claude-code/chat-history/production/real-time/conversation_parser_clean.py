#!/usr/bin/env python3
"""
Conversation Parser for Claude Code Sessions
Processes logged Claude Code sessions into structured conversation data ready for QuestDB
"""

import re
import json
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from timestamp_utils import extract_timestamps_from_session, ConversationTimestampProcessor

@dataclass
class ConversationMessage:
    """Structured representation of a conversation message for database storage"""
    timestamp: datetime
    session_id: str
    message_type: str  # 'user_input', 'claude_response', 'tool_usage', 'system_info'
    content: str
    project_tag: Optional[str] = None
    tool_used: Optional[str] = None
    file_modified: Optional[str] = None
    context_tokens: Optional[int] = None
    response_quality: Optional[float] = None
    raw_content: Optional[str] = None

class ConversationParser:
    """Main parser for converting Claude Code sessions into structured conversation data"""
    
    def __init__(self):
        self.project_tag_patterns = self._build_project_patterns()
        self.file_patterns = self._build_file_patterns()
        self.quality_indicators = self._build_quality_patterns()
        
    def _build_project_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for detecting project context from conversation content"""
        return {
            'ai-agent-host': [
                r'ai.?agent.?host', r'claude.?code', r'questdb', r'grafana',
                r'docker.*stack', r'agentic.*environment'
            ],
            'python': [
                r'python', r'\.py', r'pip', r'conda', r'jupyter',
                r'pandas', r'numpy', r'matplotlib'
            ],
            'docker': [
                r'docker', r'container', r'compose', r'dockerfile',
                r'image.*build', r'docker.*run'
            ],
            'database': [
                r'questdb', r'sql', r'schema', r'table', r'query',
                r'database', r'time.?series'
            ]
        }
    
    def _build_file_patterns(self) -> List[Tuple[str, str]]:
        """Build patterns for detecting file operations from Claude responses"""
        return [
            (r'● Read\((.*?)\)', 'read'),
            (r'● Write\((.*?)\)', 'write'),
            (r'● Edit\((.*?)\)', 'edit'),
            (r'● Bash.*?(/?[\w\-/\.]+)', 'execute'),
            (r'created.*?(/[\w\-/\.]+)', 'create')
        ]
    
    def _build_quality_patterns(self) -> Dict[str, float]:
        """Build patterns for assessing response quality"""
        return {
            r'✅': 0.1,
            r'successfully': 0.05,
            r'completed': 0.05,
            r'❌': -0.2,
            r'error': -0.1,
            r'failed': -0.1
        }
    
    def detect_project_tag(self, content: str) -> Optional[str]:
        """Detect project context from message content"""
        content_lower = content.lower()
        
        scores = {}
        for project, patterns in self.project_tag_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                score += matches
            if score > 0:
                scores[project] = score
        
        if scores:
            return max(scores, key=scores.get)
        return None
    
    def extract_file_info(self, content: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract file path and operation type from Claude response"""
        for pattern, operation in self.file_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                file_path = match.group(1) if match.groups() else None
                return file_path, operation
        return None, None
    
    def estimate_context_tokens(self, content: str) -> int:
        """Rough estimation of token count for context tracking"""
        return max(1, len(content) // 4)
    
    def assess_response_quality(self, content: str, message_type: str) -> Optional[float]:
        """Assess the quality of a Claude response based on content indicators"""
        if message_type != 'claude_response':
            return None
        
        base_score = 0.75
        for pattern, score_delta in self.quality_indicators.items():
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            base_score += matches * score_delta
        
        return max(0.1, min(1.0, base_score))
    
    def parse_session_to_messages(self, session_log: str, timing_log: str, 
                                meta_file: str) -> List[ConversationMessage]:
        """Parse a complete Claude Code session into structured messages"""
        events = extract_timestamps_from_session(session_log, timing_log, meta_file)
        
        if not events:
            print("Warning: No conversation events extracted", file=sys.stderr)
            return []
        
        try:
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
            session_id = metadata.get('session_id', 'unknown')
        except Exception as e:
            print(f"Warning: Could not load metadata: {e}", file=sys.stderr)
            session_id = 'unknown'
        
        messages = []
        
        for event in events:
            file_path, operation = None, None
            tool_name = None
            
            if event['type'] in ['claude_response', 'tool_usage']:
                file_path, operation = self.extract_file_info(event['content'])
                if event['type'] == 'tool_usage':
                    tool_name = event.get('tool_name', 'unknown')
            
            message = ConversationMessage(
                timestamp=event['timestamp'],
                session_id=session_id,
                message_type=event['type'],
                content=event['content'],
                project_tag=self.detect_project_tag(event['content']),
                tool_used=tool_name,
                file_modified=file_path,
                context_tokens=self.estimate_context_tokens(event['content']),
                response_quality=self.assess_response_quality(event['content'], event['type']),
                raw_content=event.get('raw_content')
            )
            
            messages.append(message)
        
        return messages
    
    def export_to_questdb_format(self, messages: List[ConversationMessage], 
                                output_format: str = 'csv') -> str:
        """Export messages to QuestDB-compatible format"""
        if output_format == 'csv':
            return self._export_to_csv(messages)
        elif output_format == 'sql':
            return self._export_to_sql(messages)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def _export_to_csv(self, messages: List[ConversationMessage]) -> str:
        """Export to CSV format for QuestDB import"""
        lines = ['timestamp,session_id,message_type,content,project_tag,tool_used,file_modified,context_tokens,response_quality']
        
        for msg in messages:
            content = msg.content.replace('"', '""').replace('\n', '\\n')
            line = f'"{msg.timestamp.isoformat()}","{msg.session_id}","{msg.message_type}","{content}","{msg.project_tag or ""}","{msg.tool_used or ""}","{msg.file_modified or ""}",{msg.context_tokens or 0},{msg.response_quality or ""}'
            lines.append(line)
        
        return '\n'.join(lines)
    
    def generate_session_summary(self, messages: List[ConversationMessage]) -> Dict[str, Any]:
        """Generate summary statistics for the parsed session"""
        if not messages:
            return {}
        
        total_messages = len(messages)
        user_messages = len([m for m in messages if m.message_type == 'user_input'])
        claude_messages = len([m for m in messages if m.message_type == 'claude_response'])
        
        return {
            'session_id': messages[0].session_id,
            'total_messages': total_messages,
            'user_messages': user_messages,
            'claude_messages': claude_messages,
        }

def main():
    """Command line interface for conversation parsing"""
    parser = argparse.ArgumentParser(description='Parse Claude Code sessions into structured conversation data')
    parser.add_argument('session_log', help='Path to session log file')
    parser.add_argument('timing_log', help='Path to timing log file')
    parser.add_argument('meta_file', help='Path to metadata JSON file')
    parser.add_argument('--format', choices=['csv', 'sql', 'json'], default='csv',
                        help='Output format (default: csv)')
    parser.add_argument('--summary', action='store_true',
                        help='Generate session summary statistics')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    
    args = parser.parse_args()
    
    conversation_parser = ConversationParser()
    
    if args.verbose:
        print(f"Parsing Claude Code session from {args.session_log}...", file=sys.stderr)
    
    try:
        messages = conversation_parser.parse_session_to_messages(
            args.session_log, args.timing_log, args.meta_file
        )
        
        if not messages:
            print("❌ No messages parsed from session", file=sys.stderr)
            return 1
        
        if args.verbose:
            print(f"✅ Parsed {len(messages)} conversation messages", file=sys.stderr)
        
        if args.format == 'json':
            output = json.dumps([asdict(msg) for msg in messages], indent=2, default=str)
        else:
            output = conversation_parser.export_to_questdb_format(messages, args.format)
        
        print(output)
        
        if args.summary:
            summary = conversation_parser.generate_session_summary(messages)
            print("\n--- Session Summary ---", file=sys.stderr)
            print(json.dumps(summary, indent=2), file=sys.stderr)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error parsing session: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc(file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())