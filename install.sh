#!/bin/bash
# Simple installation script for Speech-to-Text

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$HOME/.config/autostart/speech-to-text.desktop"

echo "🔧 Installing Speech-to-Text autostart..."

# Create autostart directory if it doesn't exist
mkdir -p "$HOME/.config/autostart"

# Create desktop entry
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Speech-to-Text
Comment=Global speech-to-text with F1 hotkey
Exec=python3 "$SCRIPT_DIR/stt.py"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
Categories=Utility;
EOF

echo "✅ Created autostart entry: $DESKTOP_FILE"
echo "📋 The app will now start automatically when you log in"
echo "🎤 Press F1 to record, ESC to exit"
echo ""
echo "💡 Don't forget to set your API key:"
echo "   export OPENAI_API_KEY=""
