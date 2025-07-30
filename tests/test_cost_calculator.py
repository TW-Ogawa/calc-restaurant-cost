# -*- coding: utf-8 -*-

import pytest
import json
from cost_calculator import (
    load_ingredient_prices,
    calculate_dish_cost,
    calculate_course_cost
)

# --- load_ingredient_prices 関数のテスト ---

def test_load_ingredient_prices_success(ingredient_prices):
    """
    正常に食材価格データを読み込めるかテスト
    """
    # conftest.pyのingredient_pricesフィクスチャがそのまま期待値になる
    # '食材マスタ' キーが除外されているかも確認
    assert "食材マスタ" not in ingredient_prices
    assert ingredient_prices["ホタテ"] == 25.5

def test_load_ingredient_prices_file_not_found():
    """
    ファイルが存在しない場合に FileNotFoundError が発生するかテスト
    """
    with pytest.raises(FileNotFoundError):
        load_ingredient_prices("non_existent_file.json")

def test_load_ingredient_prices_invalid_json(invalid_json_file):
    """
    JSON形式が不正な場合に json.JSONDecodeError が発生するかテスト
    """
    with pytest.raises(json.JSONDecodeError):
        load_ingredient_prices(invalid_json_file)

def test_load_ingredient_prices_empty_file(empty_json_file):
    """
    空のJSONファイルが正しく読み込まれるかテスト
    """
    prices = load_ingredient_prices(empty_json_file)
    assert prices == {}

# --- calculate_dish_cost 関数のテスト ---

def test_calculate_dish_cost_success(ingredient_prices):
    """
    正常に料理の原価が計算できるかテスト
    """
    # 前菜A: ホタテ(80g) * 25.5円 + アスパラガス(30g) * 5.0円 + トリュフオイル(5g) * 15.0円 + バター(10g) * 2.0円
    # = 2040 + 150 + 75 + 20 = 2285
    cost, details = calculate_dish_cost("前菜A", ingredient_prices)
    assert cost == 2285
    assert len(details) == 4
    assert details[0]["name"] == "ホタテ"
    assert details[0]["cost"] == 2040

def test_calculate_dish_cost_ingredient_not_found(ingredient_prices):
    """
    一部の食材単価が見つからない場合に計算できるかテスト
    """
    # "バター"を価格リストから削除
    del ingredient_prices["バター"]
    # 前菜A: バターのコストが0になる
    # 2285 - 20 = 2265
    cost, details = calculate_dish_cost("前菜A", ingredient_prices)
    assert cost == 2265
    assert details[3]["name"] == "バター"
    assert details[3]["unit_price"] == "単価不明"
    assert details[3]["cost"] == 0

def test_calculate_dish_cost_dish_not_found(ingredient_prices):
    """
    存在しない料理IDを指定した場合のテスト
    """
    cost, details = calculate_dish_cost("存在しない料理", ingredient_prices)
    assert cost == 0
    assert details == []

# --- calculate_course_cost 関数のテスト ---

def test_calculate_course_cost_success_no_discount(ingredient_prices):
    """
    正常にコース原価が計算できるかテスト（割引なし）
    """
    # コースAの各料理の原価を計算
    # 前菜A: 2285
    # スープA: じゃがいも(150*1.5) + 生クリーム(50*3.5) + ニンニク(5*2.0) = 225 + 175 + 10 = 410
    # メインA: 鴨肉(150*30) + ベリー(50*7) + バター(15*2) + 砂糖(10*0.8) = 4500 + 350 + 30 + 8 = 4888
    # デザートA: ベリー(60*7) + 小麦粉(50*0.5) + バター(30*2) + 砂糖(40*0.8) + 生クリーム(20*3.5) = 420 + 25 + 60 + 32 + 70 = 607
    # 合計: 2285 + 410 + 4888 + 607 = 8190
    # 割引ルール 'standard' は5000円以上で5%引き
    # 割引額: 8190 * 0.05 = 409.5
    # 最終合計: 8190 - 409.5 = 7780.5
    result = calculate_course_cost("コースA", ingredient_prices)
    assert result["course_name"] == "コースA"
    assert result["subtotal_cost"] == 8190
    assert result["discount_info"]["applied"] is True
    assert result["discount_info"]["discount_amount"] == 409.5
    assert result["total_cost"] == 7780.5

def test_calculate_course_cost_with_fixed_discount(ingredient_prices):
    """
    固定額割引が適用されるかテスト
    """
    # コースBの各料理の原価を計算
    # 前菜B: キャビア(15*50) + ホタテ(60*25.5) + トリュフオイル(8*15) = 750 + 1530 + 120 = 2400
    # スープB: フォアグラ(50*60) + じゃがいも(100*1.5) + 生クリーム(70*3.5) = 3000 + 150 + 245 = 3395
    # メインB: 仔羊(180*45) + ローズマリー(5*3) + ニンニク(10*2) + じゃがいも(80*1.5) + バター(10*2) = 8100 + 15 + 20 + 120 + 20 = 8275
    # デザートB: チョコ(80*8) + 生クリーム(100*3.5) + 砂糖(30*0.8) + バター(20*2) = 640 + 350 + 24 + 40 = 1054
    # 合計: 2400 + 3395 + 8275 + 1054 = 15124
    # 割引ルール 'premium' は固定500円引き
    # 最終合計: 15124 - 500 = 14624
    result = calculate_course_cost("コースB", ingredient_prices)
    assert result["course_name"] == "コースB"
    assert result["subtotal_cost"] == 15124
    assert result["discount_info"]["applied"] is True
    assert result["discount_info"]["discount_amount"] == 500
    assert result["total_cost"] == 14624

def test_calculate_course_cost_course_not_found(ingredient_prices):
    """
    存在しないコースIDを指定した場合のテスト
    """
    result = calculate_course_cost("存在しないコース", ingredient_prices)
    assert result is None

def test_calculate_course_cost_discount_not_applied(ingredient_prices, monkeypatch):
    """
    割引条件を満たさず、割引が適用されないことをテスト
    """
    # 割引条件(5000円以上)を満たさないコースを動的に定義
    test_courses = {
        "コースC": {
            "description": "割引条件を満たさないテスト用コース",
            "dishes": ["スープA"], # スープAの原価は410円
            "discount_rule": "standard"
        }
    }
    # DISHESもモンキーパッチで渡す
    from menu_definitions import DISHES
    monkeypatch.setattr("cost_calculator.COURSES", test_courses)
    monkeypatch.setattr("cost_calculator.DISHES", DISHES)

    result = calculate_course_cost("コースC", ingredient_prices)
    assert result is not None
    assert result["subtotal_cost"] == 410
    assert result["discount_info"]["applied"] is False
    assert result["discount_info"]["discount_amount"] == 0
    assert result["total_cost"] == 410
