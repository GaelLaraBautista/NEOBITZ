// ========== FUNCIONES DEL CHATBOT ========== //

// Función principal de inicialización
document.addEventListener('DOMContentLoaded', function() {
    setupChatbotTasks();
    initChatbotNotifications();
    setupEventListeners();
});

// ===== CONFIGURACIÓN DE EVENTOS ===== //
function setupEventListeners() {
    // Botón de enviar
    document.getElementById('chatbotSendButton').addEventListener('click', sendChatbotMessage);
    
    // Input para enviar con Enter
    document.getElementById('chatbotInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatbotMessage();
        }
    });
}

// Alternativa para manejar Enter desde HTML
function handleChatbotKeyPress(e) {
    if (e.key === 'Enter') {
        sendChatbotMessage();
    }
}

// ===== GESTIÓN DE TAREAS ===== //
async function getTasksFromBot(status = 'pendiente') {
    try {
        const response = await fetch(`/get-tasks?status=${status}`);
        const data = await response.json();
        
        if (data.tasks?.length > 0) {
            let message = `📌 Tareas ${status}:\n`;
            data.tasks.forEach((task, index) => {
                message += `\n${index + 1}. ${task.title} (${task.created_at})`;
            });
            return message;
        }
        return `No hay tareas ${status} registradas.`;
    } catch (error) {
        console.error("Error:", error);
        return "❌ Ocurrió un error al consultar las tareas";
    }
}

async function searchTasks(query) {
    try {
        const response = await fetch(`/search-tasks?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.tasks?.length > 0) {
            let message = `🔍 Resultados para "${query}":\n`;
            data.tasks.forEach((task, index) => {
                message += `\n${index + 1}. ${task.title} (${task.status})`;
            });
            return message;
        }
        return `No se encontraron tareas para "${query}"`;
    } catch (error) {
        console.error("Error:", error);
        return "❌ Error al buscar tareas";
    }
}

// ===== INTERACCIÓN DEL USUARIO ===== //
function setupChatbotTasks() {
    const commands = {
        "tareas": () => getTasksFromBot(),
        "pendientes": () => getTasksFromBot('pendiente'),
        "en progreso": () => getTasksFromBot('en progreso'),
        "completadas": () => getTasksFromBot('completada'),
        "buscar": async () => {
            const query = prompt("¿Qué tarea deseas buscar?");
            return query ? await searchTasks(query) : "Búsqueda cancelada";
        }
    };

    window.sendChatbotMessage = async function() {
        const input = document.getElementById('chatbotInput');
        const userInput = input.value.trim();
        
        if (userInput) {
            displayMessage(userInput, 'user');
            input.value = '';
            
            // Manejo de comandos especiales
            const lowerInput = userInput.toLowerCase();
            if (commands[lowerInput]) {
                const response = await commands[lowerInput]();
                displayMessage(response, 'bot');
            } 
            // Respuesta por defecto
            else {
                const defaultResponses = [
                    "¿Quieres que revise tus tareas? Prueba con 'tareas'",
                    "Puedo ayudarte con tus tareas. Di 'pendientes' o 'completadas'",
                    "No entendí. Prueba con 'ayuda' para ver opciones"
                ];
                const randomResponse = defaultResponses[Math.floor(Math.random() * defaultResponses.length)];
                displayMessage(randomResponse, 'bot');
            }
        }
    };
}

// ===== NOTIFICACIONES ===== //
function initChatbotNotifications() {
    // Mostrar primera notificación después de 10 segundos
    setTimeout(showRandomNotification, 10000);
    
    // Mostrar periódicamente (cada 30-45 segundos)
    setInterval(() => {
        if (document.getElementById('chatbotWindow').style.display === 'none') {
            showRandomNotification();
        }
    }, 35000 + Math.random() * 15000); // Aleatorio entre 35-50 segundos
}

function showRandomNotification() {
    const messages = [
        "¡Hey aquí! 👋", 
        "¿Necesitas ayuda con tus tareas? 🤔",
        "Pregúntame por tus tareas pendientes 💡",
        "¡Hola! Di 'tareas' para ver tu lista 😊",
        "Recuerda revisar tus tareas completadas ✅"
    ];
    
    const notification = document.getElementById('chatbotNotification');
    const bubble = notification.querySelector('.notification-bubble');
    
    bubble.textContent = messages[Math.floor(Math.random() * messages.length)];
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 5000);
}

// ===== FUNCIONES AUXILIARES ===== //
function toggleChatbot() {
    const chatbot = document.getElementById('chatbotWindow');
    const currentDisplay = chatbot.style.display;
    chatbot.style.display = currentDisplay === 'none' ? 'flex' : 'none';
    
    if (currentDisplay === 'none') {
        document.getElementById('chatbotNotification').classList.remove('show');
    }
}

function displayMessage(text, sender) {
    const messagesContainer = document.getElementById('chatbotMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.innerHTML = text.replace(/\n/g, '<br>');
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}