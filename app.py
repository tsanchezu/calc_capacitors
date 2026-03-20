import streamlit as st
import math
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io

# --- 1. LÓGICA DE INGENIERÍA ---
def realizar_calculos(p_kw, fp_act, fp_obj, multa, inversion, costo_kwh, v, f=60):
    phi1, phi2 = math.acos(fp_act), math.acos(fp_obj)
    q_act = p_kw * math.tan(phi1)
    q_obj = p_kw * math.tan(phi2)
    qc_res = q_act - q_obj
    
    # Cálculo de potencias aparentes y carga liberada
    s_act = p_kw / fp_act
    s_obj = p_kw / fp_obj
    kva_lib = s_act - s_obj
    
    # Capacitancia y ahorros
    cap_uf = (qc_res * 10**9) / (2 * math.pi * f * (v**2))
    ahorro_mes = multa + (p_kw * 720 * 0.015 * costo_kwh)
    roi_val = inversion / ahorro_mes if ahorro_mes > 0 else 0
    
    return {
        "p_kw": p_kw, "fp_act": fp_act, "fp_obj": fp_obj,
        "q_act": q_act, "q_obj": q_obj, "qc": qc_res,
        "s_act": s_act, "s_obj": s_obj, "kva_liberados": kva_lib,
        "uf": cap_uf, "ahorro_mes": ahorro_mes, "roi": roi_val
    }

# --- 2. GENERADOR DE PDF (2 PÁGINAS) ---
def generar_pdf(datos, firma_nombre, fig_tri, fig_eco):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # PÁGINA 1: DATOS
    c.setFillColor(colors.darkblue)
    c.rect(0, height-100, width, 100, fill=True, stroke=False)
    try:
        logo = ImageReader('logo.png')
        c.drawImage(logo, 50, height-85, width=60, height=60, mask='auto')
    except: pass

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(130, height-60, "Dynamis Renewables")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    y = height - 150
    c.drawString(50, y, "DIAGNÓSTICO DE COMPENSACIÓN REACTIVA")
    
    c.setFont("Helvetica", 11)
    y -= 40
    tabla = [
        ["BANCO DE CAPACITORES", f"{datos['qc']:.2f} kVAR"],
        ["CAPACITANCIA", f"{datos['uf']:.1f} uF"],
        ["CARGA LIBERADA EN TRAFO", f"{datos['kva_liberados']:.1f} kVA"],
        ["AHORRO MENSUAL", f"${datos['ahorro_mes']:.2f}"],
        ["RETORNO DE INVERSIÓN", f"{datos['roi']:.1f} Meses"]
    ]
    for r in tabla:
        c.drawString(70, y, r[0]); c.drawRightString(width-100, y, r[1])
        c.line(70, y-4, width-100, y-4); y -= 25

    c.drawString(50, y-100, "__________________________")
    c.drawString(50, y-115, firma_nombre)
    
    c.showPage() # SALTO DE PÁGINA

    # PÁGINA 2: GRÁFICAS
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-50, "ANÁLISIS VISUAL")
    
    # Insertar Triángulo
    img_tri = io.BytesIO()
    fig_tri.savefig(img_tri, format='png', dpi=200)
    img_tri.seek(0)
    c.drawImage(ImageReader(img_tri), 50, height-400, width=500, preserveAspectRatio=True)
    
    # Insertar Ahorro
    img_eco = io.BytesIO()
    fig_eco.savefig(img_eco, format='png', dpi=200)
    img_eco.seek(0)
    c.drawImage(ImageReader(img_eco), 50, height-700, width=500, preserveAspectRatio=True)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- 3. INTERFAZ ---
def main():
    st.set_page_config(page_title="Dynamis Pro")
    st.title("⚡ Dynamis: Optimizador de Potencia")

    with st.form("calc_form"):
        col1, col2 = st.columns(2)
        p_kw = col1.number_input("Demanda (kW)", value=100.0)
        v = col1.selectbox("Voltaje (V)", [220, 440, 480], index=1)
        fp_act = col2.slider("FP Actual", 0.50, 0.95, 0.80)
        fp_obj = col2.slider("FP Objetivo", 0.90, 1.0, 0.97)
        multa = col1.number_input("Multa Mensual ($)", value=500.0)
        inv = col1.number_input("Inversión Banco ($)", value=2500.0)
        firma = st.text_input("Nombre del Consultor", value="Ing. Manuel Estrada")
        btn = st.form_submit_button("EJECUTAR ANÁLISIS")

    if btn:
        res = realizar_calculos(p_kw, fp_act, fp_obj, multa, inv, 0.18, v)
        
        # FIGURA 1: TRIÁNGULO MEJORADO
        fig_t, ax = plt.subplots(figsize=(7, 5))
        ax.quiver(0, 0, p_kw, 0, angles='xy', scale_units='xy', scale=1, color='#2c3e50', label='P (Activa)')
        ax.quiver(p_kw, 0, 0, res['q_act'], angles='xy', scale_units='xy', scale=1, color='#c0392b', label='Q1 (Actual)')
        ax.quiver(p_kw, 0, 0, res['q_obj'], angles='xy', scale_units='xy', scale=1, color='#27ae60', label='Q2 (Objetivo)')
        ax.set_xlim(-10, p_kw * 1.15)
        ax.set_ylim(-10, res['q_act'] * 1.2)
        ax.legend()
        st.pyplot(fig_t)

        # FIGURA 2: AHORRO
        fig_e, ax2 = plt.subplots(figsize=(7, 2))
        ax2.barh(['Multa Actual', 'Multa con Dynamis'], [multa, 0], color=['#c0392b', '#27ae60'])
        st.pyplot(fig_e)

        # GENERAR PDF
        pdf = generar_pdf(res, firma, fig_t, fig_e)
        st.download_button("📥 Descargar Reporte de 2 Páginas", data=pdf, file_name="Propuesta_Dynamis.pdf")

if __name__ == "__main__":
    main()
