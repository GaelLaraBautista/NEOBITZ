document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const taskList = document.getElementById('task-list');
    const newTaskBtn = document.getElementById('new-task-btn');
    const taskModal = document.getElementById('task-modal');
    const closeBtn = document.querySelector('.close-btn');
    const taskForm = document.getElementById('task-form');
    const filterStatus = document.getElementById('filter-status');

    // Eventos
    newTaskBtn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);
    filterStatus.addEventListener('change', loadTasks);
    taskForm.addEventListener('submit', handleSubmit);

    // Cargar tareas iniciales (desde Jinja2 o API)
    function loadTasks() {
        const status = filterStatus.value;
        if (status === 'all') return; // Ya están renderizadas por Jinja2
        
        fetch(`/api/tasks?status=${status}`)
            .then(response => response.json())
            .then(tasks => {
                taskList.innerHTML = tasks.map(task => `
                    <div class="task-card ${task.status.replace(' ', '-')}">
                        <div class="task-info">
                            <h3>${task.title}</h3>
                            <p>${task.description || 'Sin descripción'}</p>
                            <small>Estado: ${task.status}</small>
                        </div>
                        <div class="task-actions">
                            <button onclick="editTask('${task._id}')">
                                <i class="material-icons">edit</i>
                            </button>
                            <button onclick="deleteTask('${task._id}')">
                                <i class="material-icons">delete</i>
                            </button>
                        </div>
                    </div>
                `).join('');
            });
    }

    // Manejar envío del formulario
    function handleSubmit(e) {
        e.preventDefault();
        const taskId = document.getElementById('task-id').value;
        const url = taskId ? `/api/tasks/${taskId}` : '/api/tasks';
        const method = taskId ? 'PUT' : 'POST';

        fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {{ session.token | tojson | safe }}' // Adapta según tu auth
            },
            body: JSON.stringify({
                title: document.getElementById('task-title').value,
                description: document.getElementById('task-description').value,
                status: document.getElementById('task-status').value
            })
        }).then(() => {
            closeModal();
            window.location.reload(); // Recargar para ver cambios
        });
    }

    // Funciones auxiliares
    function openModal() {
        taskModal.style.display = 'block';
    }

    function closeModal() {
        taskModal.style.display = 'none';
        taskForm.reset();
    }

    // Funciones globales para botones en las tarjetas
    window.editTask = async (taskId) => {
        const task = await fetch(`/api/tasks/${taskId}`).then(res => res.json());
        document.getElementById('task-id').value = task._id;
        document.getElementById('task-title').value = task.title;
        document.getElementById('task-description').value = task.description || '';
        document.getElementById('task-status').value = task.status;
        document.getElementById('modal-title').textContent = 'Editar Tarea';
        openModal();
    };

    window.deleteTask = (taskId) => {
        if (confirm('¿Eliminar esta tarea?')) {
            fetch(`/api/tasks/${taskId}`, { method: 'DELETE' })
                .then(() => window.location.reload());
        }
    };

 async function saveTask() {
        const taskData = {
            title: document.getElementById('task-title').value,
            description: document.getElementById('task-description').value,
            status: document.getElementById('task-status').value
        };
    
        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(taskData)
            });
    
            const result = await response.json();
            
            if (response.ok) {
                closeModal();
                // Recargar la página para ver los cambios
                window.location.reload();
            } else {
                alert(`Error: ${result.error || 'No se pudo guardar la tarea'}`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error al conectar con el servidor');
        }
    }
});