# -*- coding: utf-8 -*-

import json
from menu_definitions import COURSES, DISHES, DISCOUNT_RULES, DRINKS

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

def calculate_course_cost(course_id, ingredient_prices, selected_drinks=None):
    """
    指定されたコースIDの合計原価と詳細を計算する。

    Args:
        course_id (str): menu_definitions.py で定義されたコースのID。
        ingredient_prices (dict): 食材名と単価の辞書。
        selected_drinks (list, optional): 選択されたドリンクIDのリスト。デフォルトは None。

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
        'total_food_cost': 最終的な料理原価 (割引後),
        'selected_drinks_info': [ {'name': ドリンク名, 'price': ドリンク価格}, ... ],
        'drinks_total_cost': ドリンク合計価格,
        'total_cost': 最終的なコース原価 (料理 + ドリンク)
    }
    """
    if selected_drinks is None:
        selected_drinks = []

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
    final_course_food_cost = course_total_cost - discount_amount
    print(f"  最終料理原価 (割引適用後): {final_course_food_cost:.2f} 円")

    # 4. 選択されたドリンクのコストを計算
    drinks_total_cost = 0
    selected_drinks_details = []
    if selected_drinks:
        print("  --- 選択ドリンク ---")
        for drink_id in selected_drinks:
            drink_info = DRINKS.get(drink_id)
            if drink_info:
                drink_name = drink_info["name"]
                drink_price = drink_info["price"]
                drinks_total_cost += drink_price
                selected_drinks_details.append({"name": drink_name, "price": drink_price})
                print(f"    - {drink_name}: {drink_price:.2f} 円")
            else:
                print(f"警告: ドリンクID '{drink_id}' は定義に存在しません。")
        print(f"  ドリンク合計価格: {drinks_total_cost:.2f} 円")

    # 5. 最終的な総原価を計算 (料理 + ドリンク)
    final_course_cost_with_drinks = final_course_food_cost + drinks_total_cost
    print(f"  最終合計原価 (ドリンク込み): {final_course_cost_with_drinks:.2f} 円")
    print(f"--- コース '{course_id}' の原価計算終了 ---")


    return {
        "course_name": course_id,
        "description": course_info["description"],
        "dishes_cost": dishes_cost_details,
        "subtotal_cost": course_total_cost, # 料理の割引前合計
        "discount_info": {
            "rule_id": discount_rule_id,
            "condition": rule["condition"],
            "discount_amount": discount_amount,
            "applied": applied
        },
        "total_food_cost": final_course_food_cost, # 料理の割引後合計
        "selected_drinks_info": selected_drinks_details,
        "drinks_total_cost": drinks_total_cost,
        "total_cost": final_course_cost_with_drinks # 最終的な総原価
    }

# --- メイン実行ブロック (テスト用) ---
if __name__ == "__main__":
    try:
        prices = load_ingredient_prices()

        # --- コースAのテスト ---
        print("\n--- コースA (ドリンクなし) ---")
        course_a_result_no_drinks = calculate_course_cost("コースA", prices)
        if course_a_result_no_drinks:
            # 結果を整形して表示
            print(f"\n===== {course_a_result_no_drinks['course_name']} (ドリンクなし) =====")
            print(f"説明: {course_a_result_no_drinks['description']}")
            for dish in course_a_result_no_drinks['dishes_cost']:
                print(f"  料理: {dish['dish_name']} - 原価: {dish['cost']:.2f}")
            print(f"料理小計: {course_a_result_no_drinks['subtotal_cost']:.2f}")
            if course_a_result_no_drinks['discount_info']['applied']:
                print(f"割引 ({course_a_result_no_drinks['discount_info']['condition']}): -{course_a_result_no_drinks['discount_info']['discount_amount']:.2f}")
            print(f"料理合計原価: {course_a_result_no_drinks['total_food_cost']:.2f}")
            print(f"ドリンク合計: {course_a_result_no_drinks['drinks_total_cost']:.2f}")
            print(f"最終合計原価: {course_a_result_no_drinks['total_cost']:.2f}")
            print("=" * (len(course_a_result_no_drinks['course_name']) + 20))

        print("\n--- コースA (ドリンクあり) ---")
        course_a_drinks = ["WINE_RED", "ORANGE_JUICE", "INVALID_DRINK"]
        course_a_result_with_drinks = calculate_course_cost("コースA", prices, selected_drinks=course_a_drinks)
        if course_a_result_with_drinks:
            # 結果を整形して表示
            print(f"\n===== {course_a_result_with_drinks['course_name']} (ドリンク: {', '.join(course_a_drinks)}) =====")
            print(f"説明: {course_a_result_with_drinks['description']}")
            for dish in course_a_result_with_drinks['dishes_cost']:
                print(f"  料理: {dish['dish_name']} - 原価: {dish['cost']:.2f}")
            print(f"料理小計: {course_a_result_with_drinks['subtotal_cost']:.2f}")
            if course_a_result_with_drinks['discount_info']['applied']:
                print(f"割引 ({course_a_result_with_drinks['discount_info']['condition']}): -{course_a_result_with_drinks['discount_info']['discount_amount']:.2f}")
            print(f"料理合計原価: {course_a_result_with_drinks['total_food_cost']:.2f}")
            print("  --- 選択されたドリンク ---")
            for drink_item in course_a_result_with_drinks['selected_drinks_info']:
                print(f"    - {drink_item['name']}: {drink_item['price']:.2f} 円")
            print(f"ドリンク合計: {course_a_result_with_drinks['drinks_total_cost']:.2f}")
            print(f"最終合計原価: {course_a_result_with_drinks['total_cost']:.2f}")
            print("=" * (len(course_a_result_with_drinks['course_name']) + 20))


        # --- コースBのテスト (割引あり、ドリンクあり) ---
        print("\n--- コースB (ドリンクあり、割引期待) ---")
        # コースBは元々の食材原価が高いので、割引が適用されるはず
        course_b_drinks = ["CHAMPAGNE", "BEER"]
        course_b_result_with_drinks = calculate_course_cost("コースB", prices, selected_drinks=course_b_drinks)
        if course_b_result_with_drinks:
             # 結果を整形して表示
            print(f"\n===== {course_b_result_with_drinks['course_name']} (ドリンク: {', '.join(course_b_drinks)}) =====")
            print(f"説明: {course_b_result_with_drinks['description']}")
            for dish in course_b_result_with_drinks['dishes_cost']:
                print(f"  料理: {dish['dish_name']} - 原価: {dish['cost']:.2f}")
            print(f"料理小計: {course_b_result_with_drinks['subtotal_cost']:.2f}")
            if course_b_result_with_drinks['discount_info']['applied']:
                print(f"割引 ({course_b_result_with_drinks['discount_info']['condition']}): -{course_b_result_with_drinks['discount_info']['discount_amount']:.2f}")
            else:
                print("割引: なし")
            print(f"料理合計原価: {course_b_result_with_drinks['total_food_cost']:.2f}")
            print("  --- 選択されたドリンク ---")
            for drink_item in course_b_result_with_drinks['selected_drinks_info']:
                print(f"    - {drink_item['name']}: {drink_item['price']:.2f} 円")
            print(f"ドリンク合計: {course_b_result_with_drinks['drinks_total_cost']:.2f}")
            print(f"最終合計原価: {course_b_result_with_drinks['total_cost']:.2f}")
            print("=" * (len(course_b_result_with_drinks['course_name']) + 20))


    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"処理を中断しました: {e}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")