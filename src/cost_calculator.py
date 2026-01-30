# -*- coding: utf-8 -*-

import json
from menu_definitions import COURSES, DISHES, DISCOUNT_RULES
from data_validator import (
    get_all_ingredients_from_dishes,
    validate_ingredient_data,
    report_validation_results
)

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

def calculate_course_cost(course_id, ingredient_prices):
    """
    指定されたコースIDの合計原価と詳細を計算する。

    Args:
        course_id (str): menu_definitions.py で定義されたコースのID。
        ingredient_prices (dict): 食材名と単価の辞書。

    Returns:
        dict: コースの原価計算結果を含む辞書。
              コースが見つからない場合は None を返す。

    辞書の構造:
    {
        'course_name': コース名,
        'description': コース説明,
        'dishes_cost': [
            {'dish_name': 料理名, 'cost': 料理原価, 'ingredients': [食材詳細...]}, ...
        ],
        'subtotal_cost': 割引前の合計原価,
        'discount_info': {
            'rule_id': 割引ルールID,
            'condition': 適用条件,
            'discount_amount': 割引額,
            'applied': 割引が適用されたか (bool)
        },
        'total_cost': 最終的なコース原価
    }
    """
    if course_id not in COURSES:
        print(f"エラー: コースID '{course_id}' が定義に存在しません。")
        return None

    course_info = COURSES[course_id]
    course_total_cost = 0
    dishes_cost_details = []

    # 1. コース内の各料理の原価を計算し、合計する
    #    コース定義(COURSES)から料理リスト(dishes)を取得し、各料理について calculate_dish_cost を呼び出す。
    print(f"\n--- コース '{course_id}' の原価計算開始 ---")
    for dish_id in course_info["dishes"]:
        dish_cost, ingredient_details = calculate_dish_cost(dish_id, ingredient_prices)
        dishes_cost_details.append({
            "dish_name": DISHES.get(dish_id, {}).get("name", dish_id), # 料理名を取得、なければID
            "cost": dish_cost,
            "ingredients": ingredient_details
        })
        course_total_cost += dish_cost
        print(f"  - 料理 '{DISHES.get(dish_id, {}).get('name', dish_id)}': {dish_cost:.2f} 円")

    print(f"  割引前合計原価: {course_total_cost:.2f} 円")

    # 2. 割引ルールを適用する
    #    コース定義(COURSES)から割引ルールID(discount_rule)を取得。
    discount_rule_id = course_info.get("discount_rule", "none") # 未定義なら割引なし
    rule = DISCOUNT_RULES.get(discount_rule_id, DISCOUNT_RULES["none"]) # ルールが存在しない場合も割引なし

    discount_amount = 0
    applied = False
    #   ルールタイプに応じて割引額を計算。
    #   'percentage': 割引率を適用 (例: 5%なら 合計原価 * 5 / 100)
    #   'fixed': 固定額を割引 (例: 500円引きなら 500)
    #   'none': 割引なし (0)
    #   割引条件(condition)も考慮する（ここでは簡易的にルール名で判断）。
    #   例: standardルールは合計原価5000円以上の場合のみ適用
    if rule["type"] == "percentage":
        if course_total_cost >= 5000: # standardルールの条件
             discount_amount = course_total_cost * (rule["value"] / 100.0)
             applied = True
             print(f"  適用割引: {rule['value']}% ({discount_amount:.2f} 円)")
        else:
             print(f"  割引条件未達 ({rule['condition']})")
    elif rule["type"] == "fixed":
        discount_amount = rule["value"]
        applied = True
        print(f"  適用割引: 固定 {discount_amount:.2f} 円")
    else: # none or unknown type
        print("  割引なし")

    # 3. 最終的なコース原価を計算
    #    最終原価 = 割引前合計原価 - 割引額
    final_course_cost = course_total_cost - discount_amount
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

# --- メイン実行ブロック (テスト用) ---
if __name__ == "__main__":
    try:
        # 1. データの読み込み
        prices = load_ingredient_prices()

        # 2. データ整合性チェック
        print("--- データ整合性チェック開始 ---")
        used_ingredients = get_all_ingredients_from_dishes(DISHES)
        price_ingredients = set(prices.keys())

        validation_results = validate_ingredient_data(used_ingredients, price_ingredients)

        # レポート生成と表示
        report = report_validation_results(validation_results, list(price_ingredients))
        print(report)

        # エラー（単価未定義の食材）がある場合は処理を中断
        if validation_results["missing_in_prices"]:
            print("\nエラーが検出されたため、原価計算を中断します。")
            exit() # スクリプトを終了

        print("--- データ整合性チェック終了 ---")

        # 3. 全コースの原価を計算して表示
        print("\n--- 全コースの原価計算開始 ---")
        for course_id in COURSES:
            course_result = calculate_course_cost(course_id, prices)
            if course_result:
                # 結果を整形して表示（ここでは簡易表示）
                print(f"\n===== {course_result['course_name']} =====")
                print(f"説明: {course_result['description']}")
                for dish in course_result['dishes_cost']:
                    print(f"  料理: {dish['dish_name']} - 原価: {dish['cost']:.2f}")
                print(f"小計: {course_result['subtotal_cost']:.2f}")
                if course_result['discount_info']['applied']:
                    print(f"割引 ({course_result['discount_info']['condition']}): -{course_result['discount_info']['discount_amount']:.2f}")
                print(f"合計原価: {course_result['total_cost']:.2f}")
                print("=" * (len(course_result['course_name']) + 10))
        print("\n--- 全コースの原価計算終了 ---")

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"処理を中断しました: {e}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")