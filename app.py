from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from flask_cors import CORS
import datetime
import os

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
app.config ['MONGO_URI'] = os.getenv('MONGO_URI')

#### Conexión a Base de Datos Con MongoDB ###
mongo = PyMongo(app)
bcrypt = Bcrypt(app)

#### Rutas Ordinarias ####

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/inicio')
def index():
  return render_template('index.html')

@app.route('/contacto')
def contacto():
   return render_template('contacto.html')

##### Rutas de Registro #######

@app.route('/login', methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    user = mongo.db.users.find_one({"username": username})
    if user and bcrypt.check_password_hash(user["password"], password):  # Validar hash correctamente
        session["user"] = user["username"]
        return redirect(url_for("index"))
    
    return jsonify({"message": "Credenciales incorrectas"}), 401

@app.route('/signup', methods=['GET', 'POST'])
def signup():
   if request.method == "POST":
      ### Parametros a guardar en la Base de datos ####
      username = request.form["username"]
      email = request.form["email"]
      password = request.form["password"]
      #### Encriptado de la contraseña ###
      hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

      if mongo.db.users.find_one({"email": email}):
         return jsonify({"message": "Este correo ya existe"})
   
      user_data = {
         "username": username,
         "email" : email,
         "password": hashed_pw,
         "create_at": datetime.datetime.utcnow()
      }

      mongo.db.users.insert_one(user_data)
      return redirect(url_for('home'))

   return render_template('signup.html')

#### Rutas de Tareas ###


if __name__ == '__main__':
    app.run(debug=True)
