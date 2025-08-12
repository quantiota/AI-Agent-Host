#!/bin/bash
# Claude Code Session Logger - Docker Compatible Version
# Captures complete terminal sessions with timing for conversation parsing

set -euo pipefail

# Configuration
CHAT_LOGS_DIR="${HOME}/.claude_chat_logs"
# Generate session ID without uuidgen - use timestamp + random number
SESSION_ID=$(date +%Y%m%d_%H%M%S)_$(printf "%04x" $((RANDOM * RANDOM % 65536)))
SESSION_LOG="${CHAT_LOGS_DIR}/session_${SESSION_ID}.log"
TIMING_LOG="${CHAT_LOGS_DIR}/timing_${SESSION_ID}.log"
META_FILE="${CHAT_LOGS_DIR}/meta_${SESSION_ID}.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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
    "environment": "AI Agent Host - Docker",
    "log_files": {
        "session": "${SESSION_LOG}",
        "timing": "${TIMING_LOG}",
        "metadata": "${META_FILE}"
    }
}
EOF
}

# Function to update metadata on exit
update_metadata_on_exit() {
    local exit_code=$?
    local end_time=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
    
    # Update metadata with end time and exit status
    python3 -c "
import json
import sys

try:
    with open('${META_FILE}', 'r') as f:
        meta = json.load(f)
    
    meta['end_time'] = '${end_time}'
    meta['exit_code'] = ${exit_code}
    meta['session_duration'] = 'calculated'
    
    with open('${META_FILE}', 'w') as f:
        json.dump(meta, f, indent=2)
        
    print('Metadata updated successfully')
except Exception as e:
    print(f'Failed to update metadata: {e}', file=sys.stderr)
    sys.exit(1)
"
}

# Function to show session info
show_session_info() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🤖 Claude Code Session Logger (Docker)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Session ID:${NC} ${SESSION_ID}"
    echo -e "${GREEN}Start Time:${NC} $(date)"
    echo -e "${GREEN}Log Files:${NC}"
    echo -e "  📝 Session: ${SESSION_LOG}"
    echo -e "  ⏱️  Timing:  ${TIMING_LOG}"
    echo -e "  📊 Meta:    ${META_FILE}"
    echo -e "${YELLOW}💡 This session will be automatically parsed for chat history${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo
}

# Function to show exit info
show_exit_info() {
    local exit_code=$1
    echo
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📋 Claude Code Session Complete${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Session ID:${NC} ${SESSION_ID}"
    echo -e "${GREEN}End Time:${NC} $(date)"
    if [[ $exit_code -eq 0 ]]; then
        echo -e "${GREEN}Status:${NC} Success ✅"
    else
        echo -e "${RED}Status:${NC} Error (exit code: $exit_code) ❌"
    fi
    echo -e "${GREEN}Ready for parsing:${NC} Log files captured"
    echo
    echo -e "${YELLOW}💡 To parse this session into chat history:${NC}"
    echo -e "   python3 questdb_inserter_fixed.py ${SESSION_LOG} ${TIMING_LOG} ${META_FILE} --create-table --verify --verbose"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Cleanup function
cleanup() {
    local exit_code=$?
    update_metadata_on_exit
    show_exit_info $exit_code
    exit $exit_code
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Function to check prerequisites
check_prerequisites() {
    # Check if script command is available
    if ! command -v script &> /dev/null; then
        echo -e "${RED}❌ Error: 'script' command not found${NC}" >&2
        echo -e "${YELLOW}💡 Install with: apt-get install bsdutils${NC}" >&2
        exit 1
    fi
    
    # Check if claude is available
    if ! command -v claude &> /dev/null; then
        echo -e "${RED}❌ Error: 'claude' command not found${NC}" >&2
        echo -e "${YELLOW}💡 Make sure Claude Code is installed and in PATH${NC}" >&2
        exit 1
    fi
    
    # Check write permissions
    if [[ ! -w "$(dirname "${CHAT_LOGS_DIR}")" ]]; then
        echo -e "${RED}❌ Error: Cannot write to logs directory${NC}" >&2
        echo -e "${YELLOW}💡 Check permissions for: ${CHAT_LOGS_DIR}${NC}" >&2
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Verbose logging"
    echo "  -d, --dir DIR  Custom logs directory (default: ~/.claude_chat_logs)"
    echo
    echo "Examples:"
    echo "  $0                    # Start Claude Code with logging"
    echo "  $0 -d /tmp/logs       # Use custom log directory"
    echo
    echo "Log files will be created with unique session ID for each run."
}

# Parse command line arguments
VERBOSE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--dir)
            CHAT_LOGS_DIR="$2"
            SESSION_LOG="${CHAT_LOGS_DIR}/session_${SESSION_ID}.log"
            TIMING_LOG="${CHAT_LOGS_DIR}/timing_${SESSION_ID}.log"
            META_FILE="${CHAT_LOGS_DIR}/meta_${SESSION_ID}.json"
            shift 2
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}" >&2
            show_usage >&2
            exit 1
            ;;
    esac
done

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Main execution
main() {
    # Check prerequisites
    check_prerequisites
    
    # Create logs directory
    mkdir -p "${CHAT_LOGS_DIR}"
    
    # Log session metadata
    log_metadata
    
    # Create QuestDB table before starting
    echo -e "${CYAN}🔧 Initializing QuestDB table...${NC}"
    python3 "${SCRIPT_DIR}/questdb_inserter_fixed.py" /tmp/dummy.log /tmp/dummy.log /tmp/dummy.json --create-table --quiet || {
        echo -e "${RED}❌ Failed to initialize QuestDB table${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ QuestDB table ready${NC}"
    
    # Show session info
    show_session_info
    
    # Start Claude Code with script logging
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}🚀 Starting Claude Code with verbose logging...${NC}"
        script -qef --timing="${TIMING_LOG}" "${SESSION_LOG}" claude
    else
        script -qef --timing="${TIMING_LOG}" "${SESSION_LOG}" claude
    fi
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi