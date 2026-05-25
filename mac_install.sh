#!/bin/bash
# Полная установка SendScreen на Mac — SSH ключ + Quick Action без пароля

KEY="$HOME/.ssh/id_claude"
SERVER="root@23.88.109.33"

echo "=== Шаг 1: SSH ключ ==="
if [[ ! -f "$KEY" ]]; then
    ssh-keygen -t ed25519 -f "$KEY" -N "" -q
    echo "Ключ создан: $KEY"
else
    echo "Ключ уже есть: $KEY"
fi

echo "Копирую ключ на сервер (введи пароль последний раз):"
ssh-copy-id -i "$KEY.pub" "$SERVER"
if [[ $? -ne 0 ]]; then
    echo "Ошибка. Проверь подключение к серверу."
    exit 1
fi
echo "Пароль больше не нужен."

echo ""
echo "=== Шаг 2: Функция sendscreen ==="
sed -i '' '/function sendscreen/,/^}/d' ~/.zshrc 2>/dev/null
cat >> ~/.zshrc << 'ZSHEOF'

function sendscreen() {
    screencapture -s /tmp/cs_tmp.png && \
    scp -i ~/.ssh/id_claude -o StrictHostKeyChecking=no /tmp/cs_tmp.png root@23.88.109.33:~/claude_screenshots/latest.png && \
    echo "Скрин загружен" || echo "Отменено"
}
ZSHEOF
source ~/.zshrc
echo "Функция обновлена."

echo ""
echo "=== Шаг 3: Quick Action ==="
WORKFLOW="$HOME/Library/Services/SendScreen.workflow/Contents"
mkdir -p "$WORKFLOW"

cat > "$WORKFLOW/document.wflow" << 'PLIST_EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>AMApplicationBuild</key>
	<string>521</string>
	<key>AMApplicationVersion</key>
	<string>2.10</string>
	<key>AMDocumentVersion</key>
	<string>2</string>
	<key>actions</key>
	<array>
		<dict>
			<key>action</key>
			<dict>
				<key>AMAccepts</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Optional</key>
					<true/>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.string</string>
					</array>
				</dict>
				<key>AMActionVersion</key>
				<string>2.0.3</string>
				<key>AMApplication</key>
				<array>
					<string>Terminal</string>
				</array>
				<key>AMParameterProperties</key>
				<dict>
					<key>COMMAND_STRING</key>
					<dict/>
					<key>CheckedForUserDefaultShell</key>
					<dict/>
					<key>inputMethod</key>
					<dict/>
					<key>shell</key>
					<dict/>
					<key>source</key>
					<dict/>
				</dict>
				<key>AMProvides</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.string</string>
					</array>
				</dict>
				<key>ActionBundlePath</key>
				<string>/System/Library/Automator/Run Shell Script.action</string>
				<key>ActionName</key>
				<string>Run Shell Script</string>
				<key>ActionParameters</key>
				<dict>
					<key>COMMAND_STRING</key>
					<string>/usr/sbin/screencapture -s /tmp/cs_tmp.png &amp;&amp; /usr/bin/scp -i ~/.ssh/id_claude -o StrictHostKeyChecking=no /tmp/cs_tmp.png root@23.88.109.33:~/claude_screenshots/latest.png &amp;&amp; osascript -e 'display notification "Скрин отправлен в Telegram" with title "Claude"' || osascript -e 'display notification "Ошибка или отменено" with title "Claude"'</string>
					<key>CheckedForUserDefaultShell</key>
					<true/>
					<key>inputMethod</key>
					<integer>0</integer>
					<key>shell</key>
					<string>/bin/zsh</string>
					<key>source</key>
					<string></string>
				</dict>
				<key>BundleIdentifier</key>
				<string>com.apple.RunShellScript</string>
				<key>CFBundleVersion</key>
				<string>2.0.3</string>
				<key>CanShowSelectedItemsWhen</key>
				<false/>
				<key>CanShowWhenRun</key>
				<false/>
				<key>Category</key>
				<array>
					<string>AMCategoryUtilities</string>
				</array>
				<key>Class Name</key>
				<string>RunShellScriptAction</string>
				<key>InputUUID</key>
				<string>3D4A7C1B-E8F2-4D5A-9C6E-1B2D3E4F5A6B</string>
				<key>Keywords</key>
				<array>
					<string>Shell</string>
					<string>Script</string>
				</array>
				<key>OutputUUID</key>
				<string>7E8F9A1B-2C3D-4E5F-6A7B-8C9D0E1F2A3B</string>
				<key>UUID</key>
				<string>1A2B3C4D-5E6F-7A8B-9C0D-E1F2A3B4C5D6</string>
				<key>UnlockWithPassphrase</key>
				<false/>
				<key>name</key>
				<string>Run Shell Script</string>
				<key>techVersion</key>
				<string>2</string>
			</dict>
		</dict>
	</array>
	<key>connectors</key>
	<dict/>
	<key>workflowMetaData</key>
	<dict>
		<key>serviceInputTypeIdentifier</key>
		<string>com.apple.automator.no-input</string>
		<key>serviceOutputTypeIdentifier</key>
		<string>com.apple.automator.no-output</string>
		<key>serviceProcessesInput</key>
		<integer>0</integer>
		<key>workflowTypeIdentifier</key>
		<string>com.apple.automator.servicesMenu</string>
	</dict>
</dict>
</plist>
PLIST_EOF

killall pbs 2>/dev/null
/System/Library/CoreServices/pbs -update 2>/dev/null
echo "Quick Action обновлён."

echo ""
echo "=== Всё готово ==="
echo ""
echo "Осталось назначить горячую клавишу (один раз вручную):"
open "x-apple.systempreferences:com.apple.preference.keyboard?Shortcuts"
echo ""
echo "В открывшемся окне:"
echo "1. Слева выбери 'Службы'"
echo "2. Найди 'SendScreen' в списке справа"
echo "3. Нажми 'нет' рядом с ним и введи комбинацию, например Cmd+Shift+5"
