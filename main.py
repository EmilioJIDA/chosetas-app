import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="JD Las Chosetas", page_icon="🚜", layout="centered")

# --- 2. BASE DE DATOS ROBUSTA ---
# Creamos la conexión y la tabla si no existe
conn = sqlite3.connect('chosetas_datos.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS registros
             (fecha TEXT, trabajador TEXT, cultivo TEXT, labor TEXT, plaga TEXT, producto TEXT, cantidad REAL, notas TEXT)''')
conn.commit()

# --- 3. CEREBRO DE LA APP: DICCIONARIO DE PLAGAS Y TRATAMIENTOS ---
# Estructura: Cultivo -> { Plaga: Tratamiento }
# IMPORTANTE: "Ninguna" debe ser siempre la primera opción.
datos_tecnicos = {
    "Naranjos": {
        "Ninguna": "",
        "Mosca de la fruta": "🧪 TRATAMIENTO NARANJOS: Deltametrina (decis), Lambda Cihalotrin o Trampeo masivo.",
        "Piojo Rojo": "🧪 TRATAMIENTO NARANJOS: Spirotetramat (Movento), Piriproxifen o Aceite de parafina.",
        "Cotonet": "🧪 TRATAMIENTO NARANJOS: Acetamiprid o suelta de Cryptolaemus (biológico).",
        "Minador": "🧪 TRATAMIENTO NARANJOS: Abamectina (si hay brotación tierna)."
    },
    "Aguacates": {
        "Ninguna": "",
        "Araña cristalina": "🧪 TRATAMIENTO AGUACATES: Abamectina (Vertimec) o Aceite de parafina. Aumentar humedad.",
        "Phytophthora": "🧪 TRATAMIENTO AGUACATES: Fosetil-Aluminio (vía riego o foliar) o Pintado del tronco con Cobre.",
        "Trips": "🧪 TRATAMIENTO AGUACATES: Spinosad o Azadiractina (Aceite de Neem).",
        "Ácaro de las agallas": "🧪 TRATAMIENTO AGUACATES: Azufre mojable (si la temperatura lo permite)."
    },
    "Cafetos": {
        "Ninguna": "",
        "Roya": "🧪 TRATAMIENTO CAFETOS: Oxicloruro de Cobre (preventivo) o Tebuconazol (curativo).",
        "Broca del café": "🧪 TRATAMIENTO CAFETOS: Ciantraniliprol o hongo Beauveria bassiana.",
        "Minador de la hoja": "🧪 TRATAMIENTO CAFETOS: Imidacloprid (revisar autorización) o trampas cromáticas."
    }
}

# --- 4. INTERFAZ DE USUARIO ---
st.title("🚜 JD Las Chosetas")
st.markdown("---")

menu = st.sidebar.radio("Menú Principal", ["📝 Nuevo Registro", "📊 Ver Historial"])

if menu == "📝 Nuevo Registro":
    st.subheader("Registrar Labor en Campo")
    
    with st.form("formulario_campo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            fecha = st.date_input("Fecha", datetime.now())
            trabajador = st.selectbox("Trabajador", ["Propietario", "Trabajador 1", "Trabajador 2"])
            
            # --- PASO CLAVE 1: SELECCIONAR CULTIVO ---
            lista_cultivos = list(datos_tecnicos.keys())
            cultivo_seleccionado = st.selectbox("1. Selecciona el Cultivo", lista_cultivos)
        
        with col2:
            labor = st.selectbox("Labor Realizada", ["Monitoreo de Plagas", "Tratamiento Fito", "Riego", "Abonado", "Poda", "Cosecha"])
            
            # --- PASO CLAVE 2: SELECCIONAR PLAGA (DINÁMICO) ---
            # Aquí obligamos a la app a leer SOLO las plagas del cultivo seleccionado arriba
            plagas_disponibles = list(datos_tecnicos[cultivo_seleccionado].keys())
            plaga_detectada = st.selectbox("2. Plaga Detectada (Opcional)", plagas_disponibles)
            
            producto = st.text_input("Producto Utilizado / Lote")

        # --- VISUALIZACIÓN DE ALERTAS Y TRATAMIENTOS ---
        # Solo mostramos el mensaje si el usuario NO ha elegido "Ninguna"
        if plaga_detectada != "Ninguna":
            recomendacion = datos_tecnicos[cultivo_seleccionado][plaga_detectada]
            st.info(f"⚠️ **ALERTA DETECTADA EN {cultivo_seleccionado.upper()}**\n\n{recomendacion}")
            st.caption("Nota: Consulte siempre el Registro Oficial de Fitosanitarios (MAPA) antes de aplicar.")

        # Resto del formulario
        cantidad = st.number_input("Cantidad (L / Kg / Horas)", min_value=0.0)
        notas = st.text_area("Notas o ubicación (Sector)")
        
        # Botón de Guardado
        boton_guardar = st.form_submit_button("💾 GUARDAR DATOS")
        
        if boton_guardar:
            c.execute("INSERT INTO registros VALUES (?,?,?,?,?,?,?,?)", 
                      (fecha.strftime("%Y-%m-%d"), trabajador, cultivo_seleccionado, labor, plaga_detectada, producto, cantidad, notas))
            conn.commit()
            st.success(f"✅ Registro guardado: {labor} en {cultivo_seleccionado}.")

else:
    # --- VISTA DE HISTORIAL ---
    st.subheader("📊 Historial de Registros")
    df = pd.read_sql_query("SELECT * FROM registros ORDER BY fecha DESC", conn)
    
    if not df.empty:
        # Colorear filas con plagas para detección rápida
        def resaltar_plagas(row):
            if row.plaga != "Ninguna":
                return ['background-color: #ffcccc'] * len(row) # Rojo suave
            return [''] * len(row)
            
        st.dataframe(df.style.apply(resaltar_plagas, axis=1), use_container_width=True)
        
        # Botón de descarga
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Excel", csv, "chosetas_datos.csv", "text/csv")
    else:
        st.info("Aún no hay datos registrados.")

