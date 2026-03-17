# BudgetWise Backend

Backend API para **BudgetWise**, una aplicación Android de finanzas personales diseñada para ayudar a los usuarios a registrar gastos, gestionar categorías y analizar sus hábitos financieros.

El backend proporciona una **API REST desarrollada con FastAPI** que permite a la aplicación móvil almacenar y recuperar información financiera.

---

# Descripción del proyecto

BudgetWise es una aplicación móvil de gestión financiera personal.
Este backend gestiona la persistencia de datos y expone endpoints REST que son consumidos por la aplicación Android.

El objetivo del proyecto es demostrar el desarrollo de un backend simple, estructurado y funcional que pueda integrarse fácilmente con aplicaciones móviles.

---

# Tecnologías utilizadas

* Python
* FastAPI
* SQLite
* Uvicorn

---

# Funcionalidades

* Registro de gastos
* Gestión de categorías
* Persistencia de datos
* API REST para cliente móvil
* Arquitectura backend modular

---

# Endpoints principales

| Método | Endpoint    | Descripción               |
| ------ | ----------- | ------------------------- |
| GET    | /expenses   | Obtener todos los gastos  |
| POST   | /expenses   | Crear un nuevo gasto      |
| GET    | /categories | Obtener categorías        |
| POST   | /categories | Crear una nueva categoría |

---

# Estructura del proyecto

backend/

app/
├── main.py → punto de entrada de FastAPI
├── database.py → configuración de base de datos
├── models.py → modelos de datos
└── routers → rutas de la API

requirements.txt
README.md

---

# Ejecutar el proyecto en local

Clonar el repositorio

git clone https://github.com/AlejandroDehesa/budgetwise-backend
cd budgetwise-backend

Crear entorno virtual

python -m venv .venv

Activar entorno virtual

Windows
.venv\Scripts\activate

Instalar dependencias

pip install -r requirements.txt

Ejecutar el servidor

uvicorn app.main:app --reload

Servidor disponible en:

http://127.0.0.1:8000

---

# Documentación automática de la API

FastAPI genera documentación automática:

Swagger UI
http://127.0.0.1:8000/docs

Redoc
http://127.0.0.1:8000/redoc

---

# Contexto del proyecto

Este backend forma parte del proyecto **BudgetWise**, una aplicación Android desarrollada con:

* Kotlin
* Jetpack Compose
* arquitectura MVVM
* base de datos Room

La aplicación móvil consume esta API para almacenar y recuperar datos financieros.

---

# Despliegue

El backend está desplegado en **Railway**, permitiendo que la aplicación Android acceda a la API desde internet.

---

# Autor

Alejandro Dehesa Delgado

Estudiante de Desarrollo de Aplicaciones Multiplataforma (DAM) interesado en desarrollo backend, aplicaciones móviles y sistemas basados en inteligencia artificial.
