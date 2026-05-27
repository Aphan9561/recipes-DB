from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import pathlib

app = Flask(__name__)

DB_PATH = pathlib.Path.cwd() / "Recipes.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/recipes")
def recipes():
    page = int(request.args.get("page", 1))
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT recipeID, name, photoURL, duration, difficulty_level
        FROM Recipes
        ORDER BY recipeID
        LIMIT ? OFFSET ?;
    """, (per_page, offset))

    rows = cursor.fetchall()
    conn.close()

    return render_template("recipes.html", recipes=rows, page=page)


@app.get("/recipes/<int:recipe_id>")
def recipe_details(recipe_id):
    conn = get_db()
    cursor = conn.cursor()

    # RECIPE
    cursor.execute("""
        SELECT *
        FROM Recipes
        WHERE recipeID = ?;
    """, (recipe_id,))
    recipe = cursor.fetchone()

    if not recipe:
        conn.close()
        return "Recipe not found", 404

    # INGREDIENTS
    cursor.execute("""
        SELECT i.name, u.quantity, u.units
        FROM UsedIn u
        JOIN Ingredients i ON u.ingredientID = i.ingredientID
        WHERE u.recipeID = ?;
    """, (recipe_id,))
    ingredients = cursor.fetchall()

    # NUTRITION
    cursor.execute("""
        SELECT calories, protein, carbs
        FROM Nutrition
        WHERE recipeID = ?;
    """, (recipe_id,))
    nutrition = cursor.fetchone()

    # REVIEWS
    cursor.execute("""
        SELECT c.username, r.rating, r.description
        FROM Reviews r
        JOIN Chefs c ON r.chefID = c.chefID
        WHERE r.recipeID = ?;
    """, (recipe_id,))
    reviews = cursor.fetchall()

    # CATEGORIES
    cursor.execute("""
        SELECT c.name
        FROM Has h
        JOIN Categories c ON h.categoryID = c.categoryID
        WHERE h.recipeID = ?;
    """, (recipe_id,))
    categories = cursor.fetchall()

    # CUISINES
    cursor.execute("""
        SELECT c.cuisine_name
        FROM Belongs b
        JOIN Cuisines c ON b.cuisineID = c.cuisineID
        WHERE b.recipeID = ?;
    """, (recipe_id,))
    cuisines = cursor.fetchall()

    # DIETARY
    cursor.execute("""
        SELECT d.name
        FROM Safe s
        JOIN DietaryRestrictions d ON s.dietaryRestrictionID = d.dietaryRestrictionID
        WHERE s.recipeID = ?;
    """, (recipe_id,))
    dietary_restrictions = cursor.fetchall()

    # EQUIPMENT
    cursor.execute("""
        SELECT e.equipmentName
        FROM NecessaryFor n
        JOIN Equipment e ON n.equipmentID = e.equipmentID
        WHERE n.recipeID = ?;
    """, (recipe_id,))
    equipment = cursor.fetchall()

    conn.close()

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
        conn = get_db()
        cursor = conn.cursor()

        try:
            # -------------------------
            # BASIC FIELDS
            # -------------------------
            name = request.form["name"]
            yield_amount = request.form["yield"]
            difficulty_level = request.form["difficulty_level"]
            photoURL = request.form.get("photoURL") or ""
            instructions = request.form["instructions"]

            hours = int(request.form.get("duration_hours") or 0)
            minutes = int(request.form.get("duration_minutes") or 0)
            duration = hours * 60 + minutes

            # -------------------------
            # INSERT RECIPE
            # -------------------------
            cursor.execute("""
                INSERT INTO Recipes (
                    name, duration, yield, difficulty_level, photoURL, instructions
                )
                VALUES (?, ?, ?, ?, ?, ?);
            """, (name, duration, yield_amount, difficulty_level, photoURL, instructions))

            recipe_id = cursor.lastrowid

            # -------------------------
            # NUTRITION (safe defaults)
            # -------------------------
            calories = request.form.get("calories") or 0
            protein = request.form.get("protein") or 0
            carbs = request.form.get("carbs") or 0

            cursor.execute("""
                INSERT INTO Nutrition (
                    recipeID, calories, protein, carbs
                )
                VALUES (?, ?, ?, ?);
            """, (recipe_id, calories, protein, carbs))

            # -------------------------
            # INGREDIENTS (SAFE LOOP)
            # -------------------------
            ingredients = request.form.getlist("ingredients[]")
            quantities = request.form.getlist("quantities[]")
            units = request.form.getlist("units[]")

            for ingredient, qty, unit in zip(ingredients, quantities, units):
                if not ingredient.strip():
                    continue

                cursor.execute(
                    "SELECT ingredientID FROM Ingredients WHERE name = ?;",
                    (ingredient,)
                )
                row = cursor.fetchone()

                if row:
                    ingredient_id = row["ingredientID"]
                else:
                    cursor.execute(
                        "INSERT INTO Ingredients (name) VALUES (?);",
                        (ingredient,)
                    )
                    ingredient_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO UsedIn (ingredientID, recipeID, quantity, units)
                    VALUES (?, ?, ?, ?);
                """, (ingredient_id, recipe_id, qty, unit))

            # -------------------------
            # CATEGORIES
            # -------------------------
            for category_name in request.form.getlist("categories[]"):
                if not category_name.strip():
                    continue

                cursor.execute(
                    "SELECT categoryID FROM Categories WHERE name = ?;",
                    (category_name,)
                )
                row = cursor.fetchone()

                if row:
                    category_id = row["categoryID"]
                else:
                    cursor.execute(
                        "INSERT INTO Categories (name) VALUES (?);",
                        (category_name,)
                    )
                    category_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO Has (categoryID, recipeID) VALUES (?, ?);",
                    (category_id, recipe_id)
                )

            # -------------------------
            # DIETARY RESTRICTIONS
            # -------------------------
            for name in request.form.getlist("restrictions[]"):
                if not name.strip():
                    continue

                cursor.execute(
                    "SELECT dietaryRestrictionID FROM DietaryRestrictions WHERE name = ?;",
                    (name,)
                )
                row = cursor.fetchone()

                if row:
                    rid = row["dietaryRestrictionID"]
                else:
                    cursor.execute(
                        "INSERT INTO DietaryRestrictions (name) VALUES (?);",
                        (name,)
                    )
                    rid = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO Safe (dietaryRestrictionID, recipeID) VALUES (?, ?);",
                    (rid, recipe_id)
                )

            # -------------------------
            # CUISINES
            # -------------------------
            for cuisine_name in request.form.getlist("cuisines[]"):
                if not cuisine_name.strip():
                    continue

                cursor.execute(
                    "SELECT cuisineID FROM Cuisines WHERE cuisine_name = ?;",
                    (cuisine_name,)
                )
                row = cursor.fetchone()

                if row:
                    cid = row["cuisineID"]
                else:
                    cursor.execute(
                        "INSERT INTO Cuisines (cuisine_name) VALUES (?);",
                        (cuisine_name,)
                    )
                    cid = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO Belongs (cuisineID, recipeID) VALUES (?, ?);",
                    (cid, recipe_id)
                )

            # -------------------------
            # EQUIPMENT
            # -------------------------
            for equipment_name in request.form.getlist("equipment[]"):
                if not equipment_name.strip():
                    continue

                cursor.execute(
                    "SELECT equipmentID FROM Equipment WHERE equipmentName = ?;",
                    (equipment_name,)
                )
                row = cursor.fetchone()

                if row:
                    eid = row["equipmentID"]
                else:
                    cursor.execute(
                        "INSERT INTO Equipment (equipmentName) VALUES (?);",
                        (equipment_name,)
                    )
                    eid = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO NecessaryFor (equipmentID, recipeID) VALUES (?, ?);",
                    (eid, recipe_id)
                )

            # -------------------------
            # COMMIT
            # -------------------------
            conn.commit()
            return redirect(url_for("recipes"))

        except Exception as e:
            conn.rollback()
            print("ADD RECIPE ERROR:", e)
            return f"Error: {e}", 500

        finally:
            conn.close()

    return render_template("add_recipe.html")


