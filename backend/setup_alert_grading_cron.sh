#!/bin/bash
# Setup automated alert grading on VPS
# Runs daily at 2 AM to grade previous day's alerts

BACKEND_DIR="/root/sporttrader/backend"
CRON_LOG="/root/sporttrader/logs/alert_grading_cron.log"

echo "Setting up Alert Grading Automation..."
echo "======================================"

# Create logs directory
mkdir -p /root/sporttrader/logs

# Create cron job entry
CRON_COMMAND="0 2 * * * cd $BACKEND_DIR && /usr/bin/python3 utils/grade_alerts.py >> $CRON_LOG 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "grade_alerts.py"; then
    echo "⚠️  Alert grading cron job already exists"
    echo "Current cron jobs:"
    crontab -l | grep "grade_alerts"
else
    # Add cron job
    (crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -
    echo "✅ Added alert grading cron job"
    echo "   Schedule: Daily at 2:00 AM"
    echo "   Script: $BACKEND_DIR/utils/grade_alerts.py"
    echo "   Log: $CRON_LOG"
fi

echo ""
echo "Testing alert grading script..."
cd $BACKEND_DIR
python3 utils/grade_alerts.py

echo ""
echo "✅ Alert grading automation setup complete!"
echo ""
echo "To view cron jobs: crontab -l"
echo "To view logs: tail -f $CRON_LOG"
