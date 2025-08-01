# -*- coding: utf-8 -*-

import argparse
import json
from .cost_calculator import (
    calculate_course_cost,
    calculate_dish_cost,
    load_ingredient_prices
)
from .menu_definitions import COURSES, DISHES

def display_dish_cost(dish_id, prices, verbose=False):
    """料理の原価を表示する"""
    cost, details = calculate_dish_cost(dish_id, prices)
    dish_name = DISHES.get(dish_id, {}).get("name", dish_id)

    print(f"料理 '{dish_name}' の原価: {cost:.2f} 円")

    if verbose:
        print("--- 詳細 ---")
        for item in details:
            print(f"  - {item['name']}: {item['quantity']} * {item['unit_price']} = {item['cost']:.2f} 円")
        print("-" * 10)


def display_course_cost(course_id, prices, verbose=False, quiet=False):
    """コースの原価を表示する"""
    # quietでない場合のみ、計算過程をコンソールに出力する
    show_calculation_details = not quiet
    result = calculate_course_cost(course_id, prices, verbose=show_calculation_details)
    if not result:
        return

    if quiet:
        print(f"{result['course_name']}: {result['total_cost']:.2f} 円")
        return

    print(f"\n===== {result['course_name']} =====")
    print(f"説明: {result['description']}")

    if verbose:
        for dish in result['dishes_cost']:
            print(f"\n  料理: {dish['dish_name']} - 原価: {dish['cost']:.2f}")
            for ing in dish['ingredients']:
                 print(f"    - {ing['name']} ({ing['quantity']}) @{ing['unit_price']} = {ing['cost']:.2f}")
    else:
        for dish in result['dishes_cost']:
            print(f"  料理: {dish['dish_name']} - 原価: {dish['cost']:.2f}")


    print(f"\n小計: {result['subtotal_cost']:.2f}")
    if result['discount_info']['applied']:
        print(f"割引 ({result['discount_info']['condition']}): -{result['discount_info']['discount_amount']:.2f}")
    print(f"合計原価: {result['total_cost']:.2f}")
    print("=" * (len(result['course_name']) + 10))


def main():
    """コマンドライン引数を解析し、メインの処理を実行する"""
    parser = argparse.ArgumentParser(description="レストランメニューの原価計算ツール")

    # オプションをグループ化
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--course", help="特定のコースの原価を計算 (例: コースA)")
    group.add_argument("-d", "--dish", help="特定の料理の原価を計算 (例: 前菜A)")
    group.add_argument("--all-courses", action="store_true", help="すべてのコースの原価を計算")


    # 表示オプション
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("-v", "--verbose", action="store_true", help="食材ごとの詳細な原価情報を表示")
    output_group.add_argument("-q", "--quiet", action="store_true", help="最終合計原価のみを簡潔に表示 (コース計算時のみ有効)")


    args = parser.parse_args()

    try:
        prices = load_ingredient_prices()

        if args.course:
            if args.course not in COURSES:
                print(f"エラー: コース '{args.course}' が見つかりません。")
                print("利用可能なコース:", ", ".join(COURSES.keys()))
                return
            display_course_cost(args.course, prices, args.verbose, args.quiet)

        elif args.dish:
            if args.dish not in DISHES:
                print(f"エラー: 料理 '{args.dish}' が見つかりません。")
                print("利用可能な料理:", ", ".join(DISHES.keys()))
                return
            display_dish_cost(args.dish, prices, args.verbose)

        elif args.all_courses:
            for course_id in COURSES:
                display_course_cost(course_id, prices, args.verbose, args.quiet)


    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"エラー: {e}")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
