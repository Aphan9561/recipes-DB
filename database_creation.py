from contextlib import contextmanager
import csv
import sqlite3
import pathlib

DB_Path = None

creation_string = """
PRAGMA foreign_keys = ON;

-- RECIPES
CREATE TABLE Recipes (
    recipeID INT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    duration INT,
    yield VARCHAR(255),
    difficulty_level INT CHECK (difficulty_level BETWEEN 1 AND 5),
    photoURL VARCHAR(500),
    instructions TEXT
);

-- CATEGORIES
CREATE TABLE Categories (
    categoryID INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- DIETARY RESTRICTIONS
CREATE TABLE DietaryRestrictions (
    dietaryRestrictionID INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- CUISINES
CREATE TABLE Cuisines (
    cuisineID INT PRIMARY KEY,
    cuisine_name VARCHAR(100) NOT NULL
);

-- INGREDIENTS
CREATE TABLE Ingredients (
    ingredientID INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- EQUIPMENT
CREATE TABLE Equipment (
    equipmentID INT PRIMARY KEY,
    equipmentName VARCHAR(100) NOT NULL
);

-- NUTRITION
-- Weak entity dependent on Recipes
CREATE TABLE Nutrition (
    nutritionID INT PRIMARY KEY,
    recipeID INT NOT NULL,
    carbs DECIMAL(10, 1),
    calories DECIMAL(10, 1),
    protein DECIMAL(10, 1),

    FOREIGN KEY (recipeID) REFERENCES Recipes(recipeID)
        ON DELETE CASCADE
);

-- CHEFS
CREATE TABLE Chefs (
    chefID INT PRIMARY KEY,
    username VARCHAR(100) NOT NULL
);

-- REVIEWS
CREATE TABLE Reviews (
    reviewID INT PRIMARY KEY,
    rating INT CHECK (rating BETWEEN 0 AND 5),
    description VARCHAR(1000),
    recipeID INT NOT NULL,
    chefID INT NOT NULL,

    FOREIGN KEY (recipeID) REFERENCES Recipes(recipeID)
        ON DELETE CASCADE,
    FOREIGN KEY (chefID) REFERENCES Chefs(chefID)
        ON DELETE CASCADE
);

-- USED IN
-- Ingredients Used in Recipe
-- Relationship attributes: quantity, units
CREATE TABLE UsedIn (
    ingredientID INT,
    recipeID INT,
    quantity VARCHAR(10),
    units VARCHAR(50),
    PRIMARY KEY (ingredientID, recipeID),

    FOREIGN KEY (recipeID) REFERENCES Recipes(recipeID)
        ON DELETE CASCADE,
    FOREIGN KEY (ingredientID) REFERENCES Ingredients(ingredientID)
        ON DELETE CASCADE
);

-- NECESSARY FOR
-- Equipment Necessary for Recipes
CREATE TABLE NecessaryFor (
    equipmentID INT,
    recipeID INT,
    PRIMARY KEY (equipmentID, recipeID),

    FOREIGN KEY (recipeID) REFERENCES Recipes(recipeID)
        ON DELETE CASCADE,
    FOREIGN KEY (equipmentID) REFERENCES Equipment(equipmentID)
        ON DELETE CASCADE
);

-- HAS
-- Recipes Has Categories
CREATE TABLE Has (
    categoryID INT,
    recipeID INT,
    PRIMARY KEY (categoryID, recipeID),

    FOREIGN KEY (recipeID) REFERENCES Recipes(recipeID)
        ON DELETE CASCADE,
    FOREIGN KEY (categoryID) REFERENCES Categories(categoryID)
        ON DELETE CASCADE
);

-- BELONGS
-- Recipes Has Cuisines
CREATE TABLE Belongs (
    cuisineID INT,
    recipeID INT,
    PRIMARY KEY (cuisineID, recipeID),

    FOREIGN KEY (recipeID) REFERENCES Recipes(recipeID)
        ON DELETE CASCADE,
    FOREIGN KEY (cuisineID) REFERENCES Cuisines(cuisineID)
        ON DELETE CASCADE
);

-- SAFE
-- Recipes Safe for Dietary Restrictions
CREATE TABLE Safe (
    dietaryRestrictionID INT,
    recipeID INT,
    PRIMARY KEY (dietaryRestrictionID, recipeID),

    FOREIGN KEY (recipeID) REFERENCES Recipes(recipeID)
        ON DELETE CASCADE,
    FOREIGN KEY (dietaryRestrictionID) REFERENCES DietaryRestrictions(dietaryRestrictionID)
        ON DELETE CASCADE
);

-- FAVORITES
-- User/Chef Favorites Recipes
CREATE TABLE Favorites (
    chefID INT,
    recipeID INT,
    PRIMARY KEY (chefID, recipeID),

    FOREIGN KEY (chefID) REFERENCES Chefs(chefID)
        ON DELETE CASCADE,
    FOREIGN KEY (recipeID) REFERENCES Recipes(recipeID)
        ON DELETE CASCADE
);
"""

def set_db_path(database_path: pathlib.Path):
    global DB_Path
    DB_Path = database_path

def database_already_exists() -> bool:
    if not pathlib.Path.exists(DB_Path):
        return False
    try: # Also check if DB is set up correctly, as described at https://sqlite.org/faq.html question number 7
        current_database = sqlite3.connect(DB_Path)
        existingTable = current_database.execute(
        "SELECT tbl_name FROM sqlite_schema WHERE type='table' AND tbl_name='Recipes'").fetchall()
        return existingTable != []
    except:
        return False

