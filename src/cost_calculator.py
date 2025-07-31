# -*- coding: utf-8 -*-

import json
from .menu_definitions import COURSES, DISHES, DISCOUNT_RULES

# --- データ読み込み ---
def load_ingredient_prices(filepath="data/ingredient_prices.json"):
    """
    食材の単価データをJSONファイルから読み込む関数。

    Args:
        filepath (str): 食材単価JSONファイルのパス。

    Returns:
        dict: 食材名をキー、単価を値とする辞書。
              ファイルが存在しない、または形式が不正な場合は空の辞書を返す。
    Raises:
        FileNotFoundError: 指定されたファイルパスが見つからない場合。
        json.JSONDecodeError: ファイルの内容が有効なJSONでない場合。
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # '食材マスタ'キーは説明用なので除外する
            if "食材マスタ" in data:
                del data["食材マスタ"]
            return data
    except FileNotFoundError:
        print(f"エラー: 食材単価ファイルが見つかりません: {filepath}")
        raise # エラーを再送出して上位で処理できるようにする
    except json.JSONDecodeError:
        print(f"エラー: 食材単価ファイルのJSON形式が正しくありません: {filepath}")
        raise # 同上

# --- 計算ロジック ---
def calculate_dish_cost(dish_id, ingredient_prices):
    """
    指定された料理IDの原価を計算する。

    Args:
        dish_id (str): menu_definitions.py で定義された料理のID。
        ingredient_prices (dict): 食材名と単価の辞書。

    Returns:
        tuple: (料理の原価合計, 使用食材の詳細リスト)
               料理が見つからない場合は (0, []) を返す。
               食材単価が見つからない場合は警告を表示し、その食材のコストは0として計算する。

    詳細リストの各要素は以下の辞書形式:
        {'name': 食材名, 'quantity': 使用量, 'unit_price': 単価, 'cost': 金額}
    """
    if dish_id not in DISHES:
        print(f"警告: 料理ID '{dish_id}' が定義に存在しません。")
        return 0, []

    dish_info = DISHES[dish_id]
    total_cost = 0
    ingredient_details = []

    # ***重要: ここからが料理原価の計算ロジック***
    # 料理定義(DISHES)から、その料理に必要な食材とその量を取得します。
    for ingredient, quantity in dish_info["ingredients"].items():
        # 取得した食材名を使って、食材単価データ(ingredient_prices)から単価を検索します。
        unit_price = ingredient_prices.get(ingredient) # .get()で存在しないキーでもエラーにならない

        if unit_price is None:
            # もし単価データに食材が見つからない場合は、警告を出し、原価は0円として扱います。
            # 本来はエラー処理やデフォルト単価の設定が必要です。
            print(f"警告: 食材 '{ingredient}' の単価が見つかりません。原価計算からは除外されます。")
            cost = 0
        else:
            # 単価が見つかった場合、原価を計算します: 原価 = 使用量 * 単価
            cost = quantity * unit_price
            # 料理全体の合計原価に加算します。
            total_cost += cost

        # 計算過程を記録するための詳細情報をリストに追加します。
        ingredient_details.append({
            "name": ingredient,
            "quantity": quantity,
            "unit_price": unit_price if unit_price is not None else "単価不明",
            "cost": cost
        })
        # ***ここまでが料理原価の計算ロジック***

    return total_cost, ingredient_details

def calculate_course_cost(course_id, ingredient_prices, verbose=False):
    """
    指定されたコースIDの合計原価と詳細を計算する。

    Args:
        course_id (str): menu_definitions.py で定義されたコースのID。
        ingredient_prices (dict): 食材名と単価の辞書。
        verbose (bool): 計算過程をコンソールに出力するかどうか。

    Returns:
        dict: コースの原価計算結果を含む辞書。
              コースが見つからない場合は None を返す。
    """
    if course_id not in COURSES:
        print(f"エラー: コースID '{course_id}' が定義に存在しません。")
        return None

    course_info = COURSES[course_id]
    course_total_cost = 0
    dishes_cost_details = []

    if verbose:
        print(f"\n--- コース '{course_id}' の原価計算開始 ---")

    for dish_id in course_info["dishes"]:
        dish_cost, ingredient_details = calculate_dish_cost(dish_id, ingredient_prices)
        dishes_cost_details.append({
            "dish_name": DISHES.get(dish_id, {}).get("name", dish_id),
            "cost": dish_cost,
            "ingredients": ingredient_details
        })
        course_total_cost += dish_cost
        if verbose:
            print(f"  - 料理 '{DISHES.get(dish_id, {}).get('name', dish_id)}': {dish_cost:.2f} 円")

    if verbose:
        print(f"  割引前合計原価: {course_total_cost:.2f} 円")

    discount_rule_id = course_info.get("discount_rule", "none")
    rule = DISCOUNT_RULES.get(discount_rule_id, DISCOUNT_RULES["none"])

    discount_amount = 0
    applied = False

    if rule["type"] == "percentage":
        if course_total_cost >= 5000:
            discount_amount = course_total_cost * (rule["value"] / 100.0)
            applied = True
            if verbose:
                print(f"  適用割引: {rule['value']}% ({discount_amount:.2f} 円)")
        elif verbose:
            print(f"  割引条件未達 ({rule['condition']})")
    elif rule["type"] == "fixed":
        discount_amount = rule["value"]
        applied = True
        if verbose:
            print(f"  適用割引: 固定 {discount_amount:.2f} 円")
    elif verbose:
        print("  割引なし")

    final_course_cost = course_total_cost - discount_amount
    if verbose:
        print(f"  最終合計原価: {final_course_cost:.2f} 円")
        print(f"--- コース '{course_id}' の原価計算終了 ---")


    return {
        "course_name": course_id,
        "description": course_info["description"],
        "dishes_cost": dishes_cost_details,
        "subtotal_cost": course_total_cost,
        "discount_info": {
            "rule_id": discount_rule_id,
            "condition": rule["condition"],
            "discount_amount": discount_amount,
            "applied": applied
        },
        "total_cost": final_course_cost
    }

# --- メイン実行ブロック ---
if __name__ == "__main__":
    # このスクリプトが直接実行された場合、
    # 新しいCLIインターフェース（cli.py）を実行するようにユーザーに案内します。
    # Pythonの-mオプションを使うと、パッケージ内のモジュールをスクリプトとして実行できます。
    # 例: python -m src.cli --all-courses
    print("原価計算ツールの実行は cli.py に移行しました。")
    print("コマンド例:")
    print("  python -m src.cli --all-courses")
    print("  python -m src.cli --course 'コースA' --verbose")
    print("  python -m src.cli --dish '前菜A'")
    print("  python -m src.cli --help")