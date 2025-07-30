# -*- coding: utf-8 -*-

import argparse
from cost_calculator import (
    load_ingredient_prices,
    calculate_course_cost,
    calculate_dish_cost
)
from menu_definitions import COURSES, DISHES

def display_dish_cost(dish_id, prices, verbose=False):
    """料理の原価情報を表示する"""
    dish_cost, ingredient_details = calculate_dish_cost(dish_id, prices)
    if dish_cost > 0:
        dish_name = DISHES.get(dish_id, {}).get("name", dish_id)
        print(f"\n--- 料理 '{dish_name}' の原価 ---")
        print(f"合計原価: {dish_cost:.2f} 円")
        if verbose:
            print("  --- 使用食材 ---")
            for ing in ingredient_details:
                price_str = f"{ing['unit_price']:.2f}" if isinstance(ing['unit_price'], (int, float)) else ing['unit_price']
                print(f"    - {ing['name']} ({ing['quantity']}) @{price_str} = {ing['cost']:.2f} 円")
        print("-" * (len(dish_name) + 12))

def display_course_cost(course_id, prices, verbose=False, quiet=False):
    """コースの原価情報を表示する"""
    course_result = calculate_course_cost(course_id, prices)
    if course_result:
        print(f"\n===== {course_result['course_name']} =====")
        print(f"説明: {course_result['description']}")
        if not quiet and not verbose: # normal
            for dish in course_result['dishes_cost']:
                print(f"  料理: {dish['dish_name']} - 原価: {dish['cost']:.2f}")
        elif verbose: # verbose
            for dish in course_result['dishes_cost']:
                print(f"\n  --- 料理: {dish['dish_name']} (原価: {dish['cost']:.2f}) ---")
                for ing in dish['ingredients']:
                     price_str = f"{ing['unit_price']:.2f}" if isinstance(ing['unit_price'], (int, float)) else ing['unit_price']
                     print(f"    - {ing['name']} ({ing['quantity']}) @{price_str} = {ing['cost']:.2f} 円")
        # quiet の場合は料理一覧を何も表示しない

        print("-" * 20)
        print(f"小計: {course_result['subtotal_cost']:.2f}")
        if course_result['discount_info']['applied']:
            print(f"割引 ({course_result['discount_info']['condition']}): -{course_result['discount_info']['discount_amount']:.2f}")
        print(f"合計原価: {course_result['total_cost']:.2f}")
        print("=" * (len(course_result['course_name']) + 10))


def main():
    """
    コマンドラインインターフェースを処理するメイン関数
    """
    parser = argparse.ArgumentParser(description="レストランのメニュー原価計算ツール")

    # オプションをグループ化
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--course", help="特定のコースの原価を計算 (例: コースA)")
    group.add_argument("-d", "--dish", help="特定の料理の原価を計算 (例: 前菜A)")

    # 表示詳細レベル
    display_group = parser.add_mutually_exclusive_group()
    display_group.add_argument("-v", "--verbose", action="store_true", help="食材詳細など、より詳細な情報を表示")
    display_group.add_argument("-q", "--quiet", action="store_true", help="コース内の料理一覧を省略し、合計のみ表示 (デフォルトは通常表示)")


    args = parser.parse_args()

    try:
        prices = load_ingredient_prices()

        if args.course:
            if args.course in COURSES:
                display_course_cost(args.course, prices, args.verbose, args.quiet)
            else:
                print(f"エラー: コース '{args.course}' が見つかりません。")
                print(f"利用可能なコース: {', '.join(COURSES.keys())}")

        elif args.dish:
            if args.dish in DISHES:
                display_dish_cost(args.dish, prices, args.verbose)
            else:
                print(f"エラー: 料理 '{args.dish}' が見つかりません。")
                print(f"利用可能な料理: {', '.join(DISHES.keys())}")

        else:
            # デフォルトの動作: 全コースを計算・表示
            print("=== 全コースの原価概要 ===")
            for course_id in COURSES:
                display_course_cost(course_id, prices, args.verbose)

    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
