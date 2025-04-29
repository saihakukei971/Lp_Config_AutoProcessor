import os
import sys
import csv
import shutil
import logging
import traceback
import json
from datetime import datetime
from pathlib import Path

class LPFolderProcessor:
    def __init__(self):
        # 実行ファイルの場所を基準にパスを設定
        self.BASE_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
        self.CSV_FOLDER_NAME = "更新するデータCSV"
        self.LOG_FOLDER_NAME = "log"
        self.DEFAULT_TEMPLATE_PATH = "\\\\rin\\rep\\営業本部\\プロジェクト\\fam\\デザイン関係\\lp\\top55_template"
        
        # 設定と Logger の初期化
        self._init_config()
        self._setup_logger()

    def _init_config(self):
        config_path = self.BASE_DIR / "config.json"
        default_settings = {
            "level": "DEBUG",
            "format": "[%(asctime)s] [%(levelname)s] (%(filename)s:%(lineno)d) %(message)s",
            "file_mode": "a",
            "encoding": "utf-8"
        }

        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.TEMPLATE_DIR = Path(config.get('template_path', self.DEFAULT_TEMPLATE_PATH))
                csv_path = config.get('csv_path', '')
                self.CSV_DIR = self.BASE_DIR / csv_path if csv_path else self.BASE_DIR / self.CSV_FOLDER_NAME
                log_path = config.get('log_path', '')
                self.LOG_DIR = self.BASE_DIR / log_path if log_path else self.BASE_DIR / self.LOG_FOLDER_NAME
                self.log_settings = config.get('log_settings', default_settings)
            else:
                self.TEMPLATE_DIR = Path(self.DEFAULT_TEMPLATE_PATH)
                self.CSV_DIR = self.BASE_DIR / self.CSV_FOLDER_NAME
                self.LOG_DIR = self.BASE_DIR / self.LOG_FOLDER_NAME
                self.log_settings = default_settings
                self._create_default_config(config_path)
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            self.TEMPLATE_DIR = Path(self.DEFAULT_TEMPLATE_PATH)
            self.CSV_DIR = self.BASE_DIR / self.CSV_FOLDER_NAME
            self.LOG_DIR = self.BASE_DIR / self.LOG_FOLDER_NAME
            self.log_settings = default_settings

    def _create_default_config(self, config_path):
        default_config = {
            "template_path": str(self.DEFAULT_TEMPLATE_PATH),
            "csv_path": self.CSV_FOLDER_NAME,
            "log_path": self.LOG_FOLDER_NAME,
            "log_settings": {
                "level": "DEBUG",
                "format": "[%(asctime)s] [%(levelname)s] (%(filename)s:%(lineno)d) %(message)s",
                "file_mode": "a",
                "encoding": "utf-8"
            }
        }
        
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)
            print(f"デフォルト設定ファイルを作成しました: {config_path}")
        except Exception as e:
            print(f"設定ファイル作成エラー: {e}")

    def _setup_logger(self):
        now = datetime.now()
        if not self.LOG_DIR.exists():
            self.LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_folder = self.LOG_DIR / f"{now.year}年{now.month:02d}月"
        log_folder.mkdir(parents=True, exist_ok=True)
        log_file = log_folder / f"{now.strftime('%Y%m%d')}.log"

        self.logger = logging.getLogger("LPProcessorLogger")
        self.logger.setLevel(getattr(logging, self.log_settings.get('level', 'DEBUG')))
        if self.logger.handlers:
            self.logger.handlers.clear()

        file_handler = logging.FileHandler(
            log_file, 
            mode=self.log_settings.get('file_mode', 'a'), 
            encoding=self.log_settings.get('encoding', 'utf-8')
        )
        formatter = logging.Formatter(
            self.log_settings.get('format', '[%(asctime)s] [%(levelname)s] (%(filename)s:%(lineno)d) %(message)s')
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def _find_csv_file(self):
        if not self.CSV_DIR.exists():
            self.CSV_DIR.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"CSVディレクトリを作成しました: {self.CSV_DIR}")

        csv_files = list(self.CSV_DIR.glob("*.csv"))
        if csv_files:
            self.logger.info(f"CSVファイルを検出: {csv_files[0].name}")
            print(f"処理開始: {csv_files[0].name}")
            return csv_files[0]
        else:
            print(f"CSVファイルが見つかりません。{self.CSV_DIR}フォルダにCSVファイルを配置してください。")
            self.logger.info("CSVファイルなし")
            return None

    def _find_template_df_folder(self):
        """テンプレート用_dfフォルダを探す"""
        try:
            for folder in self.TEMPLATE_DIR.iterdir():
                if folder.is_dir():
                    df_folder = folder / "_df"
                    if df_folder.exists() and df_folder.is_dir():
                        self.logger.info(f"テンプレート用_dfフォルダが見つかりました: {df_folder}")
                        return df_folder
            return None
        except Exception as e:
            self.logger.error(f"テンプレート用_dfフォルダ検索エラー: {e}")
            return None

    def _create_template_config_php(self):
        """新規テンプレートconfig.phpを作成"""
        return """<?php
/**
 * 設定ファイル
 */

// クライアントID（案件識別用）
$client_id = "";

// アドジャスト計測の有無（1=有効, 0=無効）
$adjust = "0";

// アドジャストURL
$adjust_url = "";

// アドジャスト用広告主ID（client_idからの自動値設定）
$advertiser_id = substr($client_id, 0, 8);

/* これより下は編集不可 ------------------------------------------------------------------- */

// SSL化（1=SSL, 0=非SSL）
$ssl = "1";
$protocol = $ssl ? "https://" : "http://";

// ドメイン設定
$domain = "";
$full_domain = $protocol . $domain;

// 共通設定ファイル読み込み
require_once($_SERVER["DOCUMENT_ROOT"] . "/common/lib/common_config.php");
?>"""

    def _create_df_folder(self, target_dir):
        """_dfフォルダを作成"""
        df_dir = target_dir / "_df"
        
        # 既に存在する場合は何もしない
        if df_dir.exists():
            return df_dir
            
        # テンプレート用の_dfフォルダを探す
        template_df = self._find_template_df_folder()
        
        if template_df:
            # テンプレートからコピー
            shutil.copytree(template_df, df_dir)
            self.logger.info(f"テンプレートから_dfフォルダをコピー: {template_df} -> {df_dir}")
        else:
            # テンプレートが見つからない場合は新規作成
            df_dir.mkdir(parents=True, exist_ok=True)
            # config.phpも作成
            config_path = df_dir / "config.php"
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(self._create_template_config_php())
            self.logger.info(f"_dfフォルダを新規作成: {df_dir}")
            
        return df_dir

    def process_csv(self, csv_path):
        """CSVファイルの処理"""
        try:
            self.logger.info(f"処理開始: {csv_path.name}")
            print(f"ファイル処理中: {csv_path.name}")

            # 複数のエンコーディングで試行
            encodings = ['utf-8-sig', 'shift_jis', 'cp932', 'euc-jp']
            rows = None
            
            for encoding in encodings:
                try:
                    with open(csv_path, 'r', encoding=encoding) as f:
                        reader = csv.reader(f)
                        rows = list(reader)
                        self.logger.info(f"エンコーディング {encoding} で読み込み成功")
                        break
                except UnicodeDecodeError:
                    continue
            
            if rows is None:
                self.logger.error("CSVファイルの読み込みに失敗しました。対応するエンコーディングがありません。")
                print("CSVファイルの読み込みに失敗しました。対応するエンコーディングがありません。")
                return False
                
            # ヘッダー行をスキップ（もしあれば）
            if rows and (rows[0][0].strip() == "LPフォルダ名（テンプレート名）" or rows[0][0].strip() == "LPフォルダ名"):
                rows = rows[1:]
            
            total_rows = len(rows)
            print(f"合計 {total_rows} 行を処理します...")
            
            for index, row in enumerate(rows, 1):
                if not row or len(row) < 5:
                    self.logger.warning(f"不正な行（カラム数不足）: {row}")
                    print(f"警告: 行 {index} のカラム数が不足しています。スキップします。")
                    continue
                   
                # 辞書形式に変換
                row_dict = {
                    'LPフォルダ名': row[0].strip(),
                    '案件名フォルダ名': row[1].strip(),
                    'クライアントID': row[2].strip(),
                    'adjustフラグ': row[3].strip(),
                    'adjustURL': row[4].strip() if len(row) > 4 else ''
                }

                print(f"処理中 [{index}/{total_rows}]: {row_dict['LPフォルダ名']}/{row_dict['案件名フォルダ名']}")
                result = self._process_row(row_dict)
                print(f"{result}")
                print("-" * 50)
                
            # 完了後、CSVを削除
            csv_path.unlink()
            self.logger.info(f"処理完了: {csv_path.name}")
            print(f"\n{csv_path.name} の処理が完了しました。")
            
            print("\n【確認方法】")
            print("1. 案件フォルダ内のconfig.phpを確認してください。")
            print("2. 「これより下は編集不可」以降が変更されていないことを確認してください。")
            print("例: alice/alice_project/config.php")

            return True

        except Exception as e:
            self.logger.error(f"CSV処理エラー: {e}\n{traceback.format_exc()}")
            print(f"エラーが発生しました: {e}")
            return False

    def _process_row(self, row):
        """CSV行単位の処理"""
        try:
            lp_folder = row.get('LPフォルダ名', '').strip()
            project_folder = row.get('案件名フォルダ名', '').strip()
            client_id = row.get('クライアントID', '').strip()
            adjust_flag = row.get('adjustフラグ', '').strip()
            adjust_url = row.get('adjustURL', '').strip()

            # バリデーション
            if adjust_flag == "1" and not adjust_url:
                self.logger.warning(f"警告: adjustフラグが1ですがURLが空です。")

            # 対象フォルダパス
            target_dir = self.TEMPLATE_DIR / lp_folder
            operation_type = ""
            
            # フォルダ作成
            if not target_dir.exists():
                target_dir.mkdir(parents=True, exist_ok=True)
                operation_type = "【新規作成】"
                self.logger.info(f"新規フォルダ作成: {target_dir}")
            else:
                operation_type = "【既存フォルダ】"

            # _dfフォルダの作成・確認
            df_dir = self._create_df_folder(target_dir)
            if not df_dir.exists():
                self.logger.error(f"_dfフォルダが存在しません: {df_dir}")
                return f"{operation_type} {lp_folder}/{project_folder} - _dfフォルダなし"

            # 案件名フォルダの作成
            new_dir = target_dir / project_folder
            if new_dir.exists():
                shutil.rmtree(new_dir)
                self.logger.info(f"既存フォルダを削除: {new_dir}")

            # _dfを案件名でコピー
            shutil.copytree(df_dir, new_dir)
            self.logger.info(f"フォルダコピー完了: {df_dir} -> {new_dir}")

            # config.phpの書き換え
            config_path = new_dir / "config.php"
            if not config_path.exists():
                # config.phpがなければ新規作成
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(self._create_template_config_php())
                self.logger.info(f"config.php新規作成: {config_path}")
            
            # config.phpの更新
            updated_values = self._update_config_php(config_path, client_id, adjust_flag, adjust_url)
            
            # 結果の整形
            result = f"{operation_type} {lp_folder}/{project_folder} - 処理成功"
            result += f"\n   → 更新されたファイル: {config_path}"
            result += f"\n   → 更新後の値:"
            result += f"\n      $client_id = \"{updated_values['client_id']}\""
            result += f"\n      $adjust = \"{updated_values['adjust']}\""
            result += f"\n      $adjust_url = \"{updated_values['adjust_url']}\""
            
            if adjust_flag == "1" and not adjust_url:
                result += f"\n   ⚠️ 警告: adjustフラグが1ですがURLが空です！"

            return result

        except Exception as e:
            self.logger.error(f"行処理エラー: {e}\n{traceback.format_exc()}")
            return f"エラー: {lp_folder}/{project_folder} - {str(e)}"

    def _update_config_php(self, config_path, client_id, adjust_flag, adjust_url):
        """config.phpを書き換える"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 「これより下は編集不可」の位置を探す
            edit_boundary = "これより下は編集不可"
            boundary_pos = content.find(edit_boundary)

            if boundary_pos == -1:
                editable_content = content
                non_editable_content = ""
            else:
                editable_content = content[:boundary_pos]
                non_editable_content = content[boundary_pos:]

            # 編集可能部分のみを書き換え
            lines = editable_content.split('\n')
            new_lines = []
            updated_values = {
                'client_id': client_id,
                'adjust': adjust_flag,
                'adjust_url': adjust_url
            }

            for line in lines:
                if '$client_id =' in line:
                    parts = line.split('=', 1)
                    if len(parts) > 1:
                        comment_part = ""
                        value_parts = parts[1].split(';', 1)
                        if len(value_parts) > 1:
                            comment_part = ";" + value_parts[1]
                        new_lines.append(f'{parts[0]}= "{client_id}"{comment_part}')
                    else:
                        new_lines.append(line)
                elif '$adjust =' in line:
                    parts = line.split('=', 1)
                    if len(parts) > 1:
                        comment_part = ""
                        value_parts = parts[1].split(';', 1)
                        if len(value_parts) > 1:
                            comment_part = ";" + value_parts[1]
                        new_lines.append(f'{parts[0]}= "{adjust_flag}"{comment_part}')
                    else:
                        new_lines.append(line)
                elif '$adjust_url =' in line:
                    parts = line.split('=', 1)
                    if len(parts) > 1:
                        comment_part = ""
                        value_parts = parts[1].split(';', 1)
                        if len(value_parts) > 1:
                            comment_part = ";" + value_parts[1]
                        new_lines.append(f'{parts[0]}= "{adjust_url}"{comment_part}')
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)

            # 編集可能部分と編集不可部分を結合
            new_content = '\n'.join(new_lines) + non_editable_content

            # 書き込み
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            self.logger.info(f"config.php更新完了: {config_path}")
            self.logger.debug(f"更新内容: $client_id = \"{client_id}\", $adjust = \"{adjust_flag}\", $adjust_url = \"{adjust_url}\"")

            return updated_values

        except Exception as e:
            self.logger.error(f"config.php更新エラー: {e}\n{traceback.format_exc()}")
            raise

    def run(self):
        """メイン実行"""
        try:
            self.logger.info("="*50)
            self.logger.info("LPフォルダ自動処理システム起動")
            self.logger.info(f"テンプレートフォルダ: {self.TEMPLATE_DIR}")
            self.logger.info(f"CSVフォルダ: {self.CSV_DIR}")
            self.logger.info(f"ログフォルダ: {self.LOG_DIR}")

            print("="*50)
            print("LPフォルダ自動処理システム")
            print("="*50)
            print(f"テンプレートフォルダ: {self.TEMPLATE_DIR}")
            print(f"CSVフォルダ: {self.CSV_DIR}")
            print(f"ログフォルダ: {self.LOG_DIR}")
            print("="*50)

            # CSVファイルをチェック
            csv_file = self._find_csv_file()
            
            if csv_file:
                # CSVファイルを処理
                success = self.process_csv(csv_file)
                if success:
                    print("\n処理が正常に完了しました。")
                else:
                    print("\n処理中にエラーが発生しました。ログを確認してください。")
            else:
                print("\nCSVファイルが見つかりませんでした。")
                print(f"CSVファイルを {self.CSV_DIR} に配置してください。")

            self.logger.info("LPフォルダ自動処理システム終了")
            self.logger.info("="*50)

            # 処理終了後、ユーザーに続行を促す
            print("\n処理が完了しました。Enterキーを押して終了してください...")
            input()

        except Exception as e:
            self.logger.error(f"システムエラー: {e}\n{traceback.format_exc()}")
            print(f"重大なエラーが発生しました: {e}")
            print("詳細はログを確認してください。")
            print("Enterキーを押して終了してください...")
            input()
            sys.exit(1)

if __name__ == "__main__":
    processor = LPFolderProcessor()
    processor.run()