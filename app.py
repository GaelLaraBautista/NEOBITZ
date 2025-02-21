from flask import Flask, render_template, request, redirect, url_for, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
app.config ['MONGO_URI'] = os.getenv('MONGO_URI')

#### Conexión a Base de Datos Con MongoDB ###
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
