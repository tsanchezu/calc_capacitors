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
    ahorro_mes = multa + (p_kw * 720 * 0.015 * costo_kwh)
    roi_val = inversion / ahorro_mes if ahorro_mes > 0 else 0
    
    return {
        "q_act": q_act, "q_obj": q_obj, "qc": qc_res,
        "s_act": s_act, "s_obj": s_obj, "kva_liberados": kva_lib,
        "uf": cap_uf, "ahorro_mes": ahorro_mes, "roi": roi_val
    }

# --- 2. GENERADOR DE PDF ---
def generar_pdf(datos, firma_nombre):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Encabezado
    c.setFillColor(colors.darkblue)
    c.rect(0, height-100, width, 100, fill=True, stroke=False)
    try:
        logo = ImageReader('logo.png')
        c.drawImage(logo, 50, height-85, width=65, height=65, mask='auto', preserveAspectRatio=True)
        tx = 135
    except: tx = 50

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(tx, height-55, "Dynamis Renewables")
    
    # Cuerpo - Aquí es donde daba el KeyError. Ahora usamos nombres seguros.
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    y = height - 150
    c.drawString(50, y, "REPORTE TÉCNICO DE COMPENSACIÓN")
    
    c.setFont("Helvetica", 11)
    y -= 40
    # CRÍTICO: Los nombres aquí coinciden con el diccionario del retorno de realizar_calculos
    tabla = [
        ["Demanda Activa", f"{datos['p_kw']} kW"],
        ["BANCO REQUERIDO (Qc)", f"{datos['qc']:.2f} kVAR"],
        ["CAPACITANCIA", f"{datos['uf']:.1f} uF"],
        ["CARGA LIBERADA", f"{datos['kva_liberados']:.1f} kVA"],
        ["AHORRO MENSUAL", f"${datos['ahorro_mes']:.2f}"],
        ["ROI ESTIMADO", f"{datos['roi']:.1f} Meses"]
    ]
    
    for fila in tabla:
        c.drawString(70, y, fila[0]); c.drawRightString(width-100, y, fila[1])
        c.line(70, y-4, width-100, y-4); y -= 25

    c.showPage(); c.save(); buffer.seek(0)
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
        # 1. Calculamos
        res = realizar_calculos(p_kw, fp_act, fp_obj, multa, inv, costo_kwh, v, 60)
        
        # 2. Mostramos en pantalla
        st.metric("Banco Necesario", f"{res['qc']:.1f} kVAR")
        
        # 3. Preparamos datos para PDF (AQUÍ ESTABA EL FALLO)
        # Agregamos manualmente p_kw al diccionario para que el PDF lo encuentre
        datos_completos = res 
        datos_completos['p_kw'] = p_kw 
        
        pdf = generar_pdf(datos_completos, firma)
        st.download_button("📥 Descargar PDF", data=pdf, file_name="Reporte_Dynamis.pdf")

if __name__ == "__main__":
    main()
