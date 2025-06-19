#!/bin/bash

# Sophia-Capture 빌드 스크립트
echo "🛠 Sophia-Capture 빌드 시작..."

# 기존 빌드 파일 삭제
echo "🗑 기존 빌드 파일 삭제..."
rm -rf build/ dist/ sophia.spec


# 아이콘 경로 (Python으로 절대경로 처리)
ICON_PATH=$(python -c "import os; print(os.path.abspath('src/sophia_capture.ico'))")

# PyInstaller 실행
echo "🚀 PyInstaller 실행..."
PLUGINS_PATH=$(python -c "import PySide6; import os; print(os.path.join(os.path.dirname(PySide6.__file__), 'plugins'))")
echo "PLUGINS_PATH: $PLUGINS_PATH"

pyinstaller --noconsole --onefile --icon="$ICON_PATH" --add-data "${PLUGINS_PATH}/platforms;platforms" src/sophia.py

# 실행 파일 이름 설정
TARGET_NAME="sophia"
EXT=""

# OS에 따라 확장자 설정
case "$OSTYPE" in
  msys*|cygwin*|win32*)
    EXT=".exe"
    ;;
esac

OUTPUT_PATH="dist/${TARGET_NAME}${EXT}"

# 빌드 완료 메시지
if [ -f "$OUTPUT_PATH" ]; then
    echo "✅ 빌드 완료: $OUTPUT_PATH"
    mkdir -p "$HOME/bin"
    cp "$OUTPUT_PATH" "$HOME/bin/${TARGET_NAME}${EXT}"
else
    echo "❌ 빌드 실패!"
fi
