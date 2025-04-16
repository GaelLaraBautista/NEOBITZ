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
reportes = mongo.db.reportes
notificaciones = mongo.db.notificaciones

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


######## Rutas para las tareas 

# Ruta para renderizar el template con datos iniciales
@app.route('/tareas', methods=['GET', 'POST'])
def tareas():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Obtener parámetro de filtro
    status_filter = request.args.get('status', 'all')

    # Consulta base
    query = {"user": session['user']}
    if status_filter != 'all':
        query["status"] = status_filter

    # Manejar formulario de nueva/edición tarea
    if request.method == 'POST':
        task_id = request.form.get('task_id')
        task_data = {
            "title": request.form['title'],
            "description": request.form.get('description', ''),
            "status": request.form['status'],
            "user": session['user'],
            "updated_at": datetime.utcnow()
        }

        if task_id:  # Editar tarea existente
            mongo.db.tasks.update_one(
                {"_id": ObjectId(task_id), "user": session['user']},
                {"$set": task_data}
            )
            flash('Tarea actualizada correctamente', 'success')
        else:  # Nueva tarea
            task_data["created_at"] = datetime.utcnow()
            mongo.db.tasks.insert_one(task_data)
            flash('Tarea creada correctamente', 'success')

        return redirect(url_for('tareas'))

    # Obtener tareas para mostrar
    tasks = list(mongo.db.tasks.find(query).sort("created_at", -1))
    
    # Convertir ObjectId a string para Jinja2
    tasks = [{**task, "_id": str(task["_id"])} for task in tasks]

    return render_template(
        'tasks.html',
        tasks=tasks,
        status_filter=status_filter,
        task_edit=None  # Para el formulario de edición
    )

@app.route('/tareas/eliminar/<task_id>')
def eliminar_tarea(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    mongo.db.tasks.delete_one({
        "_id": ObjectId(task_id),
        "user": session['user']
    })
    flash('Tarea eliminada correctamente', 'success')
    return redirect(url_for('tareas'))

@app.route('/tareas/editar/<task_id>')
def editar_tarea(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    task = mongo.db.tasks.find_one({
        "_id": ObjectId(task_id),
        "user": session['user']
    })
    
    if not task:
        flash('Tarea no encontrada', 'error')
        return redirect(url_for('tareas'))

    tasks = list(mongo.db.tasks.find({"user": session['user']}))
    return render_template(
        'tasks.html',
        tasks=tasks,
        status_filter='all',
        task_edit={**task, "_id": str(task["_id"])}  # Datos para edición
    )

@app.route('/get-tasks', methods=['GET'])
def get_tasks():
    if 'user' not in session:
        return jsonify({"error": "No autenticado"}), 401
    
    status = request.args.get('status', 'pendiente')
    tasks = list(mongo.db.tasks.find({
        "user": session['user'],
        "status": status
    }).sort("created_at", -1).limit(5))
    
    # Formatear respuesta
    formatted_tasks = []
    for task in tasks:
        formatted_tasks.append({
            "title": task['title'],
            "status": task['status'],
            "created_at": task['created_at'].strftime("%d/%m/%Y")
        })
    
    return jsonify({"tasks": formatted_tasks})

@app.route('/search-tasks', methods=['GET'])
def search_tasks():
    query = request.args.get('q', '')
    
    # Búsqueda flexible (por título o descripción)
    tasks = list(mongo.db.tasks.find({
        "user": session['user'],
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}}
        ]
    }).limit(5))
    
    return jsonify({"tasks": tasks})

###### Reportes ########

@app.route('/reportes')
def listar_reportes():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Buscar reportes del usuario actual
    mis_reportes = list(reportes.find({"usuario": session['user']}).sort("fecha_creacion", -1))
    
    return render_template('listar.html', 
                         reportes=mis_reportes)

