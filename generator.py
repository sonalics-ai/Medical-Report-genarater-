import spacy
from fpdf import FPDF
import os
from datetime import date

nlp = spacy.load("en_core_web_sm")

NORMAL_RANGES = {
    "bp_systolic":  {"min": 90,  "max": 120, "unit": "mmHg"},
    "bp_diastolic": {"min": 60,  "max": 80,  "unit": "mmHg"},
    "sugar":        {"min": 70,  "max": 140, "unit": "mg/dL"},
    "cholesterol":  {"min": 0,   "max": 200, "unit": "mg/dL"},
    "hemoglobin":   {"min": 12,  "max": 17,  "unit": "g/dL"},
    "pulse":        {"min": 60,  "max": 100, "unit": "bpm"},
}

TERM_SIMPLIFIER = {
    "Hypertension (High Blood Pressure)": "Your blood pressure is higher than normal",
    "Hypertension (Diastolic)": "The lower number of your blood pressure is too high",
    "Uncontrolled Diabetes / High Blood Sugar": "Your blood sugar level is very high and needs attention",
    "Hypercholesterolemia (High Cholesterol)": "There is too much fat in your blood",
    "Anemia (Low Hemoglobin)": "Your blood does not have enough iron and you may feel tired",
    "Monitor blood pressure daily": "Check your blood pressure every day at the same time",
    "Reduce salt intake and avoid stress": "Eat less salt in your food and try to stay calm and relaxed",
    "Consult a cardiologist": "Visit a heart specialist doctor as soon as possible",
    "Monitor blood sugar levels regularly": "Check your sugar levels every day using a glucometer",
    "Follow a strict low-sugar diet": "Avoid sweets, rice, bread and sugary drinks in your daily food",
    "HbA1c test recommended": "Get a special blood test that shows your average sugar for 3 months",
    "Avoid fried and fatty foods": "Do not eat oily or deep fried food items",
    "Lipid profile test recommended": "Get a blood test to check the fat levels in your body",
    "Iron-rich diet recommended": "Eat more spinach, beans, eggs and meat to increase your iron",
    "Complete Blood Count (CBC) test advised": "Get a full blood test to check all your blood cells",
    "ECG (Electrocardiogram) test recommended": "Get a heart test where wires are placed on your chest to check heart activity",
    "Cardiology consultation advised": "See a heart doctor for a detailed checkup",
    "Chest X-ray recommended": "Get an X-ray picture of your chest and lungs taken",
    "Pulmonology consultation advised": "See a lung specialist doctor",
    "Maintain a healthy diet and exercise regularly": "Eat healthy food and walk or exercise for 30 minutes every day",
    "Routine checkup after 3 months": "Visit your doctor again after 3 months for a follow up",
}

PRESCRIPTION_TEMPLATES = {
    "Hypertension (High Blood Pressure)": [
        {"medicine": "Tablet Amlodipine 5mg", "dosage": "Once daily in the morning", "duration": "1 month"},
        {"medicine": "Tablet Telmisartan 40mg", "dosage": "Once daily after breakfast", "duration": "1 month"},
    ],
    "Hypertension (Diastolic)": [
        {"medicine": "Tablet Metoprolol 25mg", "dosage": "Twice daily after meals", "duration": "1 month"},
    ],
    "Uncontrolled Diabetes / High Blood Sugar": [
        {"medicine": "Tablet Metformin 500mg", "dosage": "Twice daily after meals", "duration": "1 month"},
        {"medicine": "Tablet Glimepiride 1mg", "dosage": "Once daily before breakfast", "duration": "1 month"},
    ],
    "Hypercholesterolemia (High Cholesterol)": [
        {"medicine": "Tablet Atorvastatin 10mg", "dosage": "Once daily at night", "duration": "1 month"},
    ],
    "Anemia (Low Hemoglobin)": [
        {"medicine": "Tablet Ferrous Sulphate 200mg", "dosage": "Twice daily after meals", "duration": "1 month"},
        {"medicine": "Tablet Folic Acid 5mg", "dosage": "Once daily after breakfast", "duration": "1 month"},
    ],
}

def check_value(name, value):
    if name not in NORMAL_RANGES or value == "":
        return None
    r = NORMAL_RANGES[name]
    v = float(value)
    if v < r["min"]:
        return f"LOW ({v} {r['unit']}) - Normal: {r['min']}-{r['max']}"
    elif v > r["max"]:
        return f"HIGH ({v} {r['unit']}) - Normal: {r['min']}-{r['max']}"
    else:
        return f"NORMAL ({v} {r['unit']})"

