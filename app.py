import streamlit as st
import math
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import io

# --- 1. LÓGICA DE INGENIERÍA ---
def realizar_calculos(p_kw, fp_act, fp_obj, multa, inversion, costo_kwh, v, f):
    phi1, phi2 = math.acos(fp_act), math.acos(fp_obj)
    q_act = p_kw * math.tan(phi1)
    q_obj = p_kw * math.tan(phi2)
    qc_res = q_act - q_obj
    s_act, s_obj = p_kw / fp_act, p_kw / fp_obj
    kva_lib = s_act - s_obj
    cap_uf = (qc_res * 10**9) / (2 * math.pi * f * (v**2))
    # Ahorro Joule estimado 1.5%
    ahorro_mes = multa + (p_kw * 720 * 0.015 * costo_kwh)
    roi_val = inversion / ahorro_mes if ahorro_mes > 0 else 0
    
    return {
        "q_act": q_act, "q_obj": q_obj, "qc": qc_res,
        "s_act": s_act, "s_obj": s_obj, "kva_liberados": kva_lib,
        "uf": cap_uf, "ahorro_mes": ahorro_mes, "roi": roi_val
    }

# --- 2. GENERADOR DE PDF (2 PÁGINAS) ---
def generar_pdf(datos, firma_nombre, fig_triangulo, fig_ahorro):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # --- PÁGINA 1: RESUMEN ---
    c.setFillColor(colors.darkblue)
    c.rect(0, height-100, width, 100, fill=True, stroke=False)
    
    try:
        logo = ImageReader('logo.png')
        c.drawImage(logo, 50, height-85, width=65, height=65, mask='auto', preserveAspectRatio=True)
        text_x = 135
    except:
        text_x = 50

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(text_x, height-55, "Dynamis Renewables")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(text_x, height-75, "SOLUCIONES DE ALTA INGENIERÍA EN ENERGÍA")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    y = height - 150
    c.drawString(50, y, "REPORTE DE DIAGNÓSTICO ENERGÉTICO")
    
    c.setFont("Helvetica", 11)
    y -= 40
    tabla = [
        ["DEMANDA MÁXIMA REGISTRADA", f"{datos['p_kw']} kW"],
        ["FACTOR DE POTENCIA ACTUAL", f"{datos['fp_act']}"],
        ["FACTOR DE POTENCIA OBJETIVO", f"{datos['fp_obj']}"],
        ["CAPACIDAD DEL BANCO SUGERIDO", f"{datos['qc']:.2f} kVAR"],
        ["CAPACITANCIA REQUERIDA", f"{datos['uf']:.1f} µF"],
        ["LIBERACIÓN DE CAPACIDAD (kVA)", f"{datos['kva_liberados']:.1f} kVA"],
        ["AHORRO MENSUAL ESTIMADO", f"${datos['ahorro_mes']:.2f}"],
        ["TIEMPO DE RECUPERACIÓN (ROI)", f"{datos['roi']:.1f} Meses"]
    ]
    for item in tabla:
        c.drawString(70, y, item[0]); c.drawRightString(width-100, y, item[1])
        c.setStrokeColor(colors.lightgrey); c.line(70, y-4, width-100, y-4); y -= 25

    y -= 60
    c.setStrokeColor(colors.black); c.line(50, y, 220, y)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y-18, firma_nombre)
    c.setFont("Helvetica", 10)
    c.drawString(50, y-32, "Consultor Especialista - Dynamis Renewables")

    c.showPage()

    # --- PÁGINA 2: GRÁFICAS ---
    c.setFillColor(colors.darkblue)
    c.rect(0, height-50, width, 50, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height-32, "EVIDENCIA GRÁFICA DE MEJORA")

    # Gráfica 1
    y = height - 350
    img_tri = io.BytesIO()
    fig_triangulo.savefig(img_tri, format='png', bbox_inches='tight', dpi=200)
    img_tri.seek(0)
    c.drawImage(ImageReader(img_tri), 50, y, width=500, height=280, preserveAspectRatio=True)
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y-20, "1. Optimización Vectorial del Triángulo de Potencias")

    # Gráfica 2
    y -= 320
    img_ahorro = io.BytesIO()
    fig_ahorro.savefig(img_ahorro, format='png', bbox_inches='tight', dpi=200)
    img_ahorro.seek(0)
    c.drawImage(ImageReader(img_ahorro), 50, y, width=500, height=250, preserveAspectRatio=True)
    c.drawString(50, y-20, "2. Impacto Financiero y Eliminación de Penalizaciones")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- 3. INTERFAZ ---
def main():
    st.set_page_config(page_title="Dynamis Pro", layout="wide")
    st.title("⚡ Dynamis Renewables: Optimizador")

    with st.form("main_form"):
        col1, col2 = st.columns(2)
        p_kw = col1.number_input("Demanda (kW)", value=100.0)
        v = col1.selectbox("Voltaje (V)", [220, 440, 480], index=1)
        fp_act = col2.slider("FP Actual", 0.40, 0.95, 0.75)
        fp_obj = col2.slider("FP Objetivo", 0.90, 1.0, 0.95)
        multa = col1.number_input("Multa ($)", value=500.0)
        costo_kwh = col2.number_input("Costo kWh ($)", value=0.18)
        inv = col1.number_input("Inversión ($)", value=3000.0)
        firma = st.text_input("Firma", value="Ing. Manuel Estrada")
        btn = st.form_submit_button("CALCULAR")

    if btn:
        # 1. Cálculos
        res = realizar_calculos(p_kw, fp_act, fp_obj, multa, inv, costo_kwh, v, 60)
        
        # 2. Pantalla Streamlit
        st.subheader("Simulación Finalizada")
        c1, c2, c3 = st.columns(3)
        c1.metric("Banco Sugerido", f"{res['qc']:.1f} kVAR")
        c2.metric("Ahorro Mensual", f"${res['ahorro_mes']:.2f}")
        c3.metric("ROI", f"{res['roi']:.1f} Meses")

        # 3. Generar Gráficas
        fig_tri, ax1 = plt.subplots(figsize=(8, 4))
        ax1.quiver(0, 0, p_kw, 0, angles='xy', scale_units='xy', scale=1, color='#34495e', label='P (kW)')
        ax1.quiver(p_kw, 0, 0, res['q_act'], angles='xy', scale_units='xy', scale=1, color='#e74c3c', label='Q1 (Actual)')
        ax1.quiver(p_kw, 0, 0, res['q_obj'], angles='xy', scale_units='xy', scale=1, color='#2ecc71', label='Q2 (Objetivo)')
        ax1.legend(); plt.grid(True, alpha=0.3)
        st.pyplot(fig_tri)
        
        fig_eco, ax2 = plt.subplots(figsize=(8, 3))
        ax2.barh(['Actual (Multas)', 'Con Dynamis'], [multa, 0], color=['#e74c3c', '#2ecc71'])
        st.pyplot(fig_eco)

        # 4. PDF
        datos_pdf = {**res, 'p_kw': p_kw, 'fp_act': fp_act, 'fp_obj': fp_obj}
        pdf = generar_pdf(datos_pdf, firma, fig_tri, fig_eco)
        
        st.download_button(
            label="📥 DESCARGAR REPORTE CORPORATIVO (2 PÁG)",
            data=pdf,
            file_name=f"Propuesta_Dynamis_{v}V.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
