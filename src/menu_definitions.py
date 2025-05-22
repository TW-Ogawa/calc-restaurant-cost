# -*- coding: utf-8 -*-

"""
コースメニュー、料理、および使用食材の定義
"""

# コースメニューの定義
COURSES = {
    "コースA": {
        "description": "季節の味覚を楽しむスタンダードコース",
        "dishes": ["前菜A", "スープA", "メインA_鴨", "デザートA"],
        "discount_rule": "standard", # 適用する割引ルールID
        "available_drinks": ["WINE_RED", "WINE_WHITE", "CHAMPAGNE", "BEER", "ORANGE_JUICE"]
    },
    "コースB": {
        "description": "贅沢な食材をふんだんに使ったプレミアムコース",
        "dishes": ["前菜B", "スープB", "メインB_仔羊", "デザートB"],
        "discount_rule": "premium", # 適用する割引ルールID
        "available_drinks": ["WINE_RED", "WINE_WHITE", "CHAMPAGNE", "BEER", "ORANGE_JUICE"]
    }
}

# ドリンクの定義
DRINKS = {
    "WINE_RED": {
        "name": "ワイン (赤)",
        "price": 800
    },
    "WINE_WHITE": {
        "name": "ワイン (白)",
        "price": 800
    },
    "CHAMPAGNE": {
        "name": "シャンパン",
        "price": 1200
    },
    "BEER": {
        "name": "ビール",
        "price": 600
    },
    "ORANGE_JUICE": {
        "name": "オレンジジュース",
        "price": 400
    }
}

# 料理と使用食材リスト (食材名: 使用量(g または piece))
DISHES = {
    # --- コースA ---
    "前菜A": {
        "name": "ホタテのポワレ トリュフ風味",
        "ingredients": {
            "ホタテ": 80, # g
            "アスパラガス": 30, # g
            "トリュフオイル": 5, # g
            "バター": 10 # g
        }
    },
    "スープA": {
        "name": "じゃがいもの冷製スープ",
        "ingredients": {
            "ジャガイモ": 150, # g
            "生クリーム": 50, # g
            "ニンニク": 5 # g
        }
    },
    "メインA_鴨": {
        "name": "鴨肉のロースト ベリーソース",
        "ingredients": {
            "鴨肉": 150, # g
            "ベリー類": 50, # g
            "バター": 15, # g
            "砂糖": 10 # g
        }
    },
    "デザートA": {
        "name": "季節のフルーツタルト",
        "ingredients": {
            "ベリー類": 60, # g
            "小麦粉": 50, # g
            "バター": 30, # g
            "砂糖": 40, # g
            "生クリーム": 20 # g
        }
    },
    # --- コースB ---
     "前菜B": {
        "name": "キャビアとホタテのカルパッチョ",
        "ingredients": {
            "キャビア": 15, # g
            "ホタテ": 60, # g
            "トリュフオイル": 8 # g
        }
    },
    "スープB": {
        "name": "フォアグラのポタージュ",
        "ingredients": {
            "フォアグラ": 50, # g
            "ジャガイモ": 100, # g
            "生クリーム": 70 # g
        }
    },
    "メインB_仔羊": {
        "name": "仔羊の香草焼き ローズマリー風味",
        "ingredients": {
            "仔羊肉": 180, # g
            "ローズマリー": 5, # piece (仮定)
            "ニンニク": 10, # g
            "ジャガイモ": 80, # g
            "バター": 10 # g
        }
    },
    "デザートB": {
        "name": "濃厚チョコレートムース",
        "ingredients": {
            "チョコレート": 80, # g
            "生クリーム": 100, # g
            "砂糖": 30, # g
            "バター": 20 # g
        }
    }
}

# 割引ルールの定義
DISCOUNT_RULES = {
    "standard": {
        "type": "percentage",
        "value": 5, # 5% 割引
        "condition": "コース合計原価が5000円以上の場合"
    },
    "premium": {
        "type": "fixed",
        "value": 500, # 500円 固定割引
        "condition": "常に適用"
    },
    "none": { # 割引なし
        "type": "none",
        "value": 0,
        "condition": "割引なし"
    }
}