@app.route("/search")
def search():
    return render_template("search.html")


@app.get("/api/options/<filter_type>")
def get_options(filter_type):
    conn = get_db()
    cursor = conn.cursor()

    mapping = {
        "cuisine": ("Cuisines", "cuisineID", "cuisine_name"),
        "category": ("Categories", "categoryID", "name"),
        "chefReviewed": ("Chefs", "chefID", "username"),
        "chefFavorite": ("Chefs", "chefID", "username"),
        "chefHighest": ("Chefs", "chefID", "username"),
        "chefFavNotRev": ("Chefs", "chefID", "username"),
        "ingredient": ("Ingredients", "ingredientID", "name"),
        "equipment": ("Equipment", "equipmentID", "equipmentName"),
        "diet": ("DietaryRestrictions", "dietaryRestrictionID", "name"),
    }

    if filter_type not in mapping:
        return jsonify([])

    table, id_col, name_col = mapping[filter_type]

    cursor.execute(f"""
        SELECT {id_col}, {name_col}
        FROM {table}
        ORDER BY {name_col};
    """)

    results = cursor.fetchall()
    return jsonify([dict(row) for row in results])

@app.get("/api/search/chefs")
def search_chefs():
    q = request.args.get("q", "")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT chefID, username
        FROM Chefs
        WHERE username LIKE ?
        ORDER BY username
        LIMIT 10;
    """, (f"%{q}%",))

    results = cursor.fetchall()
    return jsonify([dict(r) for r in results])

@app.post("/api/filter")
def filter_recipes():
    conn = get_db()
    cursor = conn.cursor()

    data = request.json
    filter_type = data["filter_type"]

    limit = int(data.get("limit", 20))
    offset = int(data.get("offset", 0))

    query = """
        SELECT DISTINCT r.recipeID, r.name, r.photoURL
        FROM Recipes r
    """
    params = []

    if filter_type == "cuisine":
        query += " JOIN Belongs b ON r.recipeID = b.recipeID WHERE b.cuisineID = ?"
        params.append(data["value_id"])

    elif filter_type == "category":
        query += " JOIN Has h ON r.recipeID = h.recipeID WHERE h.categoryID = ?"
        params.append(data["value_id"])

    elif filter_type == "chefReviewed":
        query += " JOIN Reviews rev ON r.recipeID = rev.recipeID WHERE rev.chefID = ?"
        params.append(data["value_id"])

    elif filter_type == "chefFavorite":
        query += " JOIN Favorites f ON r.recipeID = f.recipeID WHERE f.chefID = ?"
        params.append(data["value_id"])

    elif filter_type == "chefHighest":
        query = """
            SELECT r.recipeID, r.name, r.photoURL, rev.rating
            FROM Recipes r
            JOIN Reviews rev ON r.recipeID = rev.recipeID
            WHERE rev.chefID = ?
            ORDER BY rev.rating DESC
        """
        params.append(data["value_id"])

    elif filter_type == "ingredient":
        ids = data["value_ids"]

        placeholders = ",".join(["?"] * len(ids))

        query += f"""
            JOIN UsedIn u ON r.recipeID = u.recipeID
            WHERE u.ingredientID IN ({placeholders})
            GROUP BY r.recipeID
            HAVING COUNT(DISTINCT u.ingredientID) = ?
        """

        params.extend(ids)
        params.append(len(ids))

    elif filter_type == "equipment":
        query += " JOIN NecessaryFor n ON r.recipeID = n.recipeID WHERE n.equipmentID = ?"
        params.append(data["value_id"])

    elif filter_type == "diet":
        ids = data["value_ids"]

        placeholders = ",".join(["?"] * len(ids))

        query += f"""
            JOIN Safe s ON r.recipeID = s.recipeID
            WHERE s.dietaryRestrictionID IN ({placeholders})
            GROUP BY r.recipeID
            HAVING COUNT(DISTINCT s.dietaryRestrictionID) = ?
        """

        params.extend(ids)
        params.append(len(ids))

    elif filter_type == "level":
        query += " WHERE r.difficulty_level = ?"
        params.append(data["value_id"])

    elif filter_type == "duration":
        query += " WHERE r.duration <= ?"
        params.append(data["duration"])

    elif filter_type == "rating":
        query += " JOIN Reviews rev ON r.recipeID = rev.recipeID WHERE rev.rating = ?"
        params.append(data["value_id"])

    elif filter_type == "nutrition":
        query += """
            JOIN Nutrition n ON r.recipeID = n.recipeID
            WHERE n.calories <= ?
            AND n.protein >= ?
            AND n.carbs <= ?
        """
        params.extend([data["calories"], data["protein"], data["carbs"]])

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    results = cursor.fetchall()

    return jsonify([dict(row) for row in results])

if __name__ == "__main__":
    app.run(debug=True, port=8080)