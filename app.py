import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Simulador Bonos TOYOSA", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main {background-color: #0f172a; color: #f8fafc;}
    h1, h2, h3 {color: #eb0a1e !important;}
    </style>
    """, unsafe_allow_html=True)

st.title("🚗 TOYOSA S.A. - Simulador de Emisión de Bonos")
st.markdown("Dashboard interactivo para evaluación de estructura de capital y proyecciones (2020 - 2034).")

# 2. BARRA LATERAL (SIMULADOR PARA EL PROFE)
st.sidebar.header("⚙️ Parámetros de la Emisión")
monto_bono = st.sidebar.number_input("Monto Nominal (Bs)", min_value=10000000, max_value=100000000, value=30000000, step=1000000)
tasa_bono = st.sidebar.slider("Tasa del Bono (%)", min_value=3.0, max_value=15.0, value=7.5, step=0.1) / 100
plazo_anios = st.sidebar.slider("Plazo (Años)", min_value=3, max_value=15, value=10, step=1)
tasa_bancaria = st.sidebar.slider("Tasa Bancaria Referencial (%)", min_value=5.0, max_value=18.0, value=10.5, step=0.1) / 100
tasa_iue = 0.25 # Impuesto a las Utilidades (Bolivia)

# 3. DATOS FINANCIEROS (REEMPLAZAR CON LOS DATOS DE TUS FOTOS)
# Creamos el rango de años
anios = list(range(2020, 2035))

# --- AQUÍ PONES TUS DATOS REALES DE LAS IMÁGENES ---
# Como ejemplo, pongo una progresión lineal, reemplaza estas listas con tus filas de Excel
ventas_historicas = [1200, 1100, 1300, 1450, 1600] # 2020-2024 (en millones)
ventas_proyectadas = [1750 + (i*150) for i in range(10)] # 2025-2034 (en millones)
ventas_totales = ventas_historicas + ventas_proyectadas

margen_ebitda = [0.12]*5 + [0.13, 0.135, 0.14, 0.14, 0.145, 0.15, 0.15, 0.15, 0.15, 0.15]
ratio_liquidez = [1.1, 1.2, 1.3, 1.25, 1.4] + [1.5 + (i*0.05) for i in range(10)]

df_finanzas = pd.DataFrame({
    'Año': anios,
    'Ventas (MM Bs)': ventas_totales,
    'Margen EBITDA (%)': [m * 100 for m in margen_ebitda],
    'Liquidez Corriente': ratio_liquidez
})

# 4. CÁLCULO DE AMORTIZACIÓN DEL BONO (MÉTODO FRANCÉS / CUOTA FIJA)
cuota_anual = (monto_bono * tasa_bono) / (1 - (1 + tasa_bono)**(-plazo_anios))
saldo = monto_bono
plan_pagos = []

for año in range(1, plazo_anios + 1):
    interes = saldo * tasa_bono
    capital = cuota_anual - interes
    saldo -= capital
    plan_pagos.append([año, monto_bono if año==1 else saldo+capital, cuota_anual, interes, capital, abs(saldo)])

df_amortizacion = pd.DataFrame(plan_pagos, columns=['Año', 'Saldo Inicial', 'Cuota', 'Interés', 'Amortización Capital', 'Saldo Final']).round(2)

# 5. PANTALLA PRINCIPAL - SECCIÓN 1: IMPACTO FINANCIERO (WACC)
st.header("1. Beneficio del Escudo Fiscal (IUE)")
col1, col2, col3 = st.columns(3)
tasa_efectiva_bono = tasa_bono * (1 - tasa_iue)

col1.metric("Costo Deuda Bancaria", f"{tasa_bancaria*100:.2f}%")
col2.metric("Costo Nominal Bono", f"{tasa_bono*100:.2f}%")
col3.metric("Costo Efectivo Bono (con Escudo)", f"{tasa_efectiva_bono*100:.2f}%", delta=f"-{(tasa_bancaria - tasa_efectiva_bono)*100:.2f}% vs Banco")

# 6. GRÁFICOS INTERACTIVOS
st.header("2. Proyecciones Financieras")
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    # Gráfico de Ventas
    fig_ventas = px.bar(df_finanzas, x='Año', y='Ventas (MM Bs)', title='Evolución y Proyección de Ingresos',
                        color_discrete_sequence=['#eb0a1e'])
    # Añadir línea que divide lo histórico de lo proyectado
    fig_ventas.add_vline(x=2024.5, line_width=2, line_dash="dash", line_color="white")
    fig_ventas.add_annotation(x=2022, y=max(ventas_totales), text="Histórico", showarrow=False, font=dict(color="white"))
    fig_ventas.add_annotation(x=2030, y=max(ventas_totales), text="Proyectado", showarrow=False, font=dict(color="white"))
    fig_ventas.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig_ventas, use_container_width=True)

with col_graf2:
    # Gráfico de Liquidez vs EBITDA
    fig_ratios = go.Figure()
    fig_ratios.add_trace(go.Scatter(x=df_finanzas['Año'], y=df_finanzas['Liquidez Corriente'], mode='lines+markers', name='Liquidez Corriente', line=dict(color='#38bdf8', width=3)))
    fig_ratios.add_trace(go.Scatter(x=df_finanzas['Año'], y=df_finanzas['Margen EBITDA (%)'], mode='lines+markers', name='Margen EBITDA (%)', yaxis='y2', line=dict(color='#a3e635', width=3)))
    
    fig_ratios.update_layout(
        title='Salud Financiera: Liquidez vs Rentabilidad',
        yaxis=dict(title='Liquidez (Veces)'),
        yaxis2=dict(title='EBITDA (%)', overlaying='y', side='right'),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white',
        legend=dict(yanchor="top", y=1.1, xanchor="left", x=0)
    )
    st.plotly_chart(fig_ratios, use_container_width=True)

# 7. TABLA Y GRÁFICO DE AMORTIZACIÓN
st.header("3. Estructura de la Deuda y Servicio")
col_amort1, col_amort2 = st.columns([1, 1.5])

with col_amort1:
    st.subheader("Cuadro de Amortización (Bs)")
    st.dataframe(df_amortizacion.style.format("{:,.2f}"))

with col_amort2:
    fig_amort = px.bar(df_amortizacion, x='Año', y=['Interés', 'Amortización Capital'], 
                       title='Servicio de la Deuda (Capital + Intereses)',
                       labels={'value': 'Monto (Bs)', 'variable': 'Componente'},
                       color_discrete_map={'Interés': '#eb0a1e', 'Amortización Capital': '#475569'})
    fig_amort.update_layout(barmode='stack', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
    st.plotly_chart(fig_amort, use_container_width=True)