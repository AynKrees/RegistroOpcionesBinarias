import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

# 1. Configuración Híbrida (PC o Nube)
if "supabase" in st.secrets:
    # Si estamos en la nube, usamos el link de Supabase que guardaste en Secrets
    DATABASE_URL = st.secrets["supabase"]["URL"]
else:
    # Si estás en tu PC, sigue usando el archivo local
    DATABASE_URL = 'sqlite:///trading.db'

# Fix para SQLAlchemy y Postgres
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
Base = declarative_base()

# 2. Tabla de Estrategias
class Strategy(Base):
    __tablename__ = 'strategies'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

# 3. Tabla de Trades
class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    executed_at = Column(DateTime, default=datetime.datetime.now)
    asset = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    result = Column(String, nullable=False)
    stake_amount = Column(Float, nullable=False)
    payout_percent = Column(Integer, nullable=False)
    profit_amount = Column(Float)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    screenshot_path = Column(String)
    notes = Column(String)

    __table_args__ = (
        CheckConstraint("direction IN ('CALL', 'PUT')"),
        CheckConstraint("result IN ('WIN', 'LOSS')"),
    )

# 4. LA LÍNEA MÁGICA (Aquí es donde va)
# Esto le dice a Supabase: "Si no ves estas tablas, créalas ahora mismo"
Base.metadata.create_all(engine)

# Configuración de la sesión para usar en app.py
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

print("✅ ¡Estructura de base de datos verificada/creada con éxito!")