

import streamlit as st
import math
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io

# --- 1. LÓGICA DE INGENIERÍA ---
def realizar_calculos(p_kw, fp_act, fp_obj, multa, inversion, costo_kwh):
    phi1, phi2 = math.acos(fp_act), math.acos(fp_obj)
    qc_kvar = p_kw * (math.tan(phi1) - math.tan(phi2))
    
    # Ahorro por reducción de pérdidas Joule (est. 3% pérdidas base)
    reduccion_perdidas_pct = (1 - (fp_act / fp_obj)**2)
    ahorro_energia_kwh = (p_kw * 720 * 0.03) * reduccion_perdidas_pct
    ahorro_eficiencia_dinero = ahorro_energia_kwh * costo_kwh
    
    ahorro_total_mes = multa + ahorro_eficiencia_dinero
    roi_meses = inversion / ahorro_total_mes if ahorro_total_mes > 0 else 0
    
    return {
        "qc": qc_kvar,
        "ahorro_mes": ahorro_total_mes,
        "ahorro_anual": ahorro_total_mes * 12,
        "roi": roi_meses
    }

# --- 2. GENERADOR DE PDF PROFESIONAL ---
def generar_pdf_buffer(datos, firma_nombre):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Encabezado Corporativo
    c.setFillColor(colors.darkblue)
    c.rect(0, height-100, width, 100, fill=True, stroke=False)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height-60, "Dynamis Renewables")
    c.setFont("Helvetica", 12)
    c.drawString(50, height-80, "Soluciones de Eficiencia Energética y Potencia")
    
    # Cuerpo del Reporte
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    y = height - 150
    c.drawString(50, y, "REPORTE TÉCNICO DE COMPENSACIÓN")
    
    c.setFont("Helvetica", 12)
    y -= 30
    lineas = [
        f"Potencia Activa Analizada: {datos['p_kw']} kW",
        f"Factor de Potencia (Actual -> Objetivo): {datos['fp_act']} -> {datos['fp_obj']}",
        f"Capacidad del Banco Requerida: {datos['qc']:.2f} kVAR",
        f"Ahorro Mensual Proyectado: ${datos['ahorro_mes']:.2f}",
        f"Ahorro Anual Estimado: ${datos['ahorro_anual']:.2f}",
        f"Retorno de Inversión (ROI): {datos['roi']:.1f} meses"
    ]
    for linea in lineas:
        y -= 25
        c.drawString(70, y, f"• {linea}")

    # Sección de Firma
    y -= 100
    c.setStrokeColor(colors.black)
    c.line(50, y, 250, y) # Línea de firma
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, firma_nombre)
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, y-15, "Consultor Energético")
    c.drawString(50, y-30, "Dynamis Renewables")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- 3. INTERFAZ DE USUARIO ---
def main():
    st.set_page_config(page_title="Dynamis Renewables | FP Calc", page_icon="⚡")
    st.title("⚡ Optimizador de Potencia")
    st.write("**Empresa:** Dynamis Renewables")

    with st.form("datos_entrada"):
        st.subheader("Configuración Técnica")
        col1, col2 = st.columns(2)
        with col1:
            p_kw = st.number_input("Demanda Máxima (kW)", value=100.0)
            fp_act = st.slider("Factor de Potencia Actual", 0.50, 0.95, 0.80)
            fp_obj = st.slider("Factor de Potencia Objetivo", 0.90, 1.0, 0.95)
        with col2:
            multa = st.number_input("Multa Mensual ($)", value=500.0)
            costo_kwh = st.number_input("Costo kWh ($)", value=0.15)
            inversion = st.number_input("Inversión Banco ($)", value=3000.0)
        
        st.divider()
        firma = st.text_input("Firma del Consultor (Nombre)", value="Ing. Juan Pérez")
        
        submitted = st.form_submit_button("Calcular y Generar Reporte")

    if submitted:
        res = realizar_calculos(p_kw, fp_act, fp_obj, multa, inversion, costo_kwh)
        
        # Mostrar métricas en pantalla
        c1, c2, c3 = st.columns(3)
        c1.metric("Banco kVAR", f"{res['qc']:.1f}")
        c2.metric("Ahorro Anual", f"${res['ahorro_anual']:.2f}")
        c3.metric("ROI", f"{res['roi']:.1f} Meses")

        # Gráfico rápido
        fig, ax = plt.subplots(figsize=(8, 2))
        ax.barh(['Sin Proyecto', 'Con Dynamis'], [multa, 0], color=['#ff4b4b', '#00cf8d'])
        st.pyplot(fig)

        # Generar PDF
        datos_pdf = {
            'p_kw': p_kw, 'fp_act': fp_act, 'fp_obj': fp_obj, 
            'qc': res['qc'], 'ahorro_mes': res['ahorro_mes'], 
            'ahorro_anual': res['ahorro_anual'], 'roi': res['roi']
        }
        pdf_file = generar_pdf_buffer(datos_pdf, firma)

        st.download_button(
            label="📥 Descargar Reporte Formal PDF",
            data=pdf_file,
            file_name=f"Propuesta_Dynamis_{firma.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()