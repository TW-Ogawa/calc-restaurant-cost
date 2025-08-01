import pytest
import json
import sys
import os

# 'src' ディレクトリをシステムパスに追加
# これにより、テストコードから 'src' 内のモジュールを直接インポートできる
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))


@pytest.fixture(scope="module")
def ingredient_prices():
    """
    テスト用の食材単価データを読み込むフィクスチャ。
    'module'スコープにすることで、テストモジュール内で1度だけ実行される。
    """
    filepath = "tests/test_data/test_ingredient_prices.json"
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if "食材マスタ" in data:
            del data["食材マスタ"]
        return data
