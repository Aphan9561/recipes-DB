from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import mysql.connector
import os

app = Flask(__name__)

# DATABASE CONNECTION
load_dotenv()

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor(dictionary=True)

@app.route("/")
def home():
    return render_template("index.html")

@app.get("/recipes")
def recipes():
    query = """
        SELECT * FROM Recipes;
    """

    cursor.execute(query)

    all_recipes = cursor.fetchall()

    return render_template("recipes.html", recipes=all_recipes)

@app.get("/recipes/<int:recipe_id>")
def recipe_details(recipe_id):

    # RECIPE INFO
    recipe_query = """
        SELECT *
        FROM Recipes
        WHERE recipeID = %s;
    """

    cursor.execute(recipe_query, (recipe_id,))
    recipe = cursor.fetchone()

    if not recipe:
        return "Recipe not found", 404

    # INGREDIENTS
    ingredients_query = """
        SELECT i.name, u.quantity, u.units
        FROM UsedIn u
        JOIN Ingredients i
            ON u.ingredientID = i.ingredientID
        WHERE u.recipeID = %s;
    """

    cursor.execute(ingredients_query, (recipe_id,))
    ingredients = cursor.fetchall()

    # NUTRITION
    nutrition_query = """
        SELECT calories, protein, carbs
        FROM Nutrition
        WHERE recipeID = %s;
    """

    cursor.execute(nutrition_query, (recipe_id,))
    nutrition = cursor.fetchone()

    # REVIEWS
    reviews_query = """
        SELECT c.username, r.rating, r.description
        FROM Reviews r
        JOIN Chefs c
            ON r.chefID = c.chefID
        WHERE r.recipeID = %s;
    """

    cursor.execute(reviews_query, (recipe_id,))
    reviews = cursor.fetchall()

    # CATEGORIES
    categories_query = """
        SELECT c.name
        FROM Has h
        JOIN Categories c
            ON h.categoryID = c.categoryID
        WHERE h.recipeID = %s;
    """

    cursor.execute(categories_query, (recipe_id,))
    categories = cursor.fetchall()

    # CUISINES
    cuisines_query = """
        SELECT c.cuisine_name
        FROM Belongs b
        JOIN Cuisines c
            ON b.cuisineID = c.cuisineID
        WHERE b.recipeID = %s;
    """

    cursor.execute(cuisines_query, (recipe_id,))
    cuisines = cursor.fetchall()

    # DIETARY RESTRICTIONS
    dietary_query = """
        SELECT d.name
        FROM Safe s
        JOIN DietaryRestrictions d
            ON s.dietaryRestrictionID = d.dietaryRestrictionID
        WHERE s.recipeID = %s;
    """

    cursor.execute(dietary_query, (recipe_id,))
    dietary_restrictions = cursor.fetchall()

    # EQUIPMENT
    equipment_query = """
        SELECT e.equipmentName
        FROM NecessaryFor n
        JOIN Equipment e
            ON n.equipmentID = e.equipmentID
        WHERE n.recipeID = %s;
    """

    cursor.execute(equipment_query, (recipe_id,))
    equipment = cursor.fetchall()

    return render_template(
        "recipe_details.html",
        recipe=recipe,
        ingredients=ingredients,
        nutrition=nutrition,
        reviews=reviews,
        categories=categories,
        cuisines=cuisines,
        dietary_restrictions=dietary_restrictions,
        equipment=equipment
    )

