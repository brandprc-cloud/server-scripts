#!/bin/bash
set -e

echo "=== Настройка голосового ввода ==="

# 1. Убрать дубли из .zprofile
sed -i '' '/pgrep skhd/d' ~/.zprofile 2>/dev/null
echo "✓ .zprofile очищен"

# 2. Убедиться что whisper-dictate.sh существует и корректен
cat > ~/whisper-dictate.sh << 'SCRIPT'
#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
MODEL="$HOME/whisper-models/ggml-medium.bin"
TMPWAV="/tmp/whisper_rec_$$.wav"
TMPOUT="/tmp/whisper_out_$$"

echo "Говори... (2 сек тишины = стоп)" >&2
rec -r 16000 -c 1 -e signed -b 16 "$TMPWAV" silence 1 0.1 3% 1 2.0 3% 2>/dev/null
echo "Распознаю..." >&2
whisper-cli -m "$MODEL" -l ru --no-timestamps --no-prints -otxt -of "$TMPOUT" -f "$TMPWAV" 2>/dev/null

TEXT=$(cat "${TMPOUT}.txt" 2>/dev/null | tr -d '\n' | sed 's/^[[:space:]]*//')
rm -f "$TMPWAV" "${TMPOUT}.txt"

if [ -n "$TEXT" ]; then
    echo "$TEXT" | pbcopy
    osascript -e 'tell application "System Events" to keystroke "v" using command down'
    echo "Готово: $TEXT" >&2
else
    echo "Ничего не распознано" >&2
fi
SCRIPT
chmod +x ~/whisper-dictate.sh
echo "✓ whisper-dictate.sh обновлён"

# 3. Убедиться что skhdrc настроен
echo 'alt - space : bash ~/whisper-dictate.sh' > ~/.skhdrc
echo "✓ skhdrc настроен (Alt+Space)"

# 4. Создать LaunchAgent для автозапуска skhd
PLIST=~/Library/LaunchAgents/com.koekeishiya.skhd.plist
mkdir -p ~/Library/LaunchAgents

/usr/libexec/PlistBuddy -c "Add :Label string com.koekeishiya.skhd" \
  -c "Add :ProgramArguments array" \
  -c "Add :ProgramArguments:0 string /opt/homebrew/bin/skhd" \
  -c "Add :RunAtLoad bool true" \
  -c "Add :KeepAlive bool true" \
  "$PLIST" 2>/dev/null && echo "✓ LaunchAgent создан" || echo "✓ LaunchAgent уже существует"

# 5. Остановить старый skhd если есть, загрузить через launchctl
pkill skhd 2>/dev/null || true
sleep 1
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
sleep 2

if pgrep skhd > /dev/null; then
    echo "✓ skhd запущен и будет стартовать при входе"
else
    echo "✗ skhd не запустился — попробуй запустить вручную: skhd &"
fi

echo ""
echo "=== Осталось одно ручное действие ==="
echo "System Settings → Privacy & Security → Accessibility"
echo "Нажми + и добавь: /opt/homebrew/bin/skhd"
echo "Без этого вставка текста (Cmd+V) работать не будет."
echo ""
echo "После этого нажми Alt+Space и скажи что-нибудь."
