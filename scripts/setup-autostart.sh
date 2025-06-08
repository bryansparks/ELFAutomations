#!/bin/bash

echo "=== Setting up Auto-Start for ELF Automations ==="
echo

# Create LaunchAgent for OrbStack auto-start
echo "Creating LaunchAgent to auto-start OrbStack..."

PLIST_FILE="$HOME/Library/LaunchAgents/com.elfautomations.orbstack.plist"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.elfautomations.orbstack</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>-a</string>
        <string>OrbStack</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/orbstack-autostart.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/orbstack-autostart-error.log</string>
</dict>
</plist>
EOF

# Load the LaunchAgent
launchctl load "$PLIST_FILE" 2>/dev/null || launchctl unload "$PLIST_FILE" && launchctl load "$PLIST_FILE"

echo "✓ OrbStack will now auto-start on login"
echo
echo "To disable auto-start later, run:"
echo "  launchctl unload $PLIST_FILE"
echo "  rm $PLIST_FILE"
echo

# Also ensure OrbStack is set to start at login via its own settings
echo "IMPORTANT: Also check OrbStack preferences:"
echo "1. Open OrbStack"
echo "2. Go to Settings/Preferences"
echo "3. Enable 'Start at login'"
echo "4. Ensure 'Start Kubernetes' is enabled"
