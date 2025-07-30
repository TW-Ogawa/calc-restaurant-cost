# -*- coding: utf-8 -*-

"""
食材データとメニュー定義の整合性を検証するモジュール。
"""

import json
from menu_definitions import DISHES

def load_ingredient_prices(filepath="data/ingredient_prices.json"):
    """
    食材の単価データをJSONファイルから読み込む関数。
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "食材マスタ" in data:
                del data["食材マスタ"]
            return data
    except FileNotFoundError:
        print(f"エラー: 食材単価ファイルが見つかりません: {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"エラー: 食材単価ファイルのJSON形式が正しくありません: {filepath}")
        return {}

def get_all_ingredients_from_dishes():
    """DISHES定義からすべてのユニークな食材リストを取得する"""
    all_ingredients = set()
    for dish in DISHES.values():
        for ingredient in dish["ingredients"]:
            all_ingredients.add(ingredient)
    return all_ingredients

def validate_ingredient_data(prices_filepath="data/ingredient_prices.json"):
    """
    食材データとメニュー定義の整合性を検証する。

    1. メニュー定義にあるが、価格データにない食材 (未定義食材)
    2. 価格データにあるが、どのメニューでも使われていない食材 (未使用食材)

    Returns:
        dict: 検証結果を含む辞書
              {
                  "missing_in_prices": set, # 価格データにない食材
                  "unused_in_dishes": set  # メニューで使われていない食材
              }
    """
    print("データ検証を開始します...")

    # データの読み込み
    defined_ingredients = get_all_ingredients_from_dishes()
    price_ingredients = set(load_ingredient_prices(prices_filepath).keys())

    # 1. 未定義食材の検出
    missing_in_prices = defined_ingredients - price_ingredients

    # 2. 未使用食材の検出
    unused_in_dishes = price_ingredients - defined_ingredients

    print("データ検証が完了しました。")

    return {
        "missing_in_prices": missing_in_prices,
        "unused_in_dishes": unused_in_dishes
    }

def generate_validation_report(validation_results):
    """検証結果を整形して文字列として生成する"""
    report_lines = ["--- 検証結果 ---"]
    has_issues = False

    if validation_results["missing_in_prices"]:
        has_issues = True
        missing_items = validation_results['missing_in_prices']
        report_lines.append(f"[警告] メニューに定義されているが、価格が未設定の食材: {', '.join(missing_items)}")

        # --- 自動修復提案 ---
        report_lines.append("\n--- 自動修復提案 ---")
        report_lines.append(f"以下の内容を `data/ingredient_prices.json` に追記することで、問題を一時的に解決できます。")
        fix_suggestions = []
        for item in sorted(list(missing_items)): # ソートして順序を固定
            fix_suggestions.append(f'  "{item}": 0.0,')
        report_lines.append("{\n" + "\n".join(fix_suggestions) + "\n}")
        report_lines.append("--------------------")

    else:
        report_lines.append("✓ 価格未設定の食材はありません。")

    if validation_results["unused_in_dishes"]:
        # これは警告ではなく情報なので has_issues は True にしない
        report_lines.append(f"[情報] 現在どのメニューでも使用されていない食材: {', '.join(validation_results['unused_in_dishes'])}")
    else:
        report_lines.append("✓ 未使用の食材データはありません。")

    if not has_issues:
        report_lines.append("\n結論: データは正常です。")
    else:
        report_lines.append("\n結論: データに問題が見つかりました。修正を検討してください。")

    report_lines.append("--- 結果終わり ---")
    return "\n".join(report_lines)


if __name__ == '__main__':
    results = validate_ingredient_data()
    report = generate_validation_report(results)
    print(report)
