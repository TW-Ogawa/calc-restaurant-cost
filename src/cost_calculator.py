# -*- coding: utf-8 -*-

import json
from menu_definitions import COURSES, DISHES, DISCOUNT_RULES
from logger import get_logger

# ロガーを取得
logger = get_logger(__name__)

# --- データ読み込み ---
def load_ingredient_prices(filepath="data/ingredient_prices.json"):
    """
    食材の単価データをJSONファイルから読み込む関数。
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "食材マスタ" in data:
                del data["食材マスタ"]
            logger.info(f"食材単価ファイルを正常に読み込みました: {filepath}")
            return data
    except FileNotFoundError:
        logger.error(f"食材単価ファイルが見つかりません: {filepath}")
        raise
    except json.JSONDecodeError:
        logger.error(f"食材単価ファイルのJSON形式が正しくありません: {filepath}")
        raise

# --- 計算ロジック ---
def calculate_dish_cost(dish_id, ingredient_prices):
    """
    指定された料理IDの原価を計算する。
    """
    if dish_id not in DISHES:
        logger.warning(f"料理ID '{dish_id}' が定義に存在しません。")
        return 0, []

    dish_info = DISHES[dish_id]
    total_cost = 0
    ingredient_details = []

    for ingredient, quantity in dish_info["ingredients"].items():
        unit_price = ingredient_prices.get(ingredient)

        if unit_price is None:
            logger.warning(f"食材 '{ingredient}' の単価が見つかりません。原価計算からは除外されます。")
            cost = 0
        else:
            cost = quantity * unit_price
            total_cost += cost

        ingredient_details.append({
            "name": ingredient,
            "quantity": quantity,
            "unit_price": unit_price if unit_price is not None else "単価不明",
            "cost": cost
        })
        logger.debug(f"  - 食材: {ingredient}, 量: {quantity}, 単価: {unit_price}, コスト: {cost}")

    return total_cost, ingredient_details

def calculate_course_cost(course_id, ingredient_prices):
    """
    指定されたコースIDの合計原価と詳細を計算する。
    """
    if course_id not in COURSES:
        logger.error(f"コースID '{course_id}' が定義に存在しません。")
        return None

    course_info = COURSES[course_id]
    course_total_cost = 0
    dishes_cost_details = []

    logger.info(f"--- コース '{course_id}' の原価計算開始 ---")
    for dish_id in course_info["dishes"]:
        dish_cost, ingredient_details = calculate_dish_cost(dish_id, ingredient_prices)
        dish_name = DISHES.get(dish_id, {}).get("name", dish_id)
        dishes_cost_details.append({
            "dish_name": dish_name,
            "cost": dish_cost,
            "ingredients": ingredient_details
        })
        course_total_cost += dish_cost
        logger.info(f"  - 料理 '{dish_name}': {dish_cost:.2f} 円")

    logger.info(f"  割引前合計原価: {course_total_cost:.2f} 円")

    discount_rule_id = course_info.get("discount_rule", "none")
    rule = DISCOUNT_RULES.get(discount_rule_id, DISCOUNT_RULES["none"])

    discount_amount = 0
    applied = False
    if rule["type"] == "percentage":
        if course_total_cost >= 5000:
             discount_amount = course_total_cost * (rule["value"] / 100.0)
             applied = True
             logger.info(f"  適用割引: {rule['value']}% ({discount_amount:.2f} 円)")
        else:
             logger.info(f"  割引条件未達 ({rule['condition']})")
    elif rule["type"] == "fixed":
        discount_amount = rule["value"]
        applied = True
        logger.info(f"  適用割引: 固定 {discount_amount:.2f} 円")
    else:
        logger.info("  割引なし")

    final_course_cost = course_total_cost - discount_amount
    logger.info(f"  最終合計原価: {final_course_cost:.2f} 円")
    logger.info(f"--- コース '{course_id}' の原価計算終了 ---")


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
    from logger import setup_logger
    setup_logger()

    try:
        prices = load_ingredient_prices()

        # 全コースの原価を計算して表示
        for course_id in COURSES:
            course_result = calculate_course_cost(course_id, prices)
            if course_result:
                # 結果を整形して表示（ここでは簡易表示）
                print(f"\n===== {course_result['course_name']} =====")
                print(f"説明: {course_result['description']}")
                for dish in course_result['dishes_cost']:
                    print(f"  料理: {dish['dish_name']} - 原価: {dish['cost']:.2f}")
                    # 食材詳細も表示する場合は以下をアンコメント
                    # for ing in dish['ingredients']:
                    #    print(f"    - {ing['name']} ({ing['quantity']}) @{ing['unit_price']} = {ing['cost']:.2f}")
                print(f"小計: {course_result['subtotal_cost']:.2f}")
                if course_result['discount_info']['applied']:
                    print(f"割引 ({course_result['discount_info']['condition']}): -{course_result['discount_info']['discount_amount']:.2f}")
                print(f"合計原価: {course_result['total_cost']:.2f}")
                print("=" * (len(course_result['course_name']) + 10))

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"処理を中断しました: {e}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")