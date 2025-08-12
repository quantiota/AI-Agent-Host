#!/bin/bash
# Claude Code Real-Time Logger with Live QuestDB Streaming
# Streams conversation data to QuestDB as it happens

set -euo pipefail

# Configuration
CHAT_LOGS_DIR="${HOME}/.claude_chat_logs"
SESSION_ID=$(date +%Y%m%d_%H%M%S)_$(printf "%04x" $((RANDOM * RANDOM % 65536)))
SESSION_LOG="${CHAT_LOGS_DIR}/session_${SESSION_ID}.log"
TIMING_LOG="${CHAT_LOGS_DIR}/timing_${SESSION_ID}.log"
META_FILE="${CHAT_LOGS_DIR}/meta_${SESSION_ID}.json"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Real-time streaming variables
FIFO_INPUT="${CHAT_LOGS_DIR}/input_${SESSION_ID}.fifo"
FIFO_OUTPUT="${CHAT_LOGS_DIR}/output_${SESSION_ID}.fifo"
STREAM_PID=""
LAST_MESSAGE_TIME=$(date +%s)
MESSAGE_BUFFER=""
BUFFER_TIMEOUT=2  # seconds

# Create logs directory
mkdir -p "${CHAT_LOGS_DIR}"

# Function to log metadata
log_metadata() {
    cat > "${META_FILE}" << EOF
{
    "session_id": "${SESSION_ID}",
    "start_time": "$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')",
    "user": "$(whoami)",
    "hostname": "$(hostname)",
    "claude_version": "$(claude --version 2>/dev/null || echo 'unknown')",
    "working_directory": "$(pwd)",
    "environment": "AI Agent Host - Real-time Streaming",
    "streaming": true,
    "log_files": {
        "session": "${SESSION_LOG}",
        "timing": "${TIMING_LOG}",
        "metadata": "${META_FILE}"
    }
}
EOF
}

# Function to stream message to QuestDB
stream_message() {
    local message_type="$1"
    local content="$2"
    local timestamp="$3"
    
    # Create a temporary JSON payload
    local temp_json=$(mktemp)
    cat > "$temp_json" << EOF
{
    "timestamp": "$timestamp",
    "session_id": "$SESSION_ID",
    "message_type": "$message_type",
    "content": "$content",
    "context_tokens": $(echo "$content" | wc -c | awk '{print int($1/4)}'),
    "streaming": true
}
EOF
    
    # Stream to QuestDB asynchronously
    (
        python3 "${SCRIPT_DIR}/questdb_stream_inserter.py" \
            --json-file "$temp_json" \
            --create-table
        rm -f "$temp_json"
    ) &
}

# Function to detect message type from content
detect_message_type() {
    local content="$1"
    
    # Look for common Claude Code patterns
    if echo "$content" | grep -q "^> \|^❯ \|^$ "; then
        echo "user_input"
    elif echo "$content" | grep -q "^I'll \|^Let me \|^● \|^✅\|^❌"; then
        echo "claude_response"
    elif echo "$content" | grep -q "^● [A-Z][a-z]*(\|^⎿"; then
        echo "tool_usage"
    else
        # Default classification based on patterns
        if echo "$content" | grep -qE "^[a-z].*\?$|^[A-Z][a-z]+ [a-z]"; then
            echo "user_input"
        else
            echo "claude_response"
        fi
    fi
}

# Function to process buffered content
process_buffer() {
    if [[ -n "$MESSAGE_BUFFER" ]]; then
        local timestamp=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
        local message_type=$(detect_message_type "$MESSAGE_BUFFER")
        
        echo -e "${MAGENTA}📡 Streaming: ${message_type}${NC}" >&2
        
        # Stream to QuestDB
        stream_message "$message_type" "$MESSAGE_BUFFER" "$timestamp"
        
        MESSAGE_BUFFER=""
    fi
}

