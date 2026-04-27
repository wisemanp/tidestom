#!/bin/bash
#
# Daily release script for TiDES staging area
# This script runs the release_staged management command daily
#
# Usage:
#   1. Make executable: chmod +x daily_release.sh
#   2. Add to crontab: 0 2 * * * /path/to/daily_release.sh
#

# Set paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/releases.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Timestamp for logging
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log start
echo "[$TIMESTAMP] Starting daily release process..." >> "$LOG_FILE"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment if it exists
if [ -d "tom_env" ]; then
    source tom_env/bin/activate
fi

# Run the release command
python manage.py release_staged >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

# Log completion
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
if [ $EXIT_CODE -eq 0 ]; then
    echo "[$TIMESTAMP] Daily release completed successfully" >> "$LOG_FILE"
else
    echo "[$TIMESTAMP] Daily release failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "----------------------------------------" >> "$LOG_FILE"

exit $EXIT_CODE
