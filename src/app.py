import json
from flask import Flask, render_template
from src.cost_calculator import load_ingredient_prices, calculate_course_cost

app = Flask(__name__, template_folder='../templates')

# COURSE_RECIPES is no longer defined here.
# calculate_course_cost will use COURSES and DISHES from menu_definitions.py

@app.route('/costs')
def display_costs():
    course_name_to_display = "コースA"
    ingredient_prices_filepath = 'data/ingredient_prices.json'

    try:
        ingredient_prices = load_ingredient_prices(ingredient_prices_filepath)
    except FileNotFoundError:
        return f"Error: Ingredient prices file not found at '{ingredient_prices_filepath}'. Please check the file path.", 500
    except json.JSONDecodeError:
        return f"Error: Could not decode ingredient prices from '{ingredient_prices_filepath}'. Please check the file format.", 500
    except Exception as e:
        return f"An unexpected error occurred while loading ingredient prices: {str(e)}", 500

    if not ingredient_prices: # Handles empty dict if load_ingredient_prices returns that on error
        return f"Error: Ingredient prices are empty or could not be loaded from '{ingredient_prices_filepath}'.", 500

    # Call calculate_course_cost without COURSE_RECIPES argument
    course_cost_details = calculate_course_cost(course_name_to_display, ingredient_prices)

    if course_cost_details is None:
        # Adjusted error message as per requirements
        return f"Error: Course '{course_name_to_display}' not found in definitions.", 404

    # Prepare data for the template according to cost_display.html expectations
    # and the structure from calculate_course_cost
    template_data = {
        'course_name': course_cost_details.get('course_name'),
        'total_course_cost': course_cost_details.get('total_cost'),
        # The 'dishes_cost' list from calculate_course_cost maps directly to 'dishes' for the template
        # Each item in 'dishes_cost' should have 'dish_name', 'cost', and 'ingredients'
        'dishes': course_cost_details.get('dishes_cost', []) 
    }
        
    return render_template('cost_display.html', **template_data)

if __name__ == '__main__':
    app.run(debug=True) # Default port is 5000, can specify port if needed e.g. app.run(debug=True, port=5001)
