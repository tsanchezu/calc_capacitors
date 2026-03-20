import streamlit as st
import math
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io

# --- 1. LÓGICA DE INGENIERÍA CORREGIDA ---
def realizar_calculos_avanzados(p_kw, fp_act, fp_obj, multa, inversion, costo_kwh, v=440, f=60):
    # Ángulos de fase
    phi1, phi2 = math.acos(fp_act), math.acos(fp_obj)
    
    # Potencias Reactivas (kVAR)
    q_act = p_kw * math.tan(phi1)
    q_obj = p_kw * math.tan(phi2)
    qc_kvar = q_act - q_obj
    
    # Potencias Aparentes (kVA)
    s_act = p_kw / fp_act
    s_obj = p_kw / fp_obj
    kva_liberados = s_act - s_obj
    
    # Capacitancia (µF)
    cap_uf = (qc_kvar * 10**9) / (2 * math.pi * f * (v**2))
    
    # Análisis Financiero
    ahorro_eficiencia = (p_kw * 720 * 0.015 * costo_kwh)
    ahorro_total_mes = multa + ahorro_eficiencia
    roi_meses = inversion / ahorro_total_mes if ahorro_total_mes > 0 else 0
    
    return {
        "q_act": q_act, "q_obj": q_obj, "qc": qc_kvar,
        "s_act": s_act, "s_obj": s_obj, "kva_liberados": kva_liberados,
        "uf": cap_uf, "ahorro_mes": ahorro_total_mes, "roi": roi_meses
    }

# --- 2. GENERADOR DE PDF ---
def generar_pdf(datos, firma_nombre):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.setFillColor(colors.darkblue)
    c.rect(0, height-100, width, 100, fill=True, stroke=False)
    
    try:
        logo = ImageReader('logo.png')
        c.drawImage(logo, 50, height-85, width=65, height=65, mask='auto', preserveAspectRatio=True)
        text_x = 135
    except:
        text_x = 50

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(text_x, height-55, "Dynamis Renewables")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(text_x, height-75, "ENERGY EFFICIENCY & POWER CONSULTING")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    y = height - 150
    c.drawString(50, y, "REPORTE TÉCNICO DE COMPENSACIÓN REACTIVA")
    
    c.setFont("Helvetica", 11)
    y -= 40
    tabla_datos = [
        ["PARÁMETRO ELÉCTRICO", "VALOR"],
        ["Demanda Activa (P)", f"{datos['p_kw']:.1f} kW"],
        ["Factor de Potencia", f"{datos['fp_act']} --> {datos['fp_obj']}"],
        ["Reactiva Inicial (Q1)", f"{datos['q_act']:.1f} kVAR"],
        ["Reactiva Final (Q2)", f"{datos['q_obj']:.1f} kVAR"],
        ["BANCO REQUERIDO (Qc)", f"{datos['qc']:.2f} kVAR"],
        ["CAPACITANCIA TOTAL", f"{datos['uf']:.1f} µF"],
        ["CARGA LIBERADA", f"{datos['kva_liberados']:.1f} kVA"],
        ["AHORRO MENSUAL ESTIMADO", f"${datos['ahorro_mes']:.2f}"],
        ["RETORNO DE INVERSIÓN", f"{datos['roi']:.1f} Meses"]
    ]
    
    for fila in tabla_datos:
        c.drawString(70, y, fila[0])
        c.drawRightString(width-100, y, fila[1])
        c.setStrokeColor(colors.lightgrey)
        c.line(70, y-4, width-100, y-4)
        y -= 25
    
    y -= 50
    c.setStrokeColor(colors.black)
    c.line(50, y, 230, y)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y-18, firma_nombre)
    c.drawString(50, y-32, "Consultor Especialista - Dynamis Renewables")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- 3. INTERFAZ ---
def main():
    st.set_page_config(page_title="Dynamis Pro", page_icon="⚡", layout="wide")
    st.title("⚡ Dynamis Renewables: Optimizador de Potencia")

    with st.form("datos_entrada"):
        col1, col2, col3 = st.columns(3)
        with col1:
            p_kw = st.number_input("Demanda Máxima (kW)", min_value=1.0, value=150.0)
            v_input = st.selectbox("Voltaje (V)", [220, 440, 480], index=1)
        with col2:
            fp_act = st.slider("FP Actual", 0.40, 0.95, 0.75)
            fp_obj = st.slider("FP Objetivo", 0.90, 1.0, 0.97)
        with col3:
            multa = st.number_input("Multa ($)", value=800.0)
            costo_kwh = st.number_input("Costo kWh ($)", value=0.18)
            inversion = st.number_input("Inversión ($)", value=4500.0)
        
        firma_usuario = st.text_input("Firma del Consultor", value="Ing. Manuel Estrada")
        submitted = st.form_submit_button("CALCULAR")

    if submitted:
        res = realizar_calculos_avanzados(p_kw, fp_act, fp_obj, multa, inversion, costo_kwh, v_input)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Banco", f"{res['qc']:.1f} kVAR")
        m2.metric("Capacitancia", f"{res['uf']:.1f} µF")
        m3.metric("Ahorro", f"${res['ahorro_mes']:,.2f}")
        m4.metric("ROI", f"{res['roi']:.1f} Meses")

        # Gráfica
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.quiver(0, 0, p_kw, 0, angles='xy', scale_units='xy', scale=1, color='#34495e', label='P')
        ax.quiver(p_kw, 0, 0, res['q_act'], angles='xy', scale_units='xy', scale=1, color='#e74c3c', label='Q1')
        ax.quiver(p_kw, 0, 0, res['q_obj'], angles='xy', scale_units='xy', scale=1, color='#2ecc71', label='Q2')
        ax.set_xlim(0, p_kw * 1.1); ax.set_ylim(0, res['q_act'] * 1.1)
        ax.legend(); st.pyplot(fig)

        # PDF
        datos_pdf = {**res, 'p_kw': p_kw, 'fp_act': fp_act, 'fp_obj': fp_obj}
        pdf_file = generar_pdf(datos_pdf, firma_usuario)

        st.download_button(
            label="📥 Descargar Reporte PDF",
            data=pdf_file,
            file_name="Propuesta_Dynamis.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
