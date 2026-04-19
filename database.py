import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

# 1. DEFINICIÓN DE LA BASE
Base = declarative_base()

# 2. CONFIGURACIÓN DE CONEXIÓN
if "supabase" in st.secrets:
    # Obtenemos el link de los Secrets
    raw_url = st.secrets["supabase"]["URL"]
    
    # REGLA DE ORO: Si hay un '#' en la clave, lo cambiamos por '%23'
    # Esto evita que el driver de Postgres se confunda.
    if "#" in raw_url:
        DATABASE_URL = raw_url.replace("#", "%23")
    else:
        DATABASE_URL = raw_url
        
    # Forzamos que use 'postgresql://' en lugar de 'postgres://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # Uso local en tu PC
    DATABASE_URL = 'sqlite:///trading.db'

# 3. CREACIÓN DEL MOTOR (ENGINE)
engine = create_engine(DATABASE_URL)

# 4. MODELOS DE TABLAS
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

# 5. INICIALIZACIÓN AUTOMÁTICA
# Esto crea las tablas en Supabase si no existen al arrancar la app
Base.metadata.create_all(engine)

# Configuración de sesión para app.py
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)