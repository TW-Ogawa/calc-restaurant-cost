import unittest
import json
import os
import sys
import tempfile
import io
from unittest.mock import patch # Removed patch_dict

# Add src directory to sys.path to allow direct import of cost_calculator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cost_calculator import load_ingredient_prices, calculate_dish_cost, calculate_course_cost
from menu_definitions import DISHES, COURSES, DISCOUNT_RULES

class TestLoadIngredientPrices(unittest.TestCase):

    def test_successful_loading(self):
        """Test loading a valid JSON file."""
        data = {"item_a": 10, "item_b": 20}
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding='utf-8') as tmp_file:
            json.dump(data, tmp_file)
            tmp_filepath = tmp_file.name
        
        try:
            loaded_data = load_ingredient_prices(tmp_filepath)
            self.assertEqual(loaded_data, data)
        finally:
            os.remove(tmp_filepath)

    def test_file_not_found(self):
        """Test loading a non-existent file."""
        non_existent_filepath = "non_existent_file.json"
        with self.assertRaises(FileNotFoundError):
            load_ingredient_prices(non_existent_filepath)

    def test_malformed_json(self):
        """Test loading a file with malformed JSON."""
        malformed_content = '{"item_a": 10, "item_b": 20,}' 
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding='utf-8') as tmp_file:
            tmp_file.write(malformed_content)
            tmp_filepath = tmp_file.name

        try:
            with self.assertRaises(json.JSONDecodeError):
                load_ingredient_prices(tmp_filepath)
        finally:
            os.remove(tmp_filepath)

    def test_exclusion_of_shokuzai_master_key(self):
        """Test that '食材マスタ' key is excluded."""
        data_with_master = {"食材マスタ": "description", "item_a": 10, "item_c": 30}
        expected_data = {"item_a": 10, "item_c": 30}
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json", encoding='utf-8') as tmp_file:
            json.dump(data_with_master, tmp_file, ensure_ascii=False)
            tmp_filepath = tmp_file.name

        try:
            loaded_data = load_ingredient_prices(tmp_filepath)
            self.assertEqual(loaded_data, expected_data)
            self.assertNotIn("食材マスタ", loaded_data)
            self.assertIn("item_a", loaded_data)
        finally:
            os.remove(tmp_filepath)

