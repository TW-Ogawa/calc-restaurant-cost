import pytest
import json
import sys
import os

# 'src' ディレクトリをPythonのパスに追加
# これにより、テストファイルから 'src' 以下のモジュールを直接importできるようになる
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

@pytest.fixture
def ingredient_prices():
    """
    テスト用の食材価格データを読み込むフィクスチャ。
    テスト実行時にこの関数が呼び出され、戻り値がテスト関数に渡される。
    """
    filepath = os.path.join(os.path.dirname(__file__), "test_data/test_ingredient_prices.json")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if "食材マスタ" in data:
            del data["食材マスタ"]
        return data

@pytest.fixture
def invalid_json_file(tmp_path):
    """
    不正なJSON形式のテストファイルを作成するフィクスチャ。
    tmp_path は pytest が提供する一時ディレクトリのパス。
    """
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("this is not a valid json")
    return str(invalid_file)

@pytest.fixture
def empty_json_file(tmp_path):
    """
    空のJSONファイルを作成するフィクスチャ。
    """
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("{}")
    return str(empty_file)
