import streamlit as st
import pandas as pd
# Importamos la configuración lista desde database.py
from database import Trade, Strategy, engine, SessionLocal
from supabase import create_client # <-- Nueva importación
import datetime
import os

# --- CONFIGURACIÓN SUPABASE STORAGE ---
# Usamos las credenciales de tus st.secrets
SUPABASE_URL = st.secrets["supabase"]["URL"]
SUPABASE_KEY = st.secrets["supabase"]["ANON_KEY"]
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Usamos la sesión que ya viene configurada
session = SessionLocal()

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
        # Nota: Aquí podrías agregar lógica para borrar del storage también si quieres
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
            hora_sel = st.number_input("HH", min_value=0, max_value=23, value=datetime.datetime.now().hour, step=1, help="Máximo 23")
        with sub_col_m:
            minuto_sel = st.number_input("MM", min_value=0, max_value=59, value=datetime.datetime.now().minute, step=1, help="Máximo 59")
            
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
        
        # --- NUEVA LÓGICA DE SUBIDA A SUPABASE ---
        img_url = ""
        if uploaded_file:
            # Creamos nombre único para evitar duplicados
            file_name = f"trade_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            file_bytes = uploaded_file.getvalue()
            
            # Subimos al bucket que creaste
            supabase_client.storage.from_("trading-captures").upload(
                path=file_name,
                file=file_bytes,
                file_options={"content-type": uploaded_file.type}
            )
            # Obtenemos la URL pública para guardarla en la base de datos
            img_url = supabase_client.storage.from_("trading-captures").get_public_url(file_name)
        
        strat = session.query(Strategy).filter_by(name=strategy).first() or Strategy(name=strategy)
        
        nuevo = Trade(
            executed_at=fecha_final, 
            asset=asset, direction=direction, result=result,
            stake_amount=stake, payout_percent=payout,
            profit_amount=round(profit, 2), strategy_id=strat.id,
            notes=notes, screenshot_path=img_url # Guardamos el LINK de internet
        )
        session.add(nuevo)
        session.commit()
        st.rerun()

# --- TABLA EN ESPAÑOL ---
st.markdown("---")
st.subheader("📈 Historial de Operaciones")

if all_trades:
    df = pd.read_sql("SELECT * FROM trades", engine)
    
    df['executed_at'] = pd.to_datetime(df['executed_at'])
    df['Fecha'] = df['executed_at'].dt.strftime('%Y-%m-%d')
    df['Hora'] = df['executed_at'].dt.strftime('%H:%M')
    
    df['Nota_Tabla'] = df['notes'].apply(lambda x: (x[:30] + '...') if x and len(x) > 30 else x)
    # Cambiamos la lógica: si empieza con http, es que hay captura en la nube
    df['Captura'] = df['screenshot_path'].apply(lambda x: "✅ Sí" if x and x.startswith("http") else "❌ No")
    
    columnas_finales = {
        "id": "ID",
        "Fecha": "Fecha",
        "Hora": "Hora",
        "asset": "Activo",
        "direction": "Tipo",
        "result": "Resultado",
        "stake_amount": "Inversión ($)",
        "profit_amount": "Profit ($)",
        "Nota_Tabla": "Notas",
        "Captura": "Captura"
    }
    
    df_mostrar = df[list(columnas_finales.keys())].rename(columns=columnas_finales)
    
    def color_resultado(val):
        color = '#2ecc71' if val == "WIN" else '#e74c3c'
        return f'background-color: {color}; color: white; font-weight: bold'

    df_styled = (df_mostrar.sort_values(by="ID", ascending=False)
                  .style
                  .format({"Inversión ($)": "{:.2f}", "Profit ($)": "{:.2f}"})
                  .map(color_resultado, subset=['Resultado']))
                  
    st.dataframe(df_styled, width="stretch", hide_index=True)

    st.markdown(" ") 
    
    df_excel = df.copy()
    
    columnas_excel = {
        "id": "ID",
        "Fecha": "Fecha",
        "Hora": "Hora",
        "asset": "Activo",
        "direction": "Tipo",
        "result": "Resultado",
        "stake_amount": "Inversión ($)",
        "profit_amount": "Profit ($)",
        "notes": "Notas Completas",
        "screenshot_path": "URL de Captura"
    }
    
    df_final_excel = df_excel[list(columnas_excel.keys())].rename(columns=columnas_excel)
    csv_data = df_final_excel.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Descargar Historial para Auditoría (CSV)",
        data=csv_data,
        file_name=f"trading_audit_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("🖼️ Visor de Capturas")
    
    if 'mostrar_img' not in st.session_state:
        st.session_state.mostrar_img = False
    if 'id_actual' not in st.session_state:
        st.session_state.id_actual = None

    col_visor1, col_visor2 = st.columns([1, 3])
    
    with col_visor1:
        st.write("¿Quieres auditar un trade?")
        visor_id = st.number_input("ID del Trade a visualizar", min_value=1, step=1)
        
        col_btns1, col_btns2 = st.columns(2)
        with col_btns1:
            if st.button("Mostrar"):
                st.session_state.mostrar_img = True
                st.session_state