@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        name = request.form["name"]
        serving_size = request.form["serving_size"]
        difficulty_level = request.form["difficulty_level"]
        photoURL = request.form["photoURL"]
        instructions = request.form["instructions"]

        hours = request.form.get("duration_hours", 0)
        minutes = request.form.get("duration_minutes", 0)
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        duration = f"{hours:02}:{minutes:02}:00"

        recipe_query = """
            INSERT INTO Recipes (
                name,
                duration,
                serving_size,
                difficulty_level,
                photoURL,
                instructions
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        recipe_values = (
            name,
            duration,
            serving_size,
            difficulty_level,
            photoURL,
            instructions
        )

        cursor.execute(recipe_query, recipe_values)
        recipe_id = cursor.lastrowid
        calories = request.form["calories"]
        protein = request.form["protein"]
        carbs = request.form["carbs"]

        nutrition_query = """
            INSERT INTO Nutrition (
                recipeID,
                calories,
                protein,
                carbs
            )
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            nutrition_query,
            (recipe_id, calories, protein, carbs)
        )

        ingredients = request.form.getlist("ingredients[]")
        quantities = request.form.getlist("quantities[]")
        units = request.form.getlist("units[]")

        for i in range(len(ingredients)):
            ingredient_name = ingredients[i]
            quantity = quantities[i]
            unit = units[i]

            cursor.execute(
                "SELECT ingredientID FROM Ingredients WHERE name=%s",
                (ingredient_name,)
            )

            ingredient = cursor.fetchone()

            if ingredient:
                ingredient_id = ingredient["ingredientID"]

            else:
                cursor.execute(
                    "INSERT INTO Ingredients (name) VALUES (%s)",
                    (ingredient_name,)
                )

                ingredient_id = cursor.lastrowid

            usedin_query = """
                INSERT INTO UsedIn (
                    ingredientID,
                    recipeID,
                    quantity,
                    units
                )
                VALUES (%s, %s, %s, %s)
            """

            cursor.execute(
                usedin_query,
                (ingredient_id, recipe_id, quantity, unit)
            )

        categories = request.form.getlist("categories[]")
        for category_name in categories:
            cursor.execute(
                "SELECT categoryID FROM Categories WHERE name=%s",
                (category_name,)
            )

            category = cursor.fetchone()

            if category:
                category_id = category["categoryID"]
            else:
                cursor.execute(
                    "INSERT INTO Categories (name) VALUES (%s)",
                    (category_name,)
                )
                category_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO Has (categoryID, recipeID)
                VALUES (%s, %s)
                """,
                (category_id, recipe_id)
            )

        restrictions = request.form.getlist("restrictions[]")

        for restriction_name in restrictions:
            cursor.execute(
                """
                SELECT dietaryRestrictionID
                FROM DietaryRestrictions
                WHERE name=%s
                """,
                (restriction_name,)
            )

            restriction = cursor.fetchone()

            if restriction:
                restriction_id = restriction["dietaryRestrictionID"]
            else:
                cursor.execute(
                    """
                    INSERT INTO DietaryRestrictions (name)
                    VALUES (%s)
                    """,
                    (restriction_name,)
                )

                restriction_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO Safe (
                    dietaryRestrictionID,
                    recipeID
                )
                VALUES (%s, %s)
                """,
                (restriction_id, recipe_id)
            )

        cuisines = request.form.getlist("cuisines[]")

        for cuisine_name in cuisines:
            cursor.execute(
                """
                SELECT cuisineID
                FROM Cuisines
                WHERE cuisine_name=%s
                """,
                (cuisine_name,)
            )

            cuisine = cursor.fetchone()

            if cuisine:
                cuisine_id = cuisine["cuisineID"]

            else:
                cursor.execute(
                    """
                    INSERT INTO Cuisines (cuisine_name)
                    VALUES (%s)
                    """,
                    (cuisine_name,)
                )

                cuisine_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO Belongs (
                    cuisineID,
                    recipeID
                )
                VALUES (%s, %s)
                """,
                (cuisine_id, recipe_id)
            )

        equipment_list = request.form.getlist("equipment[]")

        for equipment_name in equipment_list:
            cursor.execute(
                """
                SELECT equipmentID
                FROM Equipment
                WHERE equipmentName=%s
                """,
                (equipment_name,)
            )

            equipment = cursor.fetchone()

            if equipment:
                equipment_id = equipment["equipmentID"]

            else:
                cursor.execute(
                    """
                    INSERT INTO Equipment (equipmentName)
                    VALUES (%s)
                    """,
                    (equipment_name,)
                )

                equipment_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO NecessaryFor (
                    equipmentID,
                    recipeID
                )
                VALUES (%s, %s)
                """,
                (equipment_id, recipe_id)
            )

        db.commit()

        return redirect(url_for("recipes"))

    return render_template("add_recipe.html")

@app.route("/search")
def search():
    return render_template("search.html")

@app.get("/api/options/<filter_type>")
def get_options(filter_type):
    mapping = {
        "cuisine": ("Cuisines", "cuisineID", "cuisine_name"),
        "category": ("Categories", "categoryID", "name"),
        "chef": ("Chefs", "chefID", "username"),
        "ingredient": ("Ingredients", "ingredientID", "name"),
        "equipment": ("Equipment", "equipmentID", "equipmentName"),
        "diet": ("DietaryRestrictions", "dietaryRestrictionID", "name"),
    }

    table, id_col, name_col = mapping[filter_type]

    query = f"SELECT {id_col}, {name_col} FROM {table}"
    cursor.execute(query)

    return cursor.fetchall()

@app.post("/api/filter")
def filter_recipes():

    data = request.json
    filter_type = data["filter_type"]
    value_id = data["value_id"]

    query = """
        SELECT DISTINCT r.recipeID, r.name, r.photoURL
        FROM Recipes r
    """

    params = []

    if filter_type == "cuisine":
        query += """
        JOIN Belongs b ON r.recipeID = b.recipeID
        WHERE b.cuisineID = %s
        """

    elif filter_type == "category":
        query += """
        JOIN Has h ON r.recipeID = h.recipeID
        WHERE h.categoryID = %s
        """

    elif filter_type == "chef":
        query += """
        JOIN Reviews rev ON r.recipeID = rev.recipeID
        WHERE rev.chefID = %s
        """

    elif filter_type == "ingredient":
        query += """
        JOIN UsedIn u ON r.recipeID = u.recipeID
        WHERE u.ingredientID = %s
        """

    elif filter_type == "equipment":
        query += """
        JOIN NecessaryFor n ON r.recipeID = n.recipeID
        WHERE n.equipmentID = %s
        """

    elif filter_type == "diet":
        query += """
        JOIN Safe s ON r.recipeID = s.recipeID
        WHERE s.dietaryRestrictionID = %s
        """

    cursor.execute(query, (value_id,))
    results = cursor.fetchall()

    return results

if __name__ == "__main__":
    app.run(debug=True, port=8080)