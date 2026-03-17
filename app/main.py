import time
import uuid
# time: timestamps (ms) para created_at/updated_at
# uuid: generar IDs únicos para usuarios

from fastapi import FastAPI, Depends, HTTPException
# FastAPI: framework web
# Depends: inyección de dependencias (DB session)
# HTTPException: errores HTTP controlados (400/401/404/409)

from fastapi.middleware.cors import CORSMiddleware
# CORS: permitir llamadas desde Android/emulador o navegador

from sqlalchemy.orm import Session
from sqlalchemy import select, delete
# SQLAlchemy ORM Session: conexión/transacción con la BD
# select/delete: queries "core" para leer/borrar

from .db import SessionLocal, engine, Base
# SessionLocal: factory de sesiones (cada request tiene la suya)
# engine: conexión a la BD
# Base: metadata para crear tablas

from .models import User, Transaction
# Modelos ORM: mapeo a tablas

from .schemas import SignUpIn, LoginIn, UserOut, TransactionIn, TransactionOut
# Schemas Pydantic: validación de entrada/salida y tipado de API


# ------------------------------
# APP
# ------------------------------
app = FastAPI(title="BudgetWise API")
# Crea la app FastAPI con un título visible en /docs


# ------------------------------
# CORS
# ------------------------------
# Permite que el cliente (Android / Postman / web) llame a la API sin bloqueo por CORS.
# allow_origins=["*"] es cómodo para demo, pero inseguro en producción (se restringe).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # para demo. Luego restringes.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------
# DB DEPENDENCY
# ------------------------------
# Generador que crea una sesión por request y la cierra al terminar.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------
# STARTUP
# ------------------------------
# En el arranque crea las tablas si no existen (migraciones "manuales" de demo).
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


# =========================================================
# AUTH (DEMO, sin JWT todavía)
# =========================================================

@app.post("/auth/signup", response_model=UserOut)
def signup(body: SignUpIn, db: Session = Depends(get_db)):
    # Recibe username + password (SignUpIn), devuelve UserOut (sin password).

    # Normaliza username (email) para evitar duplicados por mayúsculas/espacios.
    username = body.username.strip().lower()
    password = body.password.strip()

    # Validaciones mínimas.
    if not username:
        raise HTTPException(status_code=400, detail="username obligatorio")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="password demasiado corta")

    # Comprueba si existe ya un usuario con ese username.
    existing = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if existing:
        # 409 = conflicto (recurso ya existe)
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese email")

    # Crea el usuario en BD con un UUID como id.
    # Nota: password en claro -> solo demo (en prod: hash).
    user = User(
        id=str(uuid.uuid4()),
        username=username,
        password=password,  # demo
    )

    # Persiste y confirma cambios.
    db.add(user)
    db.commit()

    # Devuelve salida filtrada (id + username).
    return UserOut(id=user.id, username=user.username)


@app.post("/auth/login", response_model=UserOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    # Login por username + password, devuelve el usuario si coincide.

    username = body.username.strip().lower()
    password = body.password.strip()

    # Busca usuario por username.
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()

    # Si no existe o password no coincide => 401 (no autorizado).
    if not user or user.password != password:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    return UserOut(id=user.id, username=user.username)


@app.post("/auth/reset-password")
def reset_password(body: SignUpIn, db: Session = Depends(get_db)):
    # Endpoint de demo para reset: reusa SignUpIn (username + password nuevo).
    # En producción esto NO sería así (faltan tokens, email verification, etc.)

    username = body.username.strip().lower()
    new_pass = body.password.strip()

    # Busca usuario.
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Valida password.
    if len(new_pass) < 4:
        raise HTTPException(status_code=400, detail="password demasiado corta")

    # Actualiza y confirma.
    user.password = new_pass
    db.commit()

    return {"ok": True}


# =========================================================
# TRANSACTIONS
# =========================================================

@app.get("/users/{user_id}/transactions", response_model=list[TransactionOut])
def list_transactions(user_id: str, db: Session = Depends(get_db)):
    # Devuelve todas las transacciones del usuario.

    # 1) Validar que el usuario existe (evita listar de un id inventado).
    u = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 2) Traer transacciones por user_id.
    rows = db.execute(
        select(Transaction).where(Transaction.user_id == user_id)
    ).scalars().all()

    # Nota: comentas que date es string dd/MM/yyyy => ordenar en SQL no es fiable.
    # Aquí solo devuelves; el cliente puede ordenar.
    return [
        TransactionOut(
            id=t.id,
            user_id=t.user_id,
            type=t.type,
            amount=t.amount,
            category=t.category,
            note=t.note,
            date=t.date,
            created_at=t.created_at,
            updated_at=t.updated_at
        )
        for t in rows
    ]


@app.post("/users/{user_id}/transactions", response_model=TransactionOut)
def upsert_transaction(user_id: str, body: TransactionIn, db: Session = Depends(get_db)):
    # "Upsert": si existe la tx con ese id para el usuario -> update, si no -> insert.

    # Validar usuario.
    u = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Timestamp en milisegundos (estilo Android).
    now = int(time.time() * 1000)

    # Busca si la transacción ya existe (mismo id + mismo user).
    existing = db.execute(
        select(Transaction).where(
            Transaction.id == body.id,
            Transaction.user_id == user_id
        )
    ).scalar_one_or_none()

    if existing:
        # UPDATE
        existing.type = body.type
        existing.amount = body.amount
        existing.category = body.category
        existing.note = body.note
        existing.date = body.date
        existing.updated_at = now
        db.commit()
        t = existing
    else:
        # INSERT
        t = Transaction(
            id=body.id,          # el id viene del cliente (Android)
            user_id=user_id,     # se fuerza por path param (no por body)
            type=body.type,
            amount=body.amount,
            category=body.category,
            note=body.note,
            date=body.date,
            created_at=now,
            updated_at=now,
        )
        db.add(t)
        db.commit()

    # Devuelve el objeto actualizado/creado.
    return TransactionOut(
        id=t.id,
        user_id=t.user_id,
        type=t.type,
        amount=t.amount,
        category=t.category,
        note=t.note,
        date=t.date,
        created_at=t.created_at,
        updated_at=t.updated_at
    )


@app.delete("/users/{user_id}/transactions/{tx_id}")
def delete_transaction(user_id: str, tx_id: str, db: Session = Depends(get_db)):
    # Borra una transacción concreta del usuario.

    # Validar usuario.
    u = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Ejecuta DELETE filtrando por tx_id y user_id (evita borrar de otro usuario).
    res = db.execute(
        delete(Transaction).where(
            Transaction.id == tx_id,
            Transaction.user_id == user_id
        )
    )
    db.commit()

    # Si no borró filas => no existía esa transacción para ese usuario.
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")

    return {"ok": True}