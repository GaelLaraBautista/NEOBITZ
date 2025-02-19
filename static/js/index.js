// Validación del formulario de registro
document.getElementById("signup-form").addEventListener("submit", function (e) {
    e.preventDefault();

    // Obtener los valores de los campos
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm-password").value;

    // Validar que las contraseñas coincidan
    if (password !== confirmPassword) {
        alert("Las contraseñas no coinciden.");
        return;
    }

    // Validar la longitud de la contraseña
    if (password.length < 6) {
        alert("La contraseña debe tener al menos 6 caracteres.");
        return;
    }

    // Simular envío de datos (puedes reemplazar esto con una llamada a tu backend)
    alert(`Registro exitoso:\nNombre: ${name}\nEmail: ${email}`);
});

// Funciones para el convertidor de archivos
function convertToWord() {
    alert("Convertir PDF a Word");
}

function convertToExcel() {
    alert("Convertir PDF a Excel");
}

function convertToPDF() {
    alert("Convertir Word a PDF");
}

// Validación del formulario de login
document.getElementById("login-form").addEventListener("submit", function (e) {
    e.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    alert(`Usuario: ${username}\nContraseña: ${password}`);
});

// Validación del formulario de contacto
document.getElementById("contact-form").addEventListener("submit", function (e) {
    e.preventDefault();
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const message = document.getElementById("message").value;
    alert(`Nombre: ${name}\nEmail: ${email}\nMensaje: ${message}`);
});