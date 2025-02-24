from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
from flask_cors import CORS
import datetime
import os
from bson.objectid import ObjectId

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

##### Rutas de Registro y Cambio de Contraseñas #######

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
         "profile_picture": "",
         "create_at": datetime.datetime.utcnow(),
         "updated_at": datetime.datetime.utcnow() 
      }

      mongo.db.users.insert_one(user_data)
      return redirect(url_for('home'))

   return render_template('signup.html')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
   session.clear()
   return redirect(url_for('home'))

@app.route('/password/change-password', methods=['GET', 'POST'])
def change_password():

   if 'user' not in session:
      return redirect( url_for ('home'))

   if request.method == 'POST':
      current_password = request.form.get('current_password')
      new_password = request.form.get('new_password')
      confirm_password = request.form.get('confirm_password')

      user = mongo.db.users.find_one({"username": session['user']})

      if not check_password_hash(user['password'], current_password):
         flash('La contraseña actual es Incorrecta', "error")
         return redirect(url_for('change_passowrd'))
      
      if new_password != confirm_password:
         flash('Las Contraseñas No Coinciden', "error")
         return redirect( url_for ('change_password'))
      
      hashed_password = generate_password_hash(new_password)
      mongo.db.users.update_one(
         {"username": session['user']},
         {"$set":{"password": hashed_password}}
      )
      flash('Contraseña Cambiada Correctamente', "success")
      return redirect( url_for ('profile'))
   return render_template ('change_password.html')

#### Rutas del perfil del Usuario ###

@app.route('/profile')
def profile():
    
    if 'user' not in session:
        return redirect(url_for('home'))
    
    user = mongo.db.users.find_one({"username": session['user']})
    return render_template ('profile.html', user=user)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    
    if 'user' not in session:
     return redirect(url_for('home'))
    
    user = mongo.db.users.find_one({"username": session['user']})

    if request.method == 'POST':
       username = request.form.get('username')
       email = request.form.get('email')
       profile_picture = request.form.get('profile_picture')

       mongo.db.users.update_one(
         {"username": session['user']},
         {"$set":{
            "username": username,
            "email": email,
            "profile_picture": profile_picture,
            "update_at": datetime.utcnow()
         }}
       )
       flash ("Perfil Actualizado Correctamente", "success")
       return redirect(url_for('profile'))
    return render_template('profile.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