class TestCalculateDishCost(unittest.TestCase):

    def test_valid_dish_and_ingredients(self):
        """Test calculating cost for a valid dish with all ingredient prices available."""
        ingredient_prices = {"ホタテ": 25.0, "アスパラガス": 5.0, "トリュフオイル": 15.0, "バター": 2.0}
        dish_id = "前菜A" 

        expected_total_cost = 2245.0
        # ... (rest of the test method as before)
        expected_ingredient_details = [
            {'name': 'ホタテ', 'quantity': 80, 'unit_price': 25.0, 'cost': 2000.0},
            {'name': 'アスパラガス', 'quantity': 30, 'unit_price': 5.0, 'cost': 150.0},
            {'name': 'トリュフオイル', 'quantity': 5, 'unit_price': 15.0, 'cost': 75.0},
            {'name': 'バター', 'quantity': 10, 'unit_price': 2.0, 'cost': 20.0},
        ]

        total_cost, ingredient_details = calculate_dish_cost(dish_id, ingredient_prices)

        self.assertEqual(total_cost, expected_total_cost)
        self.assertListEqual(ingredient_details, expected_ingredient_details)


    @patch('sys.stdout', new_callable=io.StringIO)
    def test_invalid_dish_id(self, mock_stdout):
        """Test calculating cost for an invalid dish ID."""
        ingredient_prices = {"some_item": 1.0}
        dish_id = "存在しない料理ID"

        expected_total_cost = 0
        expected_ingredient_details = []

        total_cost, ingredient_details = calculate_dish_cost(dish_id, ingredient_prices)

        self.assertEqual(total_cost, expected_total_cost)
        self.assertListEqual(ingredient_details, expected_ingredient_details)
        self.assertIn(f"警告: 料理ID '{dish_id}' が定義に存在しません。", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_ingredient_price_missing(self, mock_stdout):
        """Test calculating cost when an ingredient's price is missing."""
        ingredient_prices = {"ホタテ": 25.0, "アスパラガス": 5.0, "バター": 2.0} # トリュフオイル missing
        dish_id = "前菜A"
        
        expected_total_cost = 2170.0 
        expected_ingredient_details = [
            {'name': 'ホタテ', 'quantity': 80, 'unit_price': 25.0, 'cost': 2000.0},
            {'name': 'アスパラガス', 'quantity': 30, 'unit_price': 5.0, 'cost': 150.0},
            {'name': 'トリュフオイル', 'quantity': 5, 'unit_price': "単価不明", 'cost': 0},
            {'name': 'バター', 'quantity': 10, 'unit_price': 2.0, 'cost': 20.0},
        ]
        
        self.assertIn(dish_id, DISHES, "Dish ID for test not found in menu_definitions.DISHES")
        total_cost, ingredient_details = calculate_dish_cost(dish_id, ingredient_prices)

        self.assertEqual(total_cost, expected_total_cost)
        self.assertListEqual(sorted(ingredient_details, key=lambda x: x['name']), 
                             sorted(expected_ingredient_details, key=lambda x: x['name']))
        self.assertIn("警告: 食材 'トリュフオイル' の単価が見つかりません。", mock_stdout.getvalue())
        truffle_oil_detail = next(item for item in ingredient_details if item['name'] == 'トリュフオイル')
        self.assertEqual(truffle_oil_detail['unit_price'], "単価不明")
        self.assertEqual(truffle_oil_detail['cost'], 0)


class TestCalculateCourseCost(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        # Prices for Course A to exceed 5000 for discount
        self.mock_prices_course_A_high_cost = {
            "ホタテ": 25.0, "アスパラガス": 5.0, "トリュフオイル": 15.0, "バター": 2.0,
            "ジャガイモ": 1.5, "生クリーム": 3.5, "ニンニク": 2.0,
            "鴨肉": 30.0, "ベリー類": 7.0, "砂糖": 0.8, "小麦粉": 0.5,
        }
        # Calculated costs for Course A with high prices:
        # 前菜A: 2245, スープA: 410, メインA_鴨: 4888, デザートA: 607. Subtotal: 8150

        # Prices for Course A to be below 5000
        self.mock_prices_course_A_low_cost = {
            "ホタテ": 10.0, "アスパラガス": 2.0, "トリュフオイル": 5.0, "バター": 1.0,
            "ジャガイモ": 0.5, "生クリーム": 1.0, "ニンニク": 0.5,
            "鴨肉": 15.0, "ベリー類": 3.0, "砂糖": 0.4, "小麦粉": 0.5,
        }
        # Calculated costs for Course A with low prices:
        # 前菜A: 895, スープA: 127.5, メインA_鴨: 2419, デザートA: 271. Subtotal: 3712.5

        # Prices for Course B
        self.mock_prices_course_B = {
            "キャビア": 50.0, "ホタテ": 25.0, "トリュフオイル": 15.0,
            "フォアグラ": 60.0, "ジャガイモ": 1.5, "生クリーム": 3.5, "ニンニク": 2.0,
            "仔羊肉": 45.0, "ローズマリー": 3.0, "バター": 2.0,
            "チョコレート": 8.0, "砂糖": 0.8, # Note: 生クリーム for デザートB is already in ジャガイモ prices
        }
        # Calculated costs for Course B:
        # 前菜B: 2370, スープB: 3395, メインB_仔羊: 8275
        # デザートB: (Choc 80*8) + (SC 100*3.5) + (Sugar 30*0.8) + (Butter 20*2) = 640+350+24+40=1054
        # Subtotal: 2370 + 3395 + 8275 + 1054 = 15094

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_course_A_standard_discount_applied(self, mock_stdout):
        course_id = "コースA"
        prices = self.mock_prices_course_A_high_cost
        expected_subtotal = 8150.0
        expected_discount_amount = round(expected_subtotal * 0.05, 3) # Standard 5%
        expected_total_cost = expected_subtotal - expected_discount_amount

        result = calculate_course_cost(course_id, prices)

        self.assertIsNotNone(result)
        self.assertEqual(result['course_name'], course_id)
        self.assertEqual(result['subtotal_cost'], expected_subtotal)
        self.assertTrue(result['discount_info']['applied'])
        self.assertEqual(result['discount_info']['rule_id'], "standard")
        self.assertAlmostEqual(result['discount_info']['discount_amount'], expected_discount_amount, places=3)
        self.assertAlmostEqual(result['total_cost'], expected_total_cost, places=3)
        self.assertEqual(len(result['dishes_cost']), len(COURSES[course_id]['dishes']))
        self.assertEqual(result['dishes_cost'][0]['cost'], 2245)
        self.assertEqual(result['dishes_cost'][1]['cost'], 410)
        self.assertEqual(result['dishes_cost'][2]['cost'], 4888)
        self.assertEqual(result['dishes_cost'][3]['cost'], 607)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_course_A_standard_discount_not_applied(self, mock_stdout):
        course_id = "コースA"
        prices = self.mock_prices_course_A_low_cost
        expected_subtotal = 3712.5
        
        result = calculate_course_cost(course_id, prices)

        self.assertIsNotNone(result)
        self.assertEqual(result['subtotal_cost'], expected_subtotal)
        self.assertFalse(result['discount_info']['applied'])
        self.assertEqual(result['discount_info']['rule_id'], "standard")
        self.assertEqual(result['discount_info']['discount_amount'], 0)
        self.assertEqual(result['total_cost'], expected_subtotal)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_course_B_premium_discount(self, mock_stdout):
        course_id = "コースB"
        prices = self.mock_prices_course_B
        expected_subtotal = 15094.0
        expected_discount_amount = 500.0 # Fixed premium
        expected_total_cost = expected_subtotal - expected_discount_amount
        
        result = calculate_course_cost(course_id, prices)

        self.assertIsNotNone(result)
        self.assertEqual(result['subtotal_cost'], expected_subtotal)
        self.assertTrue(result['discount_info']['applied'])
        self.assertEqual(result['discount_info']['rule_id'], "premium")
        self.assertEqual(result['discount_info']['discount_amount'], expected_discount_amount)
        self.assertEqual(result['total_cost'], expected_total_cost)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_course_no_discount_rule(self, mock_stdout):
        course_id_temp = "コースTEMP_NO_DISCOUNT"
        original_courses_value = COURSES.get(course_id_temp)
        
        COURSES[course_id_temp] = {
            "description": "割引ルールテスト用一時コース",
            "dishes": COURSES["コースA"]["dishes"],
            "discount_rule": "none" 
        }
        
        try:
            prices = self.mock_prices_course_A_high_cost 
            expected_subtotal = 8150.0 

            result = calculate_course_cost(course_id_temp, prices)

            self.assertIsNotNone(result)
            self.assertEqual(result['subtotal_cost'], expected_subtotal)
            self.assertFalse(result['discount_info']['applied'])
            self.assertEqual(result['discount_info']['rule_id'], "none")
            self.assertEqual(result['discount_info']['discount_amount'], 0)
            self.assertEqual(result['total_cost'], expected_subtotal)
        finally:
            # Clean up: remove the temporary course or restore original
            if original_courses_value is None:
                del COURSES[course_id_temp]
            else:
                COURSES[course_id_temp] = original_courses_value


    @patch('sys.stdout', new_callable=io.StringIO)
    def test_invalid_course_id(self, mock_stdout):
        course_id = "存在しないコースID"
        prices = self.mock_prices_course_A_low_cost

        result = calculate_course_cost(course_id, prices)
        self.assertIsNone(result)
        self.assertIn(f"エラー: コースID '{course_id}' が定義に存在しません。", mock_stdout.getvalue())
        

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_course_with_missing_ingredient_price(self, mock_stdout):
        course_id = "コースB"
        prices_missing_chocolate = self.mock_prices_course_B.copy()
        # Price of "チョコレート" is 8.0 in mock_prices_course_B
        # Cost of chocolate in デザートB: 80g * 8.0 = 640
        cost_of_chocolate_in_dessert_B = DISHES["デザートB"]["ingredients"]["チョコレート"] * prices_missing_chocolate["チョコレート"]
        del prices_missing_chocolate["チョコレート"] 

        original_subtotal_course_B = 15094.0
        expected_subtotal_without_chocolate = original_subtotal_course_B - cost_of_chocolate_in_dessert_B
        expected_discount_amount = 500.0 
        expected_total_cost = expected_subtotal_without_chocolate - expected_discount_amount
        
        # Cost of デザートB was 1054. Without chocolate (cost 640), it's 1054 - 640 = 414
        expected_dessert_b_cost_without_chocolate = 414.0

        result = calculate_course_cost(course_id, prices_missing_chocolate)
        self.assertIsNotNone(result)
        
        self.assertEqual(result['subtotal_cost'], expected_subtotal_without_chocolate)
        self.assertTrue(result['discount_info']['applied'])
        self.assertEqual(result['discount_info']['discount_amount'], expected_discount_amount)
        self.assertEqual(result['total_cost'], expected_total_cost)

        dessert_b_cost_info = next(d for d in result['dishes_cost'] if d['dish_name'] == DISHES["デザートB"]["name"])
        self.assertEqual(dessert_b_cost_info['cost'], expected_dessert_b_cost_without_chocolate)

        self.assertIn("警告: 食材 'チョコレート' の単価が見つかりません。", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
