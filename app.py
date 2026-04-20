import streamlit as st
import pandas as pd
# Importamos la configuración lista desde database.py
from database import Trade, Strategy, engine, SessionLocal
import datetime
import os

# Usamos la sesión que ya viene configurada
session = SessionLocal()

# Creamos la carpeta local si no existe para las capturas temporales
if not os.path.exists("screenshots"):
    os.makedirs("screenshots")

st.set_page_config(page_title="Trading Journal Pro", layout="wide")

st.title("📊 Trading Olymptrade")
st.markdown("---")

# --- LÓGICA DE DATOS ---
all_trades = session.query(Trade).all()
CAPITAL_INICIAL = 51.75
total_p_l = sum([t.profit_amount for t in all_trades]) if all_trades else 0

# --- BARRA LATERAL ---
st.sidebar.header("💰 Estado de la Cuenta")
st.sidebar.metric("Balance Actual", f"${round(CAPITAL_INICIAL + total_p_l, 2)}", f"{round(total_p_l, 2)} USD")

st.sidebar.markdown("---")
st.sidebar.header("🗑️ Borrar por ID")
id_borrar = st.sidebar.number_input("ID a eliminar", min_value=1, step=1)

if st.sidebar.button("Eliminar"):
    trade_a_borrar = session.query(Trade).filter_by(id=id_borrar).first()
    if trade_a_borrar:
        # Borrar archivo físico si existe localmente
        if trade_a_borrar.screenshot_path and os.path.exists(trade_a_borrar.screenshot_path):
            os.remove(trade_a_borrar.screenshot_path)
        session.delete(trade_a_borrar)
        session.commit()
        st.rerun()

# --- FORMULARIO DE REGISTRO ---
st.subheader("📝 Registro de Operación")
with st.form("registro_trade", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fecha = st.date_input("Fecha del Trade", datetime.date.today())
        st.write("Selecciona la Hora (24h):")
        sub_col_h, sub_col_m = st.columns(2)
        with sub_col_h:
            hora_sel = st.number_input("HH", min_value=0, max_value=23, value=datetime.datetime.now().hour, step=1)
        with sub_col_m:
            minuto_sel = st.number_input("MM", min_value=0, max_value=59, value=datetime.datetime.now().minute, step=1)
            
        asset = st.text_input("Activo (Ej: EURUSD)")
        strategy = st.text_input("Estrategia")

    with col2:
        direction = st.selectbox("Dirección", ["CALL", "PUT"])
        stake = st.number_input("Inversión ($)", min_value=1.0, value=5.0)
        payout = st.slider("Payout %", 70, 100, 85)
        result = st.radio("Resultado", ["WIN", "LOSS"], horizontal=True)

    with col3:
        notes = st.text_area("Comentarios")
        uploaded_file = st.file_uploader("📸 Captura", type=['png', 'jpg', 'jpeg'])
    
    if st.form_submit_button("Guardar Operación"):
        hora_final = datetime.time(hour=hora_sel, minute=minuto_sel)
        fecha_final = datetime.datetime.combine(fecha, hora_final)
        
        profit = stake * (payout / 100) if result == "WIN" else -stake
        
        # Guardado local en la carpeta screenshots
        img_path = ""
        if uploaded_file:
            img_path = f"screenshots/trade_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with open(img_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        # Lógica de Estrategia: Buscar en Supabase o crear si no existe
        strat = session.query(Strategy).filter_by(name=strategy).first() or Strategy(name=strategy)
        if not strat.id:
            session.add(strat)
            session.flush() # Obtener el ID antes del commit final
        
        # Creación del objeto Trade para la tabla en Supabase
        nuevo = Trade(
            executed_at=fecha_final, 
            asset=asset, direction=direction, result=result,
            stake_amount=stake, payout_percent=payout,
            profit_amount=round(profit, 2), strategy_id=strat.id,
            notes=notes, screenshot_path=img_path 
        )
        
        # GUARDADO DEFINITIVO EN SUPABASE
        session.add(nuevo)
        session.commit()
        st.rerun()

# --- TABLA DE HISTORIAL ---
st.markdown("---")
st.subheader("📈 Historial de Operaciones")

if all_trades:
    # Leemos directamente de la base de datos de Supabase
    df = pd.read_sql("SELECT * FROM trades", engine)
    df['executed_at'] = pd.to_datetime(df['executed_at'])
    df['Fecha'] = df['executed_at'].dt.strftime('%Y-%m-%d')
    df['Hora'] = df['executed_at'].dt.strftime('%H:%M')
    
    # Marcamos si tiene captura en el servidor local
    df['Captura'] = df['screenshot_path'].apply(lambda x: "✅ Sí" if x and os.path.exists(x) else "❌ No")
    
    columnas_finales = {
        "id": "ID", "Fecha": "Fecha", "Hora": "Hora", "asset": "Activo",
        "direction": "Tipo", "result": "Resultado", "stake_amount": "Inversión ($)",
        "profit_amount": "Profit ($)", "Captura": "Captura"
    }
    
    df_mostrar = df[list(columnas_finales.keys())].rename(columns=columnas_finales)
    
    def color_resultado(val):
        color = '#2ecc71' if val == "WIN" else '#e74c3c'
        return f'background-color: {color}; color: white; font-weight: bold'

    st.dataframe(df_mostrar.sort_values(by="ID", ascending=False).style.map(color_resultado, subset=['Resultado']), hide_index=True, use_container_width=True)

    # --- VISOR DE CAPTURAS MANTENIDO ---
    st.markdown("---")
    st.subheader("🖼️ Visor de Capturas")
    
    if 'mostrar_img' not in st.session_state:
        st.session_state.mostrar_img = False
    if 'id_actual' not in st.session_state:
        st.session_state.id_actual = None

    col_visor1, col_visor2 = st.columns([1, 3])
    
    with col_visor1:
        visor_id = st.number_input("ID del Trade a visualizar", min_value=1, step=1)
        c1, c2 = st.columns(2)
        if c1.button("Mostrar"):
            st.session_state.mostrar_img = True
            st.session_state.id_actual = visor_id
        if c2.button("Cerrar"):
            st.session_state.mostrar_img = False
        
        if st.session_state.mostrar_img:
            # Consultamos la nota del trade específico en Supabase
            t_data = session.query(Trade).filter_by(id=st.session_state.id_actual).first()
            if t_data and t_data.notes:
                st.info(f"Notas: {t_data.notes}")

    with col_visor2:
        if st.session_state.mostrar_img:
            t_img = session.query(Trade).filter_by(id=st.session_state.id_actual).first()
            if t_img and t_img.screenshot_path and os.path.exists(t_img.screenshot_path):
                st.image(t_img.screenshot_path, caption=f"Trade #{t_img.id}")
            else:
                st.warning("No hay imagen disponible localmente para este ID.")

else: 
    st.info("No hay operaciones registradas aún en Supabase.")

session.close()