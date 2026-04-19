import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

# 1. Definición de la Base
Base = declarative_base()

# 2. Configuración de Conexión (Híbrida y Segura)
try:
    # Intentamos forzar la lectura del link de los Secrets de Streamlit
    DATABASE_URL = st.secrets["supabase"]["URL"]
    
    # Fix de compatibilidad: SQLAlchemy requiere 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
except Exception as e:
    # Si falla por cualquier motivo, muestra el error visual en la app y usa SQLite local
    st.error("⚠️ Aviso: No se detectaron los Secrets de Supabase. Guardando en base de datos local (SQLite).")
    DATABASE_URL = 'sqlite:///trading.db'

# 3. Creación del Motor
engine = create_engine(DATABASE_URL)

# 4. Modelos de Tablas
class Strategy(Base):
    __tablename__ = 'strategies'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

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

# 5. Inicialización Automática
# Esto crea las tablas en Supabase si no existen
Base.metadata.create_all(engine)

# Configuración de sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)