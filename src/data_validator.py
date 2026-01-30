# -*- coding: utf-8 -*-

from difflib import get_close_matches

def get_all_ingredients_from_dishes(dishes):
    """
    すべての料理定義から使用されている食材のセットを取得する。

    Args:
        dishes (dict): 料理の定義データ (menu_definitions.DISHES)。

    Returns:
        set: 使用されている全食材名のセット。
    """
    used_ingredients = set()
    for dish_info in dishes.values():
        used_ingredients.update(dish_info["ingredients"].keys())
    return used_ingredients

def validate_ingredient_data(used_ingredients, defined_prices):
    """
    食材データと単価データの整合性を検証する。

    Args:
        used_ingredients (set): 料理定義で使用されている食材のセット。
        defined_prices (set): 単価定義に存在する食材のセット。

    Returns:
        dict: 検証結果を含む辞書。
              'missing_in_prices': 単価定義にない食材のリスト。
              'unused_in_dishes': 料理で使われていない食材のリスト。
    """
    missing_in_prices = sorted(list(used_ingredients - defined_prices))
    unused_in_dishes = sorted(list(defined_prices - used_ingredients))

    return {
        "missing_in_prices": missing_in_prices,
        "unused_in_dishes": unused_in_dishes
    }

def suggest_similar_ingredients(ingredient_name, all_price_names):
    """
    未定義の食材名に似た名前の食材を単価定義から探して提案する。

    Args:
        ingredient_name (str): 未定義の食材名。
        all_price_names (list): 単価定義に存在する全食材名のリスト。

    Returns:
        list: 類似する食材名のリスト（最大3件）。
    """
    return get_close_matches(ingredient_name, all_price_names, n=3, cutoff=0.6)

def report_validation_results(validation_results, all_price_names):
    """
    検証結果を整形して表示する。

    Args:
        validation_results (dict): validate_ingredient_data の戻り値。
        all_price_names (list): 単価定義に存在する全食材名のリスト。

    Returns:
        str: 整形されたレポート文字列。
    """
    report_lines = []
    has_errors = False

    if validation_results["missing_in_prices"]:
        has_errors = True
        report_lines.append("【エラー】単価が未定義の食材があります:")
        for item in validation_results["missing_in_prices"]:
            suggestions = suggest_similar_ingredients(item, all_price_names)
            line = f"  - '{item}'"
            if suggestions:
                line += f" (もしかして: {', '.join(suggestions)} ?)"
            report_lines.append(line)

    if validation_results["unused_in_dishes"]:
        report_lines.append("\n【情報】現在使用されていない食材単価:")
        for item in validation_results["unused_in_dishes"]:
            report_lines.append(f"  - '{item}'")

    if not has_errors:
        report_lines.append("【成功】すべての食材の単価が定義されています。")

    return "\n".join(report_lines)

# --- テスト用実行ブロック ---
if __name__ == '__main__':
    # テスト用のダミーデータ
    from menu_definitions import DISHES
    from cost_calculator import load_ingredient_prices

    print("--- データ検証テスト開始 ---")

    # 1. 実際のデータを読み込む
    try:
        ingredient_prices = load_ingredient_prices("../data/ingredient_prices.json")
        # テストのために意図的に不整合なデータを作成
        # 'ホタテ'を'帆立'に、'バター'を削除
        DISHES["前菜A"]["ingredients"]["帆立"] = DISHES["前菜A"]["ingredients"].pop("ホタテ")
        DISHES["メインA_鴨"]["ingredients"].pop("バター")
        # 'トリュフ塩'という単価未定義の食材を追加
        DISHES["メインA_鴨"]["ingredients"]["トリュフ塩"] = 2

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"テストデータ読み込みエラー: {e}")
        exit()


    # 2. 検証を実行
    used_ingredients_set = get_all_ingredients_from_dishes(DISHES)
    price_names_set = set(ingredient_prices.keys())
    price_names_list = list(ingredient_prices.keys())

    results = validate_ingredient_data(used_ingredients_set, price_names_set)

    # 3. レポートを表示
    report = report_validation_results(results, price_names_list)

    print(report)

    print("\n--- データ検証テスト終了 ---")
