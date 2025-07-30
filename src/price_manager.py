# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime

class PriceManager:
    """
    食材価格データの管理を行うクラス。

    - 価格データの読み込み、書き込み
    - バリデーション
    - 履歴管理
    - バックアップ・復元
    """
    def __init__(self, data_path="data/ingredient_prices.json", history_path="data/price_history.json"):
        self.data_path = data_path
        self.history_path = history_path
        self.prices = self._load_prices()

    def _load_prices(self):
        """
        価格データをファイルから読み込み、バリデーションを行う内部メソッド。
        """
        if not os.path.exists(self.data_path):
            print(f"情報: 価格ファイル {self.data_path} が見つかりません。空のデータで開始します。")
            return {}

        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "食材マスタ" in data:
                del data["食材マスタ"]

            # バリデーション
            validated_data, errors = self._validate_prices(data)
            if errors:
                print("警告: 価格データに以下の問題が見つかりました。")
                for error in errors:
                    print(f"  - {error}")
            return validated_data
        except json.JSONDecodeError:
            print(f"警告: {self.data_path} のJSON形式が不正です。空のデータで開始します。")
            return {}

    def _validate_prices(self, data):
        """
        価格データのバリデーションを行う。
        - 価格が数値(int or float)であることを確認する。
        - 不正なデータは除外し、エラーメッセージを返す。
        """
        validated_data = {}
        errors = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                validated_data[key] = value
            else:
                errors.append(f"食材 '{key}' の価格 '{value}' が数値ではありません。")
        return validated_data, errors

    def get_prices(self):
        """
        現在の価格データを返す。
        """
        return self.prices

    def update_prices(self, new_prices_data):
        """
        価格データを一括更新し、ファイルに保存する。

        Args:
            new_prices_data (dict): 新しい価格データの辞書。

        Returns:
            bool: 更新が成功したかどうか。
        """
        validated_data, errors = self._validate_prices(new_prices_data)
        if errors:
            print("エラー: 更新データに問題があるため、処理を中断しました。")
            for error in errors:
                print(f"  - {error}")
            return False

        # 履歴保存
        self._archive_old_prices(validated_data.keys())

        # 更新
        self.prices.update(validated_data)

        # ファイルに書き出し
        self._save_prices_to_file()
        print("価格データが正常に更新されました。")
        return True

    def _archive_old_prices(self, updated_keys):
        """
        更新される予定の価格の現在値を履歴ファイルに保存する。
        """
        # 履歴に残すデータだけを抽出
        prices_to_archive = {key: self.prices[key] for key in updated_keys if key in self.prices}

        if not prices_to_archive:
            return # 履歴に残すデータがない場合は何もしない

        # 履歴ファイルの読み込み
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
            else:
                history_data = []
        except (json.JSONDecodeError, IOError):
            history_data = []

        # 新しい履歴エントリを作成
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "archived_prices": prices_to_archive
        }
        history_data.append(history_entry)

        # 履歴ファイルに書き込み
        try:
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"警告: 価格履歴ファイル '{self.history_path}' の書き込みに失敗しました: {e}")

    def _save_prices_to_file(self):
        """
        現在の価格データをJSONファイルに保存する。
        """
        # 元のファイル形式に合わせて '食材マスタ' の説明を追加
        data_to_save = {"食材マスタ": "グラム(g)または個数(piece)あたりの円建て単価"}
        data_to_save.update(self.prices)

        try:
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"エラー: 価格ファイル '{self.data_path}' の書き込みに失敗しました: {e}")

    def backup_prices(self, backup_suffix=".bak"):
        """
        現在の価格ファイルをバックアップする。
        """
        backup_path = self.data_path + backup_suffix
        try:
            with open(self.data_path, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())
            print(f"価格データを '{backup_path}' にバックアップしました。")
            return True
        except IOError as e:
            print(f"エラー: バックアップファイルの作成に失敗しました: {e}")
            return False

    def restore_prices_from_backup(self, backup_suffix=".bak"):
        """
        バックアップファイルから価格データを復元する。
        """
        backup_path = self.data_path + backup_suffix
        if not os.path.exists(backup_path):
            print(f"エラー: バックアップファイル '{backup_path}' が見つかりません。")
            return False

        try:
            with open(backup_path, 'rb') as src, open(self.data_path, 'wb') as dst:
                dst.write(src.read())

            # 復元後にデータを再読み込み
            self.prices = self._load_prices()
            print(f"価格データを '{backup_path}' から復元しました。")
            return True
        except IOError as e:
            print(f"エラー: 価格データの復元に失敗しました: {e}")
            return False

# テスト用の実行ブロック
if __name__ == '__main__':
    # --- テスト設定 ---
    test_data_path = "data/test_prices.json"
    test_history_path = "data/test_history.json"

    # テスト用の初期データを作成
    initial_prices = {
        "食材マスタ": "説明",
        "テスト食材A": 100,
        "テスト食材B": "invalid_price", # バリデーションテスト用
        "テスト食材C": 300.5
    }
    with open(test_data_path, 'w', encoding='utf-8') as f:
        json.dump(initial_prices, f, ensure_ascii=False, indent=2)

    print(f"--- 初期化: テストファイル '{test_data_path}' を作成しました ---")

    # --- PriceManagerのテスト ---
    pm = PriceManager(data_path=test_data_path, history_path=test_history_path)

    print("\n--- 1. 読み込みとバリデーションのテスト ---")
    prices = pm.get_prices()
    print("読み込まれた価格:")
    for k, v in prices.items():
        print(f"  {k}: {v}")
    # "テスト食材B"が除外されていることを確認

    print("\n--- 2. 価格更新のテスト ---")
    update_data = {
        "テスト食材A": 120, # 更新
        "テスト食材D": 500,  # 新規
        "テスト食材E": "bad_data" # 不正データ
    }
    print(f"更新データ: {update_data}")
    pm.update_prices(update_data) # 不正データがあるので失敗するはず

    update_data_valid = {"テスト食材A": 120, "テスト食材D": 500}
    print(f"有効な更新データ: {update_data_valid}")
    pm.update_prices(update_data_valid) # 成功するはず

    print("\n更新後の価格:")
    prices = pm.get_prices()
    for k, v in prices.items():
        print(f"  {k}: {v}")

    print("\n--- 3. 履歴ファイルの確認 ---")
    if os.path.exists(test_history_path):
        with open(test_history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
            print(f"履歴が1件記録されていることを確認: {len(history) == 1}")
            print(f"記録された古い価格: {history[0]['archived_prices']}")
    else:
        print("履歴ファイルが作成されていません。")

    print("\n--- 4. バックアップと復元のテスト ---")
    pm.backup_prices(".testbak")

    # さらに価格を変更
    pm.update_prices({"テスト食材A": 999})
    print("復元前の価格:", pm.get_prices()["テスト食材A"])

    # バックアップから復元
    pm.restore_prices_from_backup(".testbak")
    print("復元後の価格:", pm.get_prices()["テスト食材A"])
    # 価格が120に戻っていることを確認

    # --- 後片付け ---
    print("\n--- 後片付け: テストファイルを削除します ---")
    os.remove(test_data_path)
    os.remove(test_data_path + ".testbak")
    if os.path.exists(test_history_path):
        os.remove(test_history_path)
    print("テスト完了。")