def detect_risks(data):
    risks = []
    if data.get("bp_systolic") and float(data["bp_systolic"]) > 140:
        risks.append("Hypertension (High Blood Pressure)")
    if data.get("bp_diastolic") and float(data["bp_diastolic"]) > 90:
        risks.append("Hypertension (Diastolic)")
    if data.get("sugar") and float(data["sugar"]) > 180:
        risks.append("Uncontrolled Diabetes / High Blood Sugar")
    if data.get("cholesterol") and float(data["cholesterol"]) > 200:
        risks.append("Hypercholesterolemia (High Cholesterol)")
    if data.get("hemoglobin") and float(data["hemoglobin"]) < 12:
        risks.append("Anemia (Low Hemoglobin)")
    return risks

def get_recommendations(risks, symptoms):
    recommendations = []
    if "Hypertension" in " ".join(risks):
        recommendations.append("Monitor blood pressure daily")
        recommendations.append("Reduce salt intake and avoid stress")
        recommendations.append("Consult a cardiologist")
    if "Diabetes" in " ".join(risks):
        recommendations.append("Monitor blood sugar levels regularly")
        recommendations.append("Follow a strict low-sugar diet")
        recommendations.append("HbA1c test recommended")
    if "Cholesterol" in " ".join(risks):
        recommendations.append("Avoid fried and fatty foods")
        recommendations.append("Lipid profile test recommended")
    if "Anemia" in " ".join(risks):
        recommendations.append("Iron-rich diet recommended")
        recommendations.append("Complete Blood Count (CBC) test advised")
    if "chest" in symptoms.lower():
        recommendations.append("ECG (Electrocardiogram) test recommended")
        recommendations.append("Cardiology consultation advised")
    if "breath" in symptoms.lower():
        recommendations.append("Chest X-ray recommended")
        recommendations.append("Pulmonology consultation advised")
    if not recommendations:
        recommendations.append("Maintain a healthy diet and exercise regularly")
        recommendations.append("Routine checkup after 3 months")
    return recommendations

def simplify_terms(risks, recommendations):
    simple_risks = [TERM_SIMPLIFIER.get(r, r) for r in risks]
    simple_recs = [TERM_SIMPLIFIER.get(r, r) for r in recommendations]
    return simple_risks, simple_recs

def get_prescriptions(risks):
    prescriptions = []
    for risk in risks:
        if risk in PRESCRIPTION_TEMPLATES:
            for med in PRESCRIPTION_TEMPLATES[risk]:
                prescriptions.append(med)
    return prescriptions

def generate_report_text(data):
    today = date.today().strftime("%d/%m/%Y")
    bp_sys = data.get("bp_systolic", "")
    bp_dia = data.get("bp_diastolic", "")
    bp_str = f"{bp_sys}/{bp_dia} mmHg" if bp_sys and bp_dia else "Not provided"

    findings = []
    if bp_sys:
        findings.append(f"Blood Pressure (Systolic): {check_value('bp_systolic', bp_sys)}")
    if bp_dia:
        findings.append(f"Blood Pressure (Diastolic): {check_value('bp_diastolic', bp_dia)}")
    if data.get("sugar"):
        findings.append(f"Blood Sugar: {check_value('sugar', data['sugar'])}")
    if data.get("cholesterol"):
        findings.append(f"Cholesterol: {check_value('cholesterol', data['cholesterol'])}")
    if data.get("hemoglobin"):
        findings.append(f"Hemoglobin: {check_value('hemoglobin', data['hemoglobin'])}")
    if data.get("pulse"):
        findings.append(f"Pulse Rate: {check_value('pulse', data['pulse'])}")

    risks = detect_risks(data)
    recommendations = get_recommendations(risks, data.get("symptoms", ""))
    simple_risks, simple_recs = simplify_terms(risks, recommendations)
    prescriptions = get_prescriptions(risks)

    report = {
        "date": today,
        "patient_name": data.get("patient_name", "Unknown"),
        "age": data.get("age", ""),
        "gender": data.get("gender", ""),
        "symptoms": data.get("symptoms", ""),
        "history": data.get("history", ""),
        "bp": bp_str,
        "findings": findings,
        "risks": risks,
        "recommendations": recommendations,
        "simple_risks": simple_risks,
        "simple_recs": simple_recs,
        "prescriptions": prescriptions,
    }
    return report

