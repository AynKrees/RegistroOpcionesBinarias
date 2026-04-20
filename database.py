import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

# 1. Definición de la Base
Base = declarative_base()

# 2. Configuración de Conexión (Blindada para Supabase)
try:
    # Leemos de st.secrets["database"]["URL"]
    DATABASE_URL = st.secrets["database"]["URL"]
    
    # Limpiamos parámetros extras que pueden dar error en la nube
    if "?" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.split("?")[0]
    
    # Forzamos el driver postgresql+psycopg2 para asegurar la conexión
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        
except Exception as e:
    # Si no hay secrets, usa SQLite para que la app no crashee al abrir
    DATABASE_URL = 'sqlite:///trading.db'

# 3. Creación del Motor
# Usamos pool_pre_ping para evitar que la conexión se caiga por inactividad
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

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
Base.metadata.create_all(engine)

# Configuración de sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)