@app.route('/reportes/crear', methods=['GET', 'POST'])
def crear_reporte():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 1. Validar y obtener datos del formulario
        titulo = request.form.get('titulo', '').strip()
        if not titulo:
            flash('El título es obligatorio', 'error')
            return redirect(url_for('crear_reporte'))
        
        tipo = request.form.get('tipo', 'tareas')
        estados = request.form.getlist('estado')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        
        # 2. Validar fechas
        if fecha_inicio and fecha_fin:
            try:
                fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
                if fecha_inicio_dt > fecha_fin_dt:
                    flash('La fecha de inicio no puede ser mayor a la fecha final', 'error')
                    return redirect(url_for('crear_reporte'))
            except ValueError:
                flash('Formato de fecha inválido', 'error')
                return redirect(url_for('crear_reporte'))
        
        # 3. Construir query para MongoDB
        query = {"user": session['user']}
        
        # Filtro por estado
        if estados:
            query["status"] = {"$in": estados}
        
        # Filtro por fechas
        if fecha_inicio or fecha_fin:
            query["created_at"] = {}
            if fecha_inicio:
                query["created_at"]["$gte"] = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            if fecha_fin:
                query["created_at"]["$lte"] = datetime.strptime(fecha_fin + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
        
        # 4. Generar datos del reporte (sin JSON)
        datos_reporte = {}
        
        if tipo == 'tareas':
            # Estadísticas básicas
            total_tareas = mongo.db.tasks.count_documents(query)
            tareas_por_estado = {}
            
            # Conteo por estado
            for estado in (estados or ['pendiente', 'en progreso', 'completada']):
                count = mongo.db.tasks.count_documents({**query, "status": estado})
                if count > 0:
                    tareas_por_estado[estado] = count
            
            # Ejemplos recientes
            tareas_ejemplo = list(mongo.db.tasks.find(
                query,
                {"title": 1, "status": 1, "created_at": 1, "updated_at": 1}
            ).sort("created_at", -1).limit(5))
            
            # Calcular tiempos
            for tarea in tareas_ejemplo:
                tarea['tiempo_dias'] = round(
                    (tarea['updated_at'] - tarea['created_at']).total_seconds() / 86400, 
                    2
                )
            
            datos_reporte = {
                'total_tareas': total_tareas,
                'tareas_por_estado': tareas_por_estado,
                'ejemplos': tareas_ejemplo
            }
        
        # 5. Guardar en MongoDB
        nuevo_reporte = {
            "titulo": titulo,
            "tipo": tipo,
            "filtros": {
                "estado": estados,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin
            },
            "datos": datos_reporte,
            "usuario": session['user'],
            "fecha_creacion": datetime.utcnow(),
            "fecha_actualizacion": datetime.utcnow()
        }
        
        reportes.insert_one(nuevo_reporte)
        flash('Reporte creado con éxito', 'success')
        return redirect(url_for('detalle_reporte', id=nuevo_reporte['_id']))
    
    # GET: Mostrar formulario
    return render_template('crear.html')

@app.route('/reportes/editar/<ObjectId:id>', methods=['GET', 'POST'])
def editar_reporte(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    reporte = reportes.find_one({"_id": id, "usuario": session['user']})
    if not reporte:
        flash('Reporte no encontrado', 'error')
        return redirect(url_for('listar_reportes'))
    
    if request.method == 'POST':
        # Actualizar reporte
        updates = {
            "titulo": request.form['titulo'],
            "filtros.estado": request.form.getlist('estado'),
            "filtros.fecha_inicio": request.form['fecha_inicio'],
            "filtros.fecha_fin": request.form['fecha_fin'],
            "fecha_actualizacion": datetime.utcnow()
        }
        
        reportes.update_one({"_id": id}, {"$set": updates})
        flash('Reporte actualizado', 'success')
        return redirect(url_for('detalle_reporte', id=id))
    
    return render_template('editar.html', reporte=reporte)

@app.route('/reportes/eliminar/<ObjectId:id>')
def eliminar_reporte(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    result = reportes.delete_one({"_id": id, "usuario": session['user']})
    if result.deleted_count > 0:
        flash('Reporte eliminado', 'success')
    else:
        flash('No se pudo eliminar el reporte', 'error')
    
    return redirect(url_for('listar_reportes'))

@app.route('/reportes/<ObjectId:id>')
def detalle_reporte(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    reporte = reportes.find_one({"_id": id, "usuario": session['user']})
    if not reporte:
        flash('Reporte no encontrado', 'error')
        return redirect(url_for('listar_reportes'))
    
    return render_template('detalle.html', 
                         reporte=reporte,
                         ahora=datetime.now().strftime("%d/%m/%Y %H:%M"))

def generar_datos_reporte(tipo, filtros, usuario):
    query = {"user": usuario}
    
    # Filtros básicos
    if filtros.get('estado'):
        query["status"] = {"$in": filtros['estado']}
    
    # Datos mínimos requeridos
    return {
        "total_tareas": mongo.db.tasks.count_documents(query),
        "tareas_por_estado": {
            estado: mongo.db.tasks.count_documents({**query, "status": estado})
            for estado in (filtros.get('estado') or ['pendiente', 'en progreso', 'completada'])
        }
    }

@app.route('/reportes/regenerar/<ObjectId:id>')
def regenerar_reporte(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    reporte = reportes.find_one({"_id": id, "usuario": session['user']})
    if not reporte:
        flash('Reporte no encontrado', 'error')
        return redirect(url_for('listar_reportes'))
    
    # Regenerar datos con los mismos filtros
    nuevos_datos = generar_datos_reporte(
        tipo=reporte['tipo'],
        filtros=reporte['filtros'],
        usuario=session['user']
    )
    
    reportes.update_one(
        {"_id": id},
        {"$set": {
            "datos": nuevos_datos,
            "fecha_actualizacion": datetime.utcnow()
        }}
    )
    
    flash('¡Datos actualizados con la información más reciente!', 'success')
    return redirect(url_for('editar_reporte', id=id))

###### Notificaciones ######

def crear_notificacion(usuario, mensaje, tipo='info'):
    """Crea una notificación en la base de datos"""
    notificaciones.insert_one({
        "usuario": usuario,
        "mensaje": mensaje,
        "tipo": tipo,  # info, alerta, exito
        "leida": False,
        "fecha": datetime.utcnow()
    })

def obtener_notificaciones(usuario, limit=5):
    """Obtiene las notificaciones no leídas"""
    return list(notificaciones.find(
        {"usuario": usuario},
        sort=[("fecha", -1)],
        limit=limit
    ))

@app.route('/notificaciones')
def ver_notificaciones():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Marcar como leídas al visualizarlas
    notificaciones.update_many(
        {"usuario": session['user'], "leida": False},
        {"$set": {"leida": True}}
    )
    
    return render_template(
        'notificaciones.html',
        notificaciones=obtener_notificaciones(session['user'], limit=10)
    )


@app.context_processor
def inject_notificaciones():
    if 'user' in session:
        return dict(
            notificaciones=mongo.db.notificaciones,
            num_notificaciones=mongo.db.notificaciones.count_documents({
                "usuario": session['user'],
                "leida": False
            })
        )
    return dict(notificaciones=None, num_notificaciones=0)

if __name__ == '__main__':
    app.run(debug=True)