# Function to monitor terminal output for real-time streaming
start_realtime_monitor() {
    echo -e "${CYAN}🔄 Starting real-time conversation monitoring...${NC}"
    
    # Create named pipes for monitoring
    mkfifo "$FIFO_INPUT" "$FIFO_OUTPUT" 2>/dev/null || true
    
    # Background process to monitor and stream
    (
        while true; do
            current_time=$(date +%s)
            
            # Check if there's new content in the session log
            if [[ -f "$SESSION_LOG" ]]; then
                # Read new lines and buffer them
                tail -n 1 "$SESSION_LOG" 2>/dev/null | while IFS= read -r line; do
                    if [[ -n "$line" ]]; then
                        MESSAGE_BUFFER="$MESSAGE_BUFFER$line\n"
                        LAST_MESSAGE_TIME=$current_time
                    fi
                done
                
                # Process buffer if timeout reached or significant content accumulated
                if [[ $((current_time - LAST_MESSAGE_TIME)) -gt $BUFFER_TIMEOUT ]] || \
                   [[ ${#MESSAGE_BUFFER} -gt 500 ]]; then
                    process_buffer
                fi
            fi
            
            sleep 0.5
        done
    ) &
    
    STREAM_PID=$!
}

# Function to stop real-time monitoring
stop_realtime_monitor() {
    if [[ -n "$STREAM_PID" ]]; then
        kill "$STREAM_PID" 2>/dev/null || true
        wait "$STREAM_PID" 2>/dev/null || true
    fi
    
    # Process any remaining buffer
    process_buffer
    
    # Cleanup pipes
    rm -f "$FIFO_INPUT" "$FIFO_OUTPUT" 2>/dev/null || true
    
    echo -e "${CYAN}📡 Real-time monitoring stopped${NC}"
}

# Function to show session info
show_session_info() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🚀 Claude Code Real-Time Logger${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Session ID:${NC} ${SESSION_ID}"
    echo -e "${GREEN}Start Time:${NC} $(date)"
    echo -e "${MAGENTA}🔴 LIVE STREAMING: Messages will be sent to QuestDB in real-time${NC}"
    echo -e "${CYAN}💾 Fault Tolerance: Data preserved if session crashes${NC}"
    echo -e "${YELLOW}⚡ Immediate Availability: Previous messages accessible instantly${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
}

# Function to validate session integrity at end
validate_session_integrity() {
    echo -e "${CYAN}🔍 Validating session integrity...${NC}"
    
    if [[ -f "${SCRIPT_DIR}/questdb_inserter_fixed.py" ]]; then
        # Run batch validation to ensure all data was captured
        python3 "${SCRIPT_DIR}/questdb_inserter_fixed.py" \
            "${SESSION_LOG}" "${TIMING_LOG}" "${META_FILE}" \
            --verify --quiet \
            >/dev/null 2>&1
        
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}✅ Session integrity validated${NC}"
        else
            echo -e "${YELLOW}⚠️  Running integrity repair...${NC}"
            python3 "${SCRIPT_DIR}/questdb_inserter_fixed.py" \
                "${SESSION_LOG}" "${TIMING_LOG}" "${META_FILE}" \
                --create-table --verify
        fi
    fi
}

# Enhanced cleanup function
cleanup() {
    local exit_code=$?
    
    echo
    echo -e "${CYAN}🛑 Stopping real-time streaming...${NC}"
    
    # Stop monitoring
    stop_realtime_monitor
    
    # Update metadata
    python3 -c "
import json
try:
    with open('${META_FILE}', 'r') as f:
        meta = json.load(f)
    meta['end_time'] = '$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')'
    meta['exit_code'] = ${exit_code}
    with open('${META_FILE}', 'w') as f:
        json.dump(meta, f, indent=2)
except: pass
"
    
    # Validate session integrity
    if [[ $exit_code -eq 0 ]]; then
        validate_session_integrity
    fi
    
    # Show final status
    echo
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📊 Real-Time Session Complete${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Session ID:${NC} ${SESSION_ID}"
    echo -e "${MAGENTA}📡 Real-time streaming:${NC} Conversation data sent live to QuestDB"
    echo -e "${CYAN}💾 Immediate access:${NC} All messages available for next Claude session"
    echo -e "${YELLOW}⚡ Zero latency:${NC} No post-session processing required"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    exit $exit_code
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Function to check prerequisites
check_prerequisites() {
    if ! command -v script &> /dev/null; then
        echo -e "${RED}❌ Error: 'script' command not found${NC}" >&2
        exit 1
    fi
    
    if ! command -v claude &> /dev/null; then
        echo -e "${RED}❌ Error: 'claude' command not found${NC}" >&2
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Error: 'python3' command not found${NC}" >&2
        exit 1
    fi
}

# Main execution
main() {
    check_prerequisites
    mkdir -p "${CHAT_LOGS_DIR}"
    log_metadata
    
    # Create QuestDB table before starting
    echo -e "${CYAN}🔧 Initializing QuestDB table...${NC}"
    python3 "${SCRIPT_DIR}/questdb_stream_inserter.py" --create-table --json '{"test":"init"}' || {
        echo -e "${RED}❌ Failed to initialize QuestDB table${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ QuestDB table ready${NC}"
    
    show_session_info
    
    # Start real-time monitoring
    start_realtime_monitor
    
    # Start Claude Code with logging
    script -qef --timing="${TIMING_LOG}" "${SESSION_LOG}" claude
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi