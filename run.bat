@echo off
chcp 65001 > nul
title LPフォルダ自動処理システム

rem カレントディレクトリをバッチファイルのある場所に設定
cd /d "%~dp0"

echo ======================================================
echo LPフォルダ自動処理システム 起動中...
echo ======================================================
echo.

rem 埋め込みPythonの場所
set PYTHON_DIR=%~dp0PythonRun
set PYTHON_EXE=%PYTHON_DIR%\python.exe
set SCRIPT_PATH=%~dp0LPFolderProcessor.py

rem Pythonが存在するか確認
if not exist "%PYTHON_EXE%" (
    echo エラー: Pythonが見つかりません。
    echo PythonRunフォルダが正しく配置されているか確認してください。
    echo パス: %PYTHON_EXE%
    pause
    exit /b 1
)

rem 処理スクリプトが存在するか確認
if not exist "%SCRIPT_PATH%" (
    echo エラー: 処理スクリプトが見つかりません。
    echo LPFolderProcessor.pyが正しく配置されているか確認してください。
    echo パス: %SCRIPT_PATH%
    pause
    exit /b 1
)

rem 必要なフォルダを作成
if not exist "%~dp0log" mkdir "%~dp0log"
if not exist "%~dp0更新するデータCSV" mkdir "%~dp0更新するデータCSV"

rem Pythonスクリプトを実行
echo Pythonスクリプトを実行中...
echo.
"%PYTHON_EXE%" "%SCRIPT_PATH%"

rem スクリプトの終了コードを確認
if %errorlevel% neq 0 (
    echo.
    echo エラーが発生しました。上記のメッセージを確認してください。
    pause
)

exit /b 0