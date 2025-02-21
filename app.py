from flask import Flask, render_template, request, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secreto_seguro'

#### Conexión a Base de Datos Con MongoDB ###

app.config['MONGO_URI'] = "mongodb+srv://larabautistagael:xlg36au6xU53O9zF@neobytedb.bipzm.mongodb.net/neobyteDB"
mongo = PyMongo(app)

#### Rutas Ordinarias ####

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contacto')
def contacto():
   return render_template('contacto.html')

##### Rutas de Registro #######

@app.route('/login')
def login():
 return render_template('login.html')

@app.route('/signup')
def signup():
   return render_template('signup.html')

#### Rutas de Tareas ###


if __name__ == '__main__':
    app.run(debug=True)
