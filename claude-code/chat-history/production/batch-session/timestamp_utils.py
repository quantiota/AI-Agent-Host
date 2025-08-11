#!/usr/bin/env python3
"""
Timestamp Extraction Utilities for Claude Code Sessions
Processes script command timing logs to extract precise timestamps for conversations
"""

import re
import json
import sys
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass

@dataclass
class TimingEvent:
    """Represents a timing event from script command output"""
    delay: float  # Time since previous event in seconds
    content: str  # Content associated with this timing
    cumulative_time: float  # Total time since session start
    timestamp: datetime  # Absolute timestamp

class TimestampExtractor:
    def __init__(self, session_start_time: datetime):
        self.session_start_time = session_start_time
        self.cumulative_time = 0.0
        
    def parse_script_timing_file(self, timing_file_path: str) -> List[TimingEvent]:
        """
        Parse script command timing file format
        Format: "delay count\n" where delay is seconds and count is bytes
        """
        timing_events = []
        
        try:
            with open(timing_file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    try:
                        # Parse timing line: "delay count"
                        parts = line.split()
                        if len(parts) >= 2:
                            delay = float(parts[0])
                            byte_count = int(parts[1])
                            
                            self.cumulative_time += delay
                            timestamp = self.session_start_time + timedelta(seconds=self.cumulative_time)
                            
                            event = TimingEvent(
                                delay=delay,
                                content="",  # Content filled later by correlating with session log
                                cumulative_time=self.cumulative_time,
                                timestamp=timestamp
                            )
                            timing_events.append(event)
                            
                    except (ValueError, IndexError) as e:
                        print(f"Warning: Could not parse timing line {line_num}: '{line}' ({e})", 
                              file=sys.stderr)
                        continue
                        
        except FileNotFoundError:
            print(f"Error: Timing file not found: {timing_file_path}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Error parsing timing file: {e}", file=sys.stderr)
            return []
            
        return timing_events
    
    def correlate_with_session_log(self, timing_events: List[TimingEvent], 
                                 session_log_path: str) -> List[TimingEvent]:
        """
        Correlate timing events with actual session content
        """
        try:
            with open(session_log_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='replace')
                
            # Split content into chunks based on timing events
            content_pos = 0
            for i, event in enumerate(timing_events):
                if i + 1 < len(timing_events):
                    # Calculate chunk size (this is approximated)
                    next_event = timing_events[i + 1]
                    # For simplicity, divide content proportionally
                    chunk_size = max(1, len(content) // len(timing_events))
                    chunk = content[content_pos:content_pos + chunk_size]
                    content_pos += chunk_size
                else:
                    # Last chunk gets remaining content
                    chunk = content[content_pos:]
                
                event.content = chunk
                
        except FileNotFoundError:
            print(f"Error: Session log not found: {session_log_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error correlating with session log: {e}", file=sys.stderr)
            
        return timing_events

class ConversationTimestampProcessor:
    """Processes timing events to identify conversation boundaries and timestamps"""
    
    def __init__(self):
        # Patterns to identify Claude Code interactions
        self.user_prompt_patterns = [
            r'> ',  # Common prompt format
            r'\$ ',  # Shell prompt
            r'❯ ',  # Modern shell prompt
            r'➜ ',  # Oh-my-zsh prompt
        ]
        
        self.claude_response_patterns = [
            r'●',  # Claude Code bullet point
            r'I\'ll ',  # Common Claude Code response start
            r'Let me ',  # Common Claude Code response start
            r'✅',  # Success indicator
            r'❌',  # Error indicator
        ]
        
        self.tool_usage_patterns = [
            r'● (\w+)\(',  # Tool usage: ● Read(file.txt)
            r'⎿',  # Tool result indicator
            r'Running: ',  # Command execution
        ]
        
    def detect_conversation_events(self, timing_events: List[TimingEvent]) -> List[Dict]:
        """
        Detect conversation events (user input, AI responses, tool usage) from timing data
        """
        conversation_events = []
        
        for i, event in enumerate(timing_events):
            content = event.content.strip()
            if not content:
                continue
                
            # Detect user input
            if self.is_user_input(content):
                conversation_events.append({
                    'timestamp': event.timestamp,
                    'type': 'user_input',
                    'content': self.clean_content(content),
                    'raw_content': content,
                    'cumulative_time': event.cumulative_time
                })
                
            # Detect Claude response
            elif self.is_claude_response(content):
                conversation_events.append({
                    'timestamp': event.timestamp,
                    'type': 'claude_response', 
                    'content': self.clean_content(content),
                    'raw_content': content,
                    'cumulative_time': event.cumulative_time
                })
                
            # Detect tool usage
            elif self.is_tool_usage(content):
                tool_info = self.extract_tool_info(content)
                conversation_events.append({
                    'timestamp': event.timestamp,
                    'type': 'tool_usage',
                    'content': self.clean_content(content),
                    'raw_content': content,
                    'tool_name': tool_info.get('tool_name', 'unknown'),
                    'tool_args': tool_info.get('tool_args', ''),
                    'cumulative_time': event.cumulative_time
                })
                
        return conversation_events
    
    def is_user_input(self, content: str) -> bool:
        """Detect if content represents user input"""
        # Look for prompt patterns
        for pattern in self.user_prompt_patterns:
            if re.search(pattern, content):
                return True
        
        # Heuristics: short text followed by newlines might be user input
        lines = content.split('\n')
        if len(lines) <= 3 and any(line.strip() for line in lines):
            # Check if it doesn't look like Claude output
            if not any(re.search(pattern, content) for pattern in self.claude_response_patterns):
                return True
                
        return False
    
    def is_claude_response(self, content: str) -> bool:
        """Detect if content represents Claude Code response"""
        for pattern in self.claude_response_patterns:
            if re.search(pattern, content):
                return True
        return False
    
    def is_tool_usage(self, content: str) -> bool:
        """Detect if content represents tool usage"""
        for pattern in self.tool_usage_patterns:
            if re.search(pattern, content):
                return True
        return False
    
    def extract_tool_info(self, content: str) -> Dict[str, str]:
        """Extract tool name and arguments from tool usage content"""
        tool_info = {}
        
        # Try to extract tool name from patterns like "● Read(file.txt)"
        tool_match = re.search(r'● (\w+)\((.*?)\)', content)
        if tool_match:
            tool_info['tool_name'] = tool_match.group(1).lower()
            tool_info['tool_args'] = tool_match.group(2)
        
        return tool_info
    
    def clean_content(self, content: str) -> str:
        """Clean content for storage (remove escape sequences, normalize whitespace)"""
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', content)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

def load_session_metadata(meta_file_path: str) -> Optional[Dict]:
    """Load session metadata from JSON file"""
    try:
        with open(meta_file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Metadata file not found: {meta_file_path}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error loading metadata: {e}", file=sys.stderr)
        return None

def extract_timestamps_from_session(session_log: str, timing_log: str, 
                                  meta_file: str) -> List[Dict]:
    """
    Main function to extract timestamped conversation events from Claude Code session
    """
    # Load metadata to get session start time
    metadata = load_session_metadata(meta_file)
    if not metadata:
        print("Warning: Using current time as session start", file=sys.stderr)
        start_time = datetime.now()
    else:
        try:
            start_time = datetime.fromisoformat(metadata['start_time'].replace('Z', '+00:00'))
        except Exception as e:
            print(f"Error parsing start time: {e}", file=sys.stderr)
            start_time = datetime.now()
    
    # Extract timing events
    extractor = TimestampExtractor(start_time)
    timing_events = extractor.parse_script_timing_file(timing_log)
    
    if not timing_events:
        print("Error: No timing events found", file=sys.stderr)
        return []
    
    # Correlate with session content
    timing_events = extractor.correlate_with_session_log(timing_events, session_log)
    
    # Process conversation events
    processor = ConversationTimestampProcessor()
    conversation_events = processor.detect_conversation_events(timing_events)
    
    return conversation_events

def main():
    """Command line interface for timestamp extraction"""
    if len(sys.argv) != 4:
        print("Usage: python3 timestamp_utils.py <session_log> <timing_log> <meta_file>")
        print("Example: python3 timestamp_utils.py session.log timing.log meta.json")
        sys.exit(1)
    
    session_log, timing_log, meta_file = sys.argv[1:4]
    
    # Extract conversation events
    events = extract_timestamps_from_session(session_log, timing_log, meta_file)
    
    if not events:
        print("No conversation events found", file=sys.stderr)
        sys.exit(1)
    
    # Output results as JSON
    output = {
        'session_analysis': {
            'total_events': len(events),
            'user_inputs': len([e for e in events if e['type'] == 'user_input']),
            'claude_responses': len([e for e in events if e['type'] == 'claude_response']),
            'tool_usages': len([e for e in events if e['type'] == 'tool_usage']),
        },
        'events': events
    }
    
    print(json.dumps(output, indent=2, default=str))

if __name__ == "__main__":
    main()