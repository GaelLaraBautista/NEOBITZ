from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contacto')
def contacto():
   return render_template('contacto.html')

##### rutas de Registro #######

@app.route('/login')
def login():
 return render_template('login.html')

@app.route('signup')
def signup():
   return render_template('signup.html')


if __name__ == '__main__':
    app.run(debug=True)
