from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from passlib.context import CryptContext
from dotenv import load_dotenv
from flask_cors import CORS
from datetime import datetime, timedelta
import os
from bson.objectid import ObjectId

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
app.config['MONGO_URI'] = os.getenv('MONGO_URI')

#### Conexión a Base de Datos Con MongoDB ###
mongo = PyMongo(app)

# Inicializamos el contexto de Passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#### Rutas Ordinarias ####

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/inicio')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    #### Obtener métricas de MongoDB ######
    total_users = mongo.db.users.count_documents({})
    pending_tasks = mongo.db.tasks.count_documents({"status": "pendiente"})
    new_messages = mongo.db.messages.count_documents({"read": False})

    ### Obtener Datos de la Gráfica ###

    # Obtener lista de usuarios registrados por mes
    users_by_month = []  # Lista para almacenar el número de usuarios por mes
    for i in range(6):  # Capturar la información de los últimos 6 meses
        start_date = datetime.now() - timedelta(days=30 * (6 - i))
        end_date = datetime.now() - timedelta(days=30 * (5 - i))
        count = mongo.db.users.count_documents({
            "created_at": {"$gte": start_date, "$lt": end_date}
        })
        users_by_month.append(count)

    ### Obtener las tareas por status ###
    tasks_by_status = [
        mongo.db.tasks.count_documents({"status": "pendiente"}),
        mongo.db.tasks.count_documents({"status": "en progreso"}),
        mongo.db.tasks.count_documents({"status": "completada"})
    ]

    #### Actividad Reciente ######
    recent_activity = list(mongo.db.activity_logs.find().sort("timestamp", -1).limit(5))

    return render_template(
        'index.html',
        total_users=total_users,
        pending_tasks=pending_tasks,  
        new_messages=new_messages,
        recent_activity=recent_activity,
        users_by_month=users_by_month,
        tasks_by_status=tasks_by_status 
    )

@app.route('/contacto')
def contacto():
   return render_template('contacto.html')

##### Rutas de Registro y Cambio de Contraseñas #######

@app.route('/login', methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    user = mongo.db.users.find_one({"username": username})
    if user:
        # Verificar si la contraseña es válida con Passlib
        if pwd_context.verify(password, user["password"]):  # Verificar contraseña en hash
            session["user"] = user["username"]
            return redirect(url_for("index"))
        else:
            return jsonify({"message": "Credenciales incorrectas"}), 401
    else:
        return jsonify({"message": "Usuario no encontrado"}), 404

@app.route('/signup', methods=['GET', 'POST'])
def signup():
   if request.method == "POST":
      ### Parametros a guardar en la Base de datos ####
      username = request.form["username"]
      email = request.form["email"]
      password = request.form["password"]
      #### Encriptado de la contraseña ###
      hashed_pw = pwd_context.hash(password)  # Encriptar la contraseña con Passlib

      if mongo.db.users.find_one({"email": email}):
         return jsonify({"message": "Este correo ya existe"})
   
      user_data = {
         "username": username,
         "email": email,
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
      return redirect(url_for('home'))

   if request.method == 'POST':
      current_password = request.form.get('current_password')
      new_password = request.form.get('new_password')
      confirm_password = request.form.get('confirm_password')

      user = mongo.db.users.find_one({"username": session['user']})

      # Verificar si la contraseña actual es correcta
      if not pwd_context.verify(current_password, user['password']):
         flash('La contraseña actual es Incorrecta', "error")
         return redirect(url_for('change_password'))
      
      if new_password != confirm_password:
         flash('Las Contraseñas No Coinciden', "error")
         return redirect(url_for('change_password'))
      
      # Encriptar la nueva contraseña
      hashed_password = pwd_context.hash(new_password)
      mongo.db.users.update_one(
         {"username": session['user']},
         {"$set": {"password": hashed_password}}
      )
      flash('Contraseña Cambiada Correctamente', "success")
      return redirect(url_for('profile'))
   return render_template('change_password.html')

#### Rutas del perfil del Usuario ###

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    user = mongo.db.users.find_one({"username": session['user']})
    return render_template('profile.html', user=user)

@app.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        return redirect(url_for('home'))
    
    user = mongo.db.users.find_one({"username": session['user']})

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        profile_picture = request.form.get('profile_picture')

        print(f"Updating user: {username}, {email}, {profile_picture}")  # Depuración

        mongo.db.users.update_one(
            {"username": session['user']},
            {"$set": {
                "username": username,
                "email": email,
                "profile_picture": profile_picture,
                "updated_at": datetime.utcnow()
            }}
        )

        session['user'] = username  

        flash("Perfil Actualizado Correctamente", "success")
        return redirect(url_for('profile')) 

    return render_template('profile_edit.html', user=user)



if __name__ == '__main__':
    app.run(debug=True)