def section_header(pdf, title, r, g, b):
    """Helper to draw a colored section header"""
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(r, g, b)
    pdf.set_text_color(255, 255, 255)
    pdf.set_x(10)
    pdf.cell(190, 8, f"  {title}", fill=True, ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

def write_line(pdf, text, color=None):
    """Helper to write a full width multi_cell line"""
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(12)
    if color:
        pdf.set_text_color(*color)
    pdf.multi_cell(186, 6, text)
    pdf.set_text_color(0, 0, 0)

def generate_pdf(report, filename="report.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Header ──
    pdf.set_fill_color(41, 128, 185)
    pdf.rect(0, 0, 210, 28, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_xy(0, 6)
    pdf.cell(210, 10, "MEDICAL REPORT", align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(0, 18)
    pdf.cell(210, 6, f"Generated on: {report['date']}", align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(18)

    # ── Patient Information ──
    section_header(pdf, "PATIENT INFORMATION", 52, 73, 94)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(12)
    pdf.cell(90, 6, f"Name   : {report['patient_name']}")
    pdf.cell(90, 6, f"Age    : {report['age']} years", ln=True)
    pdf.set_x(12)
    pdf.cell(90, 6, f"Gender : {report['gender']}", ln=True)
    pdf.ln(4)

    # ── Symptoms ──
    section_header(pdf, "CHIEF COMPLAINT / SYMPTOMS", 52, 73, 94)
    write_line(pdf, report["symptoms"] or "Not provided")
    pdf.ln(3)

    # ── Medical History ──
    if report["history"]:
        section_header(pdf, "MEDICAL HISTORY", 52, 73, 94)
        write_line(pdf, report["history"])
        pdf.ln(3)

    # ── Test Findings ──
    section_header(pdf, "TEST FINDINGS", 52, 73, 94)
    for finding in report["findings"]:
        if "HIGH" in finding or "LOW" in finding:
            write_line(pdf, f"  * {finding}", color=(192, 57, 43))
        else:
            write_line(pdf, f"  * {finding}", color=(39, 174, 96))
    pdf.ln(3)

    # ── Risk Assessment ──
    section_header(pdf, "RISK ASSESSMENT", 52, 73, 94)
    if report["risks"]:
        for risk in report["risks"]:
            write_line(pdf, f"  ! {risk}", color=(192, 57, 43))
    else:
        write_line(pdf, "  No major risks detected", color=(39, 174, 96))
    pdf.ln(3)

    # ── Recommendations ──
    section_header(pdf, "RECOMMENDATIONS", 52, 73, 94)
    for rec in report["recommendations"]:
        write_line(pdf, f"  * {rec}")
    pdf.ln(3)

    # ── Prescription Template ──
    if report["prescriptions"]:
        section_header(pdf, "PRESCRIPTION TEMPLATE", 41, 128, 185)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_fill_color(255, 243, 205)
        pdf.set_x(12)
        pdf.set_text_color(120, 66, 18)
        pdf.multi_cell(186, 5,
            "DISCLAIMER: This prescription template is for EDUCATIONAL and DEMO "
            "purposes only. Medicines should only be prescribed by a qualified "
            "and licensed medical doctor. Do not self-medicate.")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)
        for i, med in enumerate(report["prescriptions"], 1):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_x(12)
            pdf.cell(186, 6, f"  {i}. {med['medicine']}", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_x(16)
            pdf.cell(186, 5, f"     Dosage   : {med['dosage']}", ln=True)
            pdf.set_x(16)
            pdf.cell(186, 5, f"     Duration : {med['duration']}", ln=True)
            pdf.ln(3)
        pdf.ln(2)

    # ── Patient Friendly Summary ──
    section_header(pdf, "PATIENT FRIENDLY SUMMARY", 39, 174, 96)
    if report["simple_risks"]:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_x(12)
        pdf.cell(186, 6, "What This Means For You:", ln=True)
        for sr in report["simple_risks"]:
            write_line(pdf, f"  * {sr}", color=(41, 128, 185))
        pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_x(12)
    pdf.cell(186, 6, "What You Should Do:", ln=True)
    for srec in report["simple_recs"]:
        write_line(pdf, f"  -> {srec}", color=(39, 174, 96))
    pdf.ln(3)

    # ── Disclaimer ──
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.set_x(12)
    pdf.multi_cell(186, 5,
        "Disclaimer: This report is AI-generated for assistance purposes only. "
        "It is not a substitute for professional medical advice, diagnosis or "
        "treatment. Always consult a qualified doctor.")

    path = os.path.join("outputs", filename)
    pdf.output(path)
    return path