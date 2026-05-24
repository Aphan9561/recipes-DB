-- CREATE DATABASE
CREATE DATABASE RecipeDB;
USE RecipeDB;

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
    rating INT CHECK (rating BETWEEN 1 AND 5),
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
    quantity INT,
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

-- QUERIES
-- 1. List of recipes that take under specified amount of time to prepare
-- under 30 mins
SELECT name, duration
FROM Recipes
WHERE duration < 30;

-- 2. List recipes belonging to particular cuisine
-- cuisine = italian
SELECT r.recipeID, r.name, c.cuisine_name
FROM Recipes r
JOIN Belongs b
    ON r.recipeID = b.recipeID
JOIN Cuisines c
    ON b.cuisineID = c.cuisineID
WHERE c.cuisine_name = 'Italian';

-- 3. List recipes belonging to particular category
-- category = dessert
SELECT r.recipeID, r.name, c.name AS category
FROM Recipes r
JOIN Has h
    ON r.recipeID = h.recipeID
JOIN Categories c
    ON h.categoryID = c.categoryID
WHERE c.name = 'Dessert';

-- 4. List recipes that do not require specific equipment user does not have access to
--  equipment = blender
SELECT DISTINCT r.recipeID, r.name
FROM Recipes r
WHERE r.recipeID NOT IN (
    SELECT nf.recipeID
    FROM NecessaryFor nf
    JOIN Equipment e
        ON nf.equipmentID = e.equipmentID
    WHERE e.equipmentName = 'Blender'
);


-- 5. List recipes that can be made with a provided list of ingredients
-- ingredients = chicken, rice, garlic
SELECT DISTINCT r.recipeID, r.name
FROM Recipes r
JOIN UsedIn u
    ON r.recipeID = u.recipeID
JOIN Ingredients i
    ON u.ingredientID = i.ingredientID
WHERE i.name IN ('Chicken', 'Rice', 'Garlic');

-- 6. List recipes written by a specific chef
-- chef = anna
SELECT DISTINCT r.recipeID, r.name, c.username
FROM Recipes r
JOIN Reviews rev
    ON r.recipeID = rev.recipeID
JOIN Chefs c
    ON rev.chefID = c.chefID
WHERE c.username = 'Anna';

-- 7. List reviews written by specific user/chef and their corresponding recipe
-- chef = anna
SELECT c.username,
       r.name AS recipe_name,
       rev.rating,
       rev.description
FROM Reviews rev
JOIN Recipes r
    ON rev.recipeID = r.recipeID
JOIN Chefs c
    ON rev.chefID = c.chefID
WHERE c.username = 'Anna';

-- 8. List recipes that meet specific dietary requirements
-- dietary requirements = vegan
SELECT r.recipeID, r.name, d.name AS dietary_restriction
FROM Recipes r
JOIN Safe s
    ON r.recipeID = s.recipeID
JOIN DietaryRestrictions d
    ON s.dietaryRestrictionID = d.dietaryRestrictionID
WHERE d.name = 'Vegan';

-- 9. Recipes that are within specific calorie, protein, carb range
-- calories <= 500, protein >= 20, and carbs <= 50
SELECT r.recipeID,
       r.name,
       n.calories,
       n.protein,
       n.carbs
FROM Recipes r
JOIN Nutrition n
    ON r.recipeID = n.recipeID
WHERE n.calories <= 500
AND n.protein >= 20
AND n.carbs <= 50;

-- 10. Recipes having received a specific rating 
-- rating = 5
SELECT DISTINCT r.recipeID,
       r.name,
       rev.rating
FROM Recipes r
JOIN Reviews rev
    ON r.recipeID = rev.recipeID
WHERE rev.rating = 5;

-- 11. List recipes with a specific difficulty rating 
-- level = 3
SELECT recipeID,
       name,
       difficulty_level
FROM Recipes
WHERE difficulty_level = 3;

-- 12. List recipes favorited by chef that you like/whose recipes you have rated highly
-- 
SELECT DISTINCT r.name,
       c.username
FROM Favorites f
JOIN Recipes r
    ON f.recipeID = r.recipeID
JOIN Chefs c
    ON f.chefID = c.chefID
JOIN Reviews rev
    ON r.recipeID = rev.recipeID
WHERE rev.rating >= 4;


-- 13. List the highest rated recipe by a specific chef 
SELECT r.name,
       MAX(rev.rating) AS highest_rating
FROM Recipes r
JOIN Reviews rev
    ON r.recipeID = rev.recipeID
JOIN Chefs c
    ON rev.chefID = c.chefID
WHERE c.username = 'Anna'
GROUP BY r.name
ORDER BY highest_rating DESC
LIMIT 1;

-- 14. List recipes that you (chef) have favorited but not reviewed (
SELECT r.recipeID,
       r.name
FROM Favorites f
JOIN Recipes r
    ON f.recipeID = r.recipeID
WHERE f.chefID = 1
AND r.recipeID NOT IN (
    SELECT recipeID
    FROM Reviews
    WHERE chefID = 1
);

-- 15. Make a shopping list based on particular recipes you want to try 
-- recipes = chicken soup, pasta alfredo
SELECT DISTINCT i.name AS ingredient,
       u.quantity,
       u.units
FROM UsedIn u
JOIN Ingredients i
    ON u.ingredientID = i.ingredientID
JOIN Recipes r
    ON u.recipeID = r.recipeID
WHERE r.name IN ('Pasta Alfredo', 'Chicken Soup');

-- 16. Count the number of recipes in each cuisine 
SELECT c.cuisine_name,
       COUNT(b.recipeID) AS recipe_count
FROM Cuisines c
JOIN Belongs b
    ON c.cuisineID = b.cuisineID
GROUP BY c.cuisine_name
ORDER BY recipe_count DESC;

