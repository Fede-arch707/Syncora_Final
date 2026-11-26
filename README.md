# Syncora — Sistema de Gestión de Salones

## Descripción del proyecto

Sycora es un sistema web desarrollado con Django que permite administrar clientes, reservas y pagos de salones de eventos.

Su objetivo principal es facilitar la organización de la información, evitando conflictos entre reservas y permitiendo consultar el estado de los pagos de cada cliente.

Este proyecto fue desarrollado como trabajo académico utilizando Python, Django, HTML, CSS, JavaScript y SQLite.

## Tecnologías utilizadas

- **Python:** lenguaje de programación del backend.
- **Django:** framework para desarrollar la aplicación web.
- **SQLite:** base de datos del sistema.
- **HTML:** estructura de las páginas.
- **CSS:** diseño y estilos visuales.
- **JavaScript:** funciones interactivas del calendario.
- **Git y GitHub:** control de versiones y almacenamiento del código.

## Funcionalidades principales

### Gestión de clientes

- Registrar nuevos clientes.
- Consultar y modificar información.
- Buscar clientes por nombre, DNI o teléfono.
- Consultar el historial de reservas.
- Identificar clientes vetados.
- Eliminar registros cuando corresponda.

### Calendario de reservas

- Visualización de tres meses por pantalla.
- Navegación entre meses y años.
- Identificación de fechas disponibles, reservadas y alquiladas.
- Creación y edición de reservas.
- Validación para evitar reservas superpuestas del mismo salón.
- Restricción de nuevas reservas para clientes vetados.

### Gestión de pagos

- Registro de pagos iniciales.
- Registro de pagos posteriores.
- Cálculo del total abonado.
- Cálculo automático del saldo pendiente.
- Consulta del historial de pagos.
- Validación para impedir pagos superiores al saldo restante.

### Exportación a Excel

El sistema permite exportar la información a un archivo Excel, incluyendo clientes, reservas y pagos.

### Autenticación

- Registro de usuarios.
- Inicio de sesión.
- Cierre de sesión.
- Protección de las vistas mediante `login_required`.

## Estructura del proyecto

El sistema se divide en dos aplicaciones principales:

**clientes:** gestiona los datos personales, el registro y la administración de clientes.

**reservas:** administra los salones, las categorías de eventos, las reservas, el calendario y los pagos.

Otras carpetas importantes:

- `config/`: configuración general de Django.
- `templates/`: plantillas HTML.
- `static/`: archivos CSS y JavaScript.
- `manage.py`: administración y ejecución del proyecto.
- `requirements.txt`: dependencias necesarias.

## Modelos de la base de datos

El proyecto cuenta con cinco modelos principales:

1. **Cliente:** almacena información y condición del cliente.
2. **Salon:** representa los salones disponibles.
3. **CategoriaEvento:** organiza los tipos de eventos.
4. **Reserva:** registra fechas, importes, cuotas y estados.
5. **Pago:** almacena los pagos asociados a cada reserva.

Los modelos utilizan relaciones `ForeignKey` y validaciones para mantener la integridad de la información.

## Instalación y ejecución

**Requisitos:** Python y las dependencias indicadas en `requirements.txt`.

Abrir una terminal en la carpeta principal del proyecto.

**1. Crear un entorno virtual:**

`python -m venv .venv`

**2. Activar el entorno virtual en Windows PowerShell:**

`.\.venv\Scripts\Activate.ps1`

**3. Instalar las dependencias:**

`python -m pip install -r requirements.txt`

**4. Aplicar las migraciones:**

`python manage.py migrate`

**5. Crear un administrador (opcional):**

`python manage.py createsuperuser`

**6. Iniciar el servidor:**

`python manage.py runserver`

**7. Abrir en el navegador:**

http://127.0.0.1:8000/

Si es una instalación nueva, se pueden configurar los salones y las categorías de eventos desde el administrador de Django.

## Seguridad y configuración

El proyecto utiliza variables de entorno para configurar `DJANGO_SECRET_KEY`, `DJANGO_DEBUG` y `DJANGO_ALLOWED_HOSTS`.

La configuración predeterminada está destinada exclusivamente al desarrollo local. Antes de desplegar el sistema públicamente, se deben configurar valores seguros.

La base de datos local, los entornos virtuales y los archivos de configuración sensibles están excluidos del repositorio mediante `.gitignore`.

## Objetivo académico

El proyecto permite aplicar conocimientos de:

- Arquitectura de aplicaciones Django.
- Modelos y ORM.
- Migraciones de base de datos.
- Relaciones entre tablas.
- Vistas y rutas.
- Formularios y validaciones.
- Autenticación de usuarios.
- Herencia de plantillas.
- Control de versiones mediante Git y GitHub.

## Estado del proyecto

Versión académica funcional, con gestión de clientes, reservas, pagos, calendario y exportación a Excel.