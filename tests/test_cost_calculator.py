import pytest
import json
from cost_calculator import (
    load_ingredient_prices,
    calculate_dish_cost,
    calculate_course_cost
)

# --- load_ingredient_prices 関数のテスト ---

def test_load_ingredient_prices_success(tmpdir):
    """正常系: テストデータが正しく読み込めることを確認"""
    # 1. テスト用のJSONファイルを作成
    p = tmpdir.mkdir("data").join("prices.json")
    test_data = {"食材マスタ": "説明", "トマト": 100, "バジル": 50}
    p.write(json.dumps(test_data, ensure_ascii=False))

    # 2. 関数を実行
    prices = load_ingredient_prices(str(p))

    # 3. 結果を検証
    assert "トマト" in prices
    assert prices["トマト"] == 100
    assert "バジル" in prices
    assert prices["バジル"] == 50
    # "食材マスタ" キーが正しく削除されているか確認
    assert "食材マスタ" not in prices

def test_load_ingredient_prices_file_not_found():
    """異常系: ファイルが存在しない場合に FileNotFoundError が発生することを確認"""
    with pytest.raises(FileNotFoundError):
        load_ingredient_prices("non_existent_file.json")

def test_load_ingredient_prices_invalid_json(tmpdir):
    """異常系: JSON形式が不正な場合に json.JSONDecodeError が発生することを確認"""
    # 1. 不正な形式のJSONファイルを作成
    p = tmpdir.mkdir("data").join("invalid.json")
    p.write("{'key': 'value',}") # JSONとして不正 (末尾カンマ)

    # 2. 関数を実行し、例外が発生することを検証
    with pytest.raises(json.JSONDecodeError):
        load_ingredient_prices(str(p))

# --- calculate_dish_cost 関数のテスト ---

def test_calculate_dish_cost_success(ingredient_prices):
    """正常系: 料理の原価が正しく計算されることを確認"""
    # "前菜A" の期待される原価:
    # ホタテ: 80g * 25.0円/g = 2000
    # アスパラガス: 30g * 10.0円/g = 300
    # トリュフオイル: 5g * 50.0円/g = 250
    # バター: 10g * 8.0円/g = 80
    # 合計: 2000 + 300 + 250 + 80 = 2630
    expected_cost = 2630

    cost, details = calculate_dish_cost("前菜A", ingredient_prices)

    assert cost == pytest.approx(expected_cost)
    assert len(details) == 4
    assert details[0]["name"] == "ホタテ"
    assert details[0]["cost"] == 2000

def test_calculate_dish_cost_dish_not_found(ingredient_prices):
    """異常系: 存在しない料理IDを指定した場合に (0, []) が返ることを確認"""
    cost, details = calculate_dish_cost("存在しない料理", ingredient_prices)
    assert cost == 0
    assert details == []

def test_calculate_dish_cost_ingredient_not_found(ingredient_prices):
    """異常系: 食材単価が見つからない場合に、その食材費が0として計算されることを確認"""
    # "チョコレート" の単価を意図的に削除したデータを作成
    prices_missing_ingredient = ingredient_prices.copy()
    del prices_missing_ingredient["チョコレート"]

    # "デザートB" の期待される原価:
    # チョコレート: 80g * 0円/g = 0 (単価不明のため)
    # 生クリーム: 100g * 12.0円/g = 1200
    # 砂糖: 30g * 4.0円/g = 120
    # バター: 20g * 8.0円/g = 160
    # 合計: 0 + 1200 + 120 + 160 = 1480
    expected_cost = 1480

    cost, details = calculate_dish_cost("デザートB", prices_missing_ingredient)

    assert cost == pytest.approx(expected_cost)
    # 単価不明の食材情報も詳細に含まれることを確認
    assert len(details) == 4
    assert details[0]["name"] == "チョコレート"
    assert details[0]["unit_price"] == "単価不明"
    assert details[0]["cost"] == 0

# --- calculate_course_cost 関数のテスト ---

