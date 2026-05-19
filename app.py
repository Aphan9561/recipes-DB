from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)

# DATABASE CONNECTION
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="hello123",
    database="RecipeDB"
)

cursor = db.cursor(dictionary=True)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=8080)