@contextmanager
def get_connection():
    global DB_Path
    current_database = sqlite3.connect(DB_Path)
    current_database.row_factory = sqlite3.Row
    current_database.execute("PRAGMA foreign_keys = ON;")
    try:
        yield current_database
    finally:
        current_database.close()
    
def create_database():
    if database_already_exists():
        return
    original_database = sqlite3.connect(DB_Path)
    original_database.row_factory = sqlite3.Row # From https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.row_factory
    original_database.executescript(creation_string)
    original_database.commit()
    original_database.close() # The initial connection for setup; doesn't help to keep it alive
                              # any longer than this.

def close_database(db: sqlite3.Connection):
    if db != None:
        db.close()

def cast_int(string: str) -> int | None:
    try:
        return int(string)
    except ValueError:
        return None

def cast_float(string: str) -> int | None:
    try:
        return float(string)
    except ValueError:
        return None

def main():
    set_db_path(pathlib.Path.cwd()/"Recipes.db") # Builds the database in the curent
                                    # working directory, most likely the Recipes-DB folder
    csv_base_path = pathlib.Path.cwd() / "dataset"
    if not database_already_exists():
        create_database()
    with get_connection() as connection:
        # Add recipes:
        with open(csv_base_path/"recipes-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["recipeID"]), line["name"],
                                cast_int(line["duration"]), line["yield"],
                                cast_int(line["difficulty_level"]), line["photoURL"],
                                line["instructions"]))
            connection.executemany("INSERT INTO Recipes VALUES (?, ?, ?, ?, ?, ?, ?)", manys)
        print("Added recipe entities.")
        connection.commit()
        # Add categories:
        with open(csv_base_path/"categories-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["categoryID"]), line["name"]))
            connection.executemany("INSERT INTO Categories VALUES (?, ?)", manys)
        print("Added category entities.")
        connection.commit()
        # Add dietary restrictions:
        with open(csv_base_path/"dietary-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["dietaryRestrictionID"]),
                                    line["name"]))
            connection.executemany("INSERT INTO DietaryRestrictions VALUES (?, ?)", manys)
        print("Added dietary restriction entities.")
        connection.commit()
        # Add cuisines:
        with open(csv_base_path/"cuisine-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["cuisineID"]), line["cuisine_name"]))
            connection.executemany("INSERT INTO Cuisines VALUES (?, ?)", manys)
        print("Added cuisine entities.")
        connection.commit()
        # Add ingredients:
        with open(csv_base_path/"ingredients-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["ingredientID"]), line["name"]))
            connection.executemany("INSERT INTO Ingredients VALUES (?, ?)", manys)
        print("Added ingredient entities.")
        connection.commit()
        # Add equipment:
        with open(csv_base_path/"equipment-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["equipmentID"]), line["equipmentName"]))
            connection.executemany("INSERT INTO Equipment VALUES (?, ?)", manys)
        print("Added equipment entities.")
        connection.commit()
        # Add nutrition:
        with open(csv_base_path/"nutrition-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["nutritionID"]), cast_int(line["recipeID"]),
                                 cast_float(line["carbs"]), cast_float(line["calories"]),
                                 cast_float(line["protein"])))
            connection.executemany("INSERT INTO Nutrition VALUES (?, ?, ?, ?, ?)", manys)
        print("Added nutrition entities.")
        connection.commit()
        # Add chef:
        with open(csv_base_path/"chefs-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["chefID"]), line["username"]))
            connection.executemany("INSERT INTO Chefs VALUES (?, ?)", manys)
        print("Added chef entities.")
        connection.commit()
        # Add review:
        with open(csv_base_path/"reviews-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["reviewID"]), line["rating"],
                                 line["description"], cast_int(line["recipeID"]),
                                 cast_int(line["chefID"])))
            connection.executemany("INSERT INTO Reviews VALUES (?, ?, ?, ?, ?)", manys)
        print("Added review entities.")
        connection.commit()
        # Add used in:
        with open(csv_base_path/"usedin-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["ingredientID"]), cast_int(line["recipeID"]),
                                 line["quantity"], line["units"]))
            connection.executemany("INSERT INTO UsedIn VALUES (?, ?, ?, ?)", manys)
        print("Added used in relations.")
        connection.commit()
        # Add necessary for:
        with open(csv_base_path/"necessary-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["equipmentID"]),
                                     cast_int(line["recipeID"])))
            connection.executemany("INSERT INTO NecessaryFor VALUES (?, ?)", manys)
        print("Added necessary for relations.")
        connection.commit()
        # Add has:
        with open(csv_base_path/"has-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["categoryID"]), cast_int(line["recipeID"])))
            connection.executemany("INSERT INTO Has VALUES (?, ?)", manys)
        print("Added has relations.")
        connection.commit()
        # Add belongs:
        with open(csv_base_path/"belongs-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["cuisineID"]), cast_int(line["recipeID"])))
            connection.executemany("INSERT INTO Belongs VALUES (?, ?)", manys)
        print("Added belongs relations.")
        connection.commit()
        # Add safe:
        with open(csv_base_path/"safe-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["dietaryRestrictionID"]),
                            cast_int(line["recipeID"])))
            connection.executemany("INSERT INTO Safe VALUES (?, ?)", manys)
        print("Added safe relations.")
        connection.commit()
        # Add favorites:
        with open(csv_base_path/"favorites-hp-dataset.csv", mode ='r', encoding='utf-8') as file:    
            csvFile = csv.DictReader(file)
            manys = []
            for line in csvFile:
                manys.append((cast_int(line["chefID"]), cast_int(line["recipeID"])))
            connection.executemany("INSERT INTO Favorites VALUES (?, ?)", manys)
        print("Added favorite relations.")
        connection.commit()
    print("Database successfully populated!")


if __name__ == "__main__":
    main()