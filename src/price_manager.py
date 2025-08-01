# -*- coding: utf-8 -*-

import json
import os
import shutil
from datetime import datetime

class PriceManager:
    """
    食材価格データの管理を行うクラス。

    - 価格データの一括更新
    - 価格履歴の管理
    - 価格データのバリデーション
    - バックアップと復元
    """

    def __init__(self, data_path="data/ingredient_prices.json", history_dir="data/history", backup_dir="data/backup"):
        """
        PriceManagerを初期化する。

        Args:
            data_path (str): 現在の価格データファイルへのパス。
            history_dir (str): 価格更新履歴を保存するディレクトリ。
            backup_dir (str): バックアップファイルを保存するディレクトリ。
        """
        self.data_path = data_path
        self.history_dir = history_dir
        self.backup_dir = backup_dir

        # 必要なディレクトリが存在しない場合は作成
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)

    def validate_prices(self, prices_data):
        """
        価格データが有効かどうかを検証する。

        - '食材マスタ' キーは無視する。
        - 価格は数値（int or float）でなければならない。
        - 価格は0以上でなければならない。

        Args:
            prices_data (dict): 検証する価格データ。

        Returns:
            bool: データが有効な場合は True、無効な場合は False。
        """
        for key, value in prices_data.items():
            if key == "食材マスタ":
                continue
            if not isinstance(value, (int, float)):
                print(f"エラー: 価格 '{value}' (食材: {key}) は数値ではありません。")
                return False
            if value < 0:
                print(f"エラー: 価格 '{value}' (食材: {key}) は0以上である必要があります。")
                return False
        return True

    def update_prices(self, new_prices):
        """
        食材価格を一括で更新する。

        1. 新しい価格データをバリデーションする。
        2. 現在の価格データを履歴として保存する。
        3. 新しい価格データで現在のファイルを上書きする。

        Args:
            new_prices (dict): 更新する新しい価格データの辞書。

        Returns:
            bool: 更新が成功した場合は True、失敗した場合は False。
        """
        if not self.validate_prices(new_prices):
            return False

        # 履歴保存
        self._archive_current_prices()

        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(new_prices, f, ensure_ascii=False, indent=2)
            print("価格データが正常に更新されました。")
            return True
        except IOError as e:
            print(f"エラー: 価格ファイルの書き込みに失敗しました: {e}")
            return False

    def _archive_current_prices(self):
        """
        現在の価格データを履歴ディレクトリにコピーする。
        ファイル名はタイムスタンプを含む形式 (e.g., prices_20231027103000.json)。
        """
        if not os.path.exists(self.data_path):
            return # 元のファイルがなければ何もしない

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        history_file = os.path.join(self.history_dir, f"prices_{timestamp}.json")
        try:
            shutil.copy2(self.data_path, history_file)
            print(f"現在の価格を {history_file} に記録しました。")
        except IOError as e:
            print(f"エラー: 価格履歴の保存に失敗しました: {e}")

    def create_backup(self):
        """
        現在の価格データのバックアップを作成する。
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"backup_{timestamp}.json")
        try:
            shutil.copy2(self.data_path, backup_file)
            print(f"バックアップを作成しました: {backup_file}")
            return backup_file
        except IOError as e:
            print(f"エラー: バックアップの作成に失敗しました: {e}")
            return None

    def restore_from_backup(self, backup_file=None):
        """
        指定されたバックアップファイルから価格データを復元する。
        ファイルが指定されない場合、最新のバックアップから復元する。

        Args:
            backup_file (str, optional): 復元元のバックアップファイルパス。

        Returns:
            bool: 復元が成功した場合は True、失敗した場合は False。
        """
        if backup_file is None:
            # 最新のバックアップファイルを見つける
            backups = sorted([os.path.join(self.backup_dir, f) for f in os.listdir(self.backup_dir)], reverse=True)
            if not backups:
                print("エラー: 利用可能なバックアップがありません。")
                return False
            backup_file = backups[0]

        if not os.path.exists(backup_file):
            print(f"エラー: バックアップファイルが見つかりません: {backup_file}")
            return False

        try:
            # 復元前に現在のデータを履歴として保存
            self._archive_current_prices()
            shutil.copy2(backup_file, self.data_path)
            print(f"{backup_file} から価格データを復元しました。")
            return True
        except IOError as e:
            print(f"エラー: バックアップからの復元に失敗しました: {e}")
            return False

if __name__ == '__main__':
    # --- テスト用コード ---
    manager = PriceManager()

    # 1. バックアップ作成
    print("\n--- バックアップ作成テスト ---")
    manager.create_backup()

    # 2. 価格更新テスト (成功例)
    print("\n--- 価格更新テスト (成功) ---")
    new_prices_ok = {
      "食材マスタ": "グラム(g)または個数(piece)あたりの円建て単価",
      "キャビア": 55.0, # 更新
      "ホタテ": 28.0, # 更新
      "トリュフオイル": 15.0,
      "新食材": 100.0 # 追加
    }
    manager.update_prices(new_prices_ok)

    # 3. 価格更新テスト (失敗例: 不正なデータ型)
    print("\n--- 価格更新テスト (失敗: 不正な値) ---")
    new_prices_bad = { "キャビア": "高価" }
    manager.update_prices(new_prices_bad)

    # 4. 復元テスト
    print("\n--- バックアップ復元テスト ---")
    # manager.restore_from_backup() # 最新のバックアップから復元

    # 現在のデータを確認
    with open(manager.data_path, 'r', encoding='utf-8') as f:
        print("\n--- 現在の価格データ ---")
        print(f.read())
