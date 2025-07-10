#!/bin/bash
# Setup cron job for team improvement loop

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create log directory
mkdir -p "$DIR/logs"

# Add cron job
(crontab -l 2>/dev/null; echo "0 2 * * * cd $DIR && /usr/bin/python3 run_improvement_loop.py >> logs/improvement_loop.log 2>&1") | crontab -

echo "Cron job scheduled for daily improvement cycles"
echo "Schedule: 0 2 * * *"
echo "Logs will be written to: $DIR/logs/improvement_loop.log"

# To remove the cron job, run:
# crontab -l | grep -v "run_improvement_loop.py" | crontab -
