from flask import Flask, render_template
from src.cost_calculator import load_ingredient_prices, calculate_course_cost
from src.menu_definitions import COURSES # Assuming COURSES is a dictionary of course definitions

# Initialize Flask App
# Flask will look for a 'templates' folder in the same directory as this app.py file (project root)
app = Flask(__name__)

# Define a route to display the cost for a specific course
@app.route('/course/<course_name>')
def display_course_cost(course_name):
    """
    Displays the detailed cost calculation for a given course.
    """
    try:
        # 1. Load ingredient prices
        # Assuming ingredient_prices.json is in a 'data' directory relative to the project root
        prices = load_ingredient_prices('data/ingredient_prices.json')

        # 2. Check if the requested course_name exists in our definitions
        if course_name not in COURSES:
            return f"Course '{course_name}' not found.", 404

        # 3. Calculate the cost for the specified course
        # The calculate_course_cost function is expected to return a dictionary
        # with keys like 'course_name', 'total_cost', and 'dishes_cost'
        course_result = calculate_course_cost(course_name, prices)

        # 4. Render the HTML template, passing the course data
        # The template cost_display.html expects variables like:
        # course_name, total_cost, dishes_cost (which is a list of dicts)
        return render_template(
            "cost_display.html",
            course_name=course_result['course_name'],
            total_cost=course_result['total_cost'],
            dishes_cost=course_result['dishes_cost']
        )

    except FileNotFoundError:
        # Handle missing ingredient prices file
        app.logger.error("ingredient_prices.json not found.")
        return "Error: Ingredient prices file not found. Please check server configuration.", 500
    except Exception as e:
        # Handle other potential errors, e.g., issues within calculate_course_cost
        app.logger.error(f"An error occurred while calculating course cost: {e}")
        return f"An error occurred: {e}", 500

# Define a simple root route for discoverability, linking to Course A
@app.route('/')
def index():
    """
    Provides a link to a default course cost page (e.g., コースA).
    """
    # We can pick a default course, for example, the first one in COURSES or "コースA"
    default_course_name = "コースA" # Or: next(iter(COURSES)) if COURSES else "コースA"
    
    # Check if "コースA" actually exists to prevent errors if it's removed from definitions
    if default_course_name not in COURSES:
        # Fallback if "コースA" is not defined, pick the first available course or show error
        if COURSES:
            default_course_name = next(iter(COURSES))
            app.logger.warning(f"'コースA' not found, defaulting to {default_course_name}.")
        else:
            app.logger.error("No courses defined in menu_definitions.py")
            return "Error: No courses available to display.", 500
            
    return f'<h1>原価計算アプリ</h1><p><a href="/course/{default_course_name}">「{default_course_name}」の原価を表示</a></p>'

# Main Execution Block
if __name__ == "__main__":
    # Note: For development, debug=True is fine.
    # For production, use a production WSGI server like Gunicorn or uWSGI.
    app.run(debug=True, port=5001) # Using port 5001 to avoid common conflicts