def test_calculate_course_cost_success_no_discount(ingredient_prices):
    """正常系: コースA (割引条件未達) の原価が正しく計算されることを確認"""
    # コースAの原価計算
    # 前菜A: 2630
    # スープA: じゃがいも(150*3) + 生クリーム(50*12) + ニンニク(5*5) = 450 + 600 + 25 = 1075
    # メインA_鴨: 鴨肉(150*40) + ベリー類(50*15) + バター(15*8) + 砂糖(10*4) = 6000 + 750 + 120 + 40 = 6910
    # デザートA: ベリー類(60*15) + 小麦粉(50*2) + バター(30*8) + 砂糖(40*4) + 生クリーム(20*12) = 900 + 100 + 240 + 160 + 240 = 1640
    # ---
    # 期待値メモ (あとで消す)
    # 前菜A: 2630
    # スープA: 1075
    # メインA_鴨: 6910
    # デザートA: 1640
    # ---
    # 割引前合計: 2630 + 1075 + 6910 + 1640 = 12255
    # 割引: 5% (5000円以上のため適用) -> 12255 * 0.05 = 612.75
    # 最終合計: 12255 - 612.75 = 11642.25

    # ↑ 割引ルールの実装を勘違いしていた。5000円未満で割引なしのケースを先にテストする。
    #    単価を調整して合計が5000円未満になるようにする
    prices = ingredient_prices.copy()
    prices["鴨肉"] = 10.0 # 単価を大幅に下げる
    # メインA_鴨(調整後): 鴨肉(150*10) + ... = 1500 + 750 + 120 + 40 = 2410
    # 割引前合計(調整後): 2630 + 1075 + 2410 + 1640 = 7755
    # ↑まだ5000円以上なので、もっと下げる
    prices["ホタテ"] = 5.0
    # 前菜A(調整後): ホタテ(80*5) + ... = 400 + 300 + 250 + 80 = 1030
    # 割引前合計(調整後): 1030 + 1075 + 2410 + 1640 = 6155
    # ↑まだ高い
    prices["フォアグラ"] = 10.0 # 使ってないけど念のため
    prices["キャビア"] = 10.0 # 使ってないけど念のため
    prices["仔羊肉"] = 10.0 # 使ってないけど念のため
    # 再計算
    # 前菜A: 1030
    # スープA: 1075
    # メインA_鴨: 2410
    # デザートA: 1640
    # 合計: 6155 ... うーん、計算ロジック側の割引条件を >= 15000 に一時的に変更してテストするか？
    # いや、テストデータ側で完結させるべき。単価をもっと大胆に下げる。
    prices = {key: 1.0 for key in ingredient_prices}
    # これなら合計は食材の総量になるはず。
    # 前菜A: 80+30+5+10 = 125
    # スープA: 150+50+5 = 205
    # メインA_鴨: 150+50+15+10 = 225
    # デザートA: 60+50+30+40+20 = 200
    # 合計: 125 + 205 + 225 + 200 = 755
    subtotal_cost = 755
    expected_total_cost = 755 # 5000円未満なので割引なし

    result = calculate_course_cost("コースA", prices)

    assert result is not None
    assert result["subtotal_cost"] == pytest.approx(subtotal_cost)
    assert result["discount_info"]["applied"] is False
    assert result["discount_info"]["discount_amount"] == 0
    assert result["total_cost"] == pytest.approx(expected_total_cost)


def test_calculate_course_cost_success_with_discount(ingredient_prices):
    """正常系: コースA (割引条件達成) とコースBの原価が正しく計算されることを確認"""
    # --- コースA (5%割引) ---
    # 割引前合計: 12255 (上のテストで計算済み)
    # 割引額: 12255 * 0.05 = 612.75
    # 最終合計: 12255 - 612.75 = 11642.25
    expected_subtotal_a = 12255
    expected_discount_a = 612.75
    expected_total_a = 11642.25

    result_a = calculate_course_cost("コースA", ingredient_prices)
    assert result_a is not None
    assert result_a["subtotal_cost"] == pytest.approx(expected_subtotal_a)
    assert result_a["discount_info"]["applied"] is True
    assert result_a["discount_info"]["discount_amount"] == pytest.approx(expected_discount_a)
    assert result_a["total_cost"] == pytest.approx(expected_total_a)

    # --- コースB (500円固定割引) ---
    # 前菜B: キャビア(15*200) + ホタテ(60*25) + トリュフオイル(8*50) = 3000 + 1500 + 400 = 4900
    # スープB: フォアグラ(50*150) + ジャガイモ(100*3) + 生クリーム(70*12) = 7500 + 300 + 840 = 8640
    # メインB_仔羊: 仔羊肉(180*60) + ローズマリー(5*30) + ニンニク(10*5) + ジャガイモ(80*3) + バター(10*8) = 10800 + 150 + 50 + 240 + 80 = 11320
    # デザートB: チョコレート(80*18) + 生クリーム(100*12) + 砂糖(30*4) + バター(20*8) = 1440 + 1200 + 120 + 160 = 2920
    # 割引前合計: 4900 + 8640 + 11320 + 2920 = 27780
    # 割引額: 500 (固定)
    # 最終合計: 27780 - 500 = 27280
    expected_subtotal_b = 27780
    expected_discount_b = 500
    expected_total_b = 27280

    result_b = calculate_course_cost("コースB", ingredient_prices)
    assert result_b is not None
    assert result_b["subtotal_cost"] == pytest.approx(expected_subtotal_b)
    assert result_b["discount_info"]["applied"] is True
    assert result_b["discount_info"]["discount_amount"] == pytest.approx(expected_discount_b)
    assert result_b["total_cost"] == pytest.approx(expected_total_b)


def test_calculate_course_cost_course_not_found(ingredient_prices):
    """異常系: 存在しないコースIDを指定した場合に None が返ることを確認"""
    result = calculate_course_cost("存在しないコース", ingredient_prices)
    assert result is None
