"""
Generate the CT-200 CardioTrack Blood Pressure Monitor manuals (v1 and v2).
This creates two realistic fictional medical device manuals with structural
variations (duplicate headings, inconsistent numbering, etc.) as mentioned
in the assignment.
"""
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


def make_styles():
    styles = getSampleStyleSheet()
    custom = {
        "DocTitle": ParagraphStyle(
            "DocTitle", parent=styles["Title"],
            fontSize=20, spaceAfter=16, alignment=TA_CENTER,
            textColor=colors.HexColor("#1a1a2e")
        ),
        "H1": ParagraphStyle(
            "H1", parent=styles["Heading1"],
            fontSize=14, spaceBefore=14, spaceAfter=6,
            textColor=colors.HexColor("#16213e"),
            borderPad=4
        ),
        "H2": ParagraphStyle(
            "H2", parent=styles["Heading2"],
            fontSize=12, spaceBefore=10, spaceAfter=4,
            textColor=colors.HexColor("#0f3460")
        ),
        "H3": ParagraphStyle(
            "H3", parent=styles["Heading3"],
            fontSize=11, spaceBefore=8, spaceAfter=3,
            textColor=colors.HexColor("#533483")
        ),
        "Body": ParagraphStyle(
            "Body", parent=styles["Normal"],
            fontSize=10, spaceAfter=6, leading=14,
            alignment=TA_JUSTIFY
        ),
        "Bullet": ParagraphStyle(
            "Bullet", parent=styles["Normal"],
            fontSize=10, spaceAfter=3, leftIndent=20,
            bulletIndent=10, leading=13
        ),
        "Caption": ParagraphStyle(
            "Caption", parent=styles["Normal"],
            fontSize=9, spaceAfter=6, alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"), italics=True
        ),
        "Warning": ParagraphStyle(
            "Warning", parent=styles["Normal"],
            fontSize=10, spaceAfter=6, leftIndent=10, rightIndent=10,
            backColor=colors.HexColor("#fff3cd"), borderColor=colors.HexColor("#ffc107"),
            borderWidth=1, borderPad=6, textColor=colors.HexColor("#856404")
        ),
    }
    return custom


def build_v1(styles):
    story = []

    # Cover
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("CardioTrack CT-200", styles["DocTitle"]))
    story.append(Paragraph("Home Blood Pressure Monitor", styles["DocTitle"]))
    story.append(Paragraph("User & Technical Manual — Version 1.0", styles["H2"]))
    story.append(Paragraph("Document ID: CT200-MAN-001 | Revision: A", styles["Body"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "WARNING: Read all instructions carefully before use. For home use only. "
        "Not intended as a replacement for professional medical advice.",
        styles["Warning"]
    ))
    story.append(PageBreak())

    # 1. Introduction
    story.append(Paragraph("1. Introduction", styles["H1"]))
    story.append(Paragraph(
        "The CardioTrack CT-200 is a clinically validated, oscillometric blood pressure monitor "
        "designed for home use by adults aged 18 years and older. It measures systolic and diastolic "
        "blood pressure, as well as pulse rate, using an upper-arm cuff. The device is intended to "
        "assist users in tracking their cardiovascular health over time under the guidance of a healthcare "
        "professional.",
        styles["Body"]
    ))

    # 1.1
    story.append(Paragraph("1.1 Intended Use", styles["H2"]))
    story.append(Paragraph(
        "The CT-200 is indicated for non-invasive blood pressure measurement in adult patients. "
        "It is designed for self-measurement at home and is not intended for use in neonates, "
        "children, or patients with arrhythmia unless specifically directed by a physician. "
        "Results should be interpreted by a qualified healthcare provider.",
        styles["Body"]
    ))

    # 1.2
    story.append(Paragraph("1.2 Contraindications", styles["H2"]))
    story.append(Paragraph("Do not use this device if any of the following apply:", styles["Body"]))
    for item in [
        "The patient has a cardiac pacemaker or other implanted electronic device.",
        "The measurement site has lymphedema, fistula, or intravenous lines.",
        "The patient is undergoing infusion therapy on the measured arm.",
        "The cuff is visibly damaged or the tubing is kinked.",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    # 1.3
    story.append(Paragraph("1.3 Symbols and Conventions", styles["H2"]))
    story.append(Paragraph(
        "Throughout this manual, the following conventions are used:",
        styles["Body"]
    ))
    data = [
        ["Symbol / Term", "Meaning"],
        ["WARNING", "Risk of patient injury if instruction not followed."],
        ["CAUTION", "Risk of device damage or inaccurate readings."],
        ["NOTE", "Important information that improves usability."],
        ["SYS", "Systolic pressure (mmHg)"],
        ["DIA", "Diastolic pressure (mmHg)"],
        ["PR", "Pulse rate (bpm)"],
    ]
    t = Table(data, colWidths=[1.8 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2 * inch))
    story.append(PageBreak())

    # 2. Device Description
    story.append(Paragraph("2. Device Description", styles["H1"]))
    story.append(Paragraph(
        "The CT-200 system consists of a main monitor unit, a standard adult upper-arm cuff "
        "(fits arm circumferences 22–42 cm), a latex-free inflation bladder, a USB-C charging cable, "
        "and a carrying case. An optional large cuff (fits 32–52 cm) is available separately.",
        styles["Body"]
    ))

    story.append(Paragraph("2.1 Hardware Components", styles["H2"]))
    for item in [
        "Main unit: 130 mm × 90 mm × 50 mm, 280 g (without batteries)",
        "3.5-inch colour LCD display (320 × 240 resolution)",
        "Rechargeable Li-ion battery: 1800 mAh, rated for 300 measurements per charge",
        "Built-in Bluetooth 5.0 (BLE) for smartphone connectivity",
        "Internal memory: stores up to 60 readings per user (2 users supported)",
        "Operating pressure range: 0–300 mmHg",
        "Accuracy: ±3 mmHg (pressure), ±5% (pulse rate)",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    story.append(Paragraph("2.2 Software Overview", styles["H2"]))
    story.append(Paragraph(
        "The CT-200 runs firmware version 2.1.4. The firmware manages measurement acquisition, "
        "data storage, Bluetooth communication, and safety interlocks. A companion mobile application "
        "(CardioTrack App, iOS 14+ / Android 10+) is available for trend tracking and physician sharing.",
        styles["Body"]
    ))

    story.append(Paragraph("2.3 Physical Interfaces", styles["H2"]))
    story.append(Paragraph(
        "The device exposes the following external interfaces:",
        styles["Body"]
    ))
    data2 = [
        ["Interface", "Type", "Purpose"],
        ["USB-C Port", "Charging only", "Battery recharging; data export not supported via USB"],
        ["Cuff Connector", "Proprietary pneumatic", "Connects upper-arm cuff to inflation system"],
        ["BLE Radio", "Bluetooth 5.0 LE", "Pairing with CardioTrack mobile app"],
        ["START/STOP Button", "Tactile pushbutton", "Initiates and aborts measurement cycles"],
        ["MODE Button", "Tactile pushbutton", "Cycles through user profiles and history view"],
    ]
    t2 = Table(data2, colWidths=[1.5 * inch, 1.5 * inch, 3.3 * inch])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t2)
    story.append(PageBreak())

    # 3. Safety Requirements
    story.append(Paragraph("3. Safety Requirements", styles["H1"]))
    story.append(Paragraph(
        "All safety requirements in this section are mandatory and shall be verified during "
        "production acceptance testing and post-market surveillance.",
        styles["Body"]
    ))

    story.append(Paragraph("3.1 Pressure Safety", styles["H2"]))
    story.append(Paragraph(
        "The inflation system shall not exceed a maximum cuff pressure of 300 mmHg under any "
        "operating condition. The firmware enforces this limit via a hardware pressure relief valve "
        "and a software interlock.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "If cuff pressure exceeds 295 mmHg during inflation, the firmware shall:",
        styles["Body"]
    ))
    for item in [
        "Immediately open the exhaust valve to initiate deflation.",
        "Display error code E3 on the LCD.",
        "Log the event with a timestamp to non-volatile memory.",
        "Auto-deflate to 0 mmHg within 2 seconds of detection.",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    story.append(Paragraph("3.2 Electrical Safety", styles["H2"]))
    story.append(Paragraph(
        "The CT-200 is classified as a Class II device (IEC 60601-1). The device shall meet "
        "IEC 60601-1 Edition 3.2 requirements for basic safety and essential performance. "
        "Maximum patient leakage current: 10 μA (normal condition), 50 μA (single-fault condition).",
        styles["Body"]
    ))

    story.append(Paragraph("3.3 Electromagnetic Compatibility", styles["H2"]))
    story.append(Paragraph(
        "The CT-200 shall comply with IEC 60601-1-2 for EMC. The device must maintain essential "
        "performance in environments with RF field strengths up to 3 V/m (80 MHz – 2.5 GHz). "
        "The BLE radio shall not interfere with other medical devices within 1 metre.",
        styles["Body"]
    ))

    # NOTE: Intentional duplicate heading for testing purposes (structural irregularity)
    story.append(Paragraph("3.3 Battery and Charging Safety", styles["H2"]))
    story.append(Paragraph(
        "The integrated Li-ion battery shall be protected against overcharge, over-discharge, "
        "and short-circuit conditions by the battery management IC. Charging shall cease automatically "
        "when the battery reaches 100% state of charge. The device shall display a low-battery warning "
        "when charge falls below 15%.",
        styles["Body"]
    ))

    story.append(Paragraph("3.4 Alarm Conditions", styles["H2"]))
    story.append(Paragraph(
        "The device shall generate a visual alarm (flashing display) for the following conditions:",
        styles["Body"]
    ))
    for code, desc in [
        ("E1", "Cuff not detected or improperly connected"),
        ("E2", "Arm movement detected during measurement (excessive motion artifact)"),
        ("E3", "Cuff pressure exceeded safe limit (see 3.1)"),
        ("E4", "Battery critically low (below 5%)"),
        ("E5", "Internal sensor fault"),
        ("E6", "Bluetooth pairing failure after 3 consecutive attempts"),
    ]:
        story.append(Paragraph(f"• {code}: {desc}", styles["Bullet"]))
    story.append(PageBreak())

    # 4. Measurement Procedure
    story.append(Paragraph("4. Measurement Procedure", styles["H1"]))
    story.append(Paragraph(
        "Follow these steps to ensure accurate and reproducible blood pressure measurements.",
        styles["Body"]
    ))

    story.append(Paragraph("4.1 Patient Preparation", styles["H2"]))
    for item in [
        "Rest quietly for at least 5 minutes before measurement.",
        "Avoid caffeine, smoking, and exercise for 30 minutes prior.",
        "Sit upright in a chair with back support; feet flat on floor.",
        "Support the arm at heart level on a flat surface.",
        "Remove tight clothing from the upper arm.",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    story.append(Paragraph("4.2 Cuff Application", styles["H2"]))
    story.append(Paragraph(
        "Place the cuff on the bare upper arm 2–3 cm above the antecubital fossa (elbow crease). "
        "The artery marker on the cuff must align with the brachial artery. Tighten the cuff so "
        "that two fingers can be inserted between the cuff and the arm.",
        styles["Body"]
    ))

    story.append(Paragraph("4.3 Measurement Acquisition", styles["H2"]))
    story.append(Paragraph(
        "Press START/STOP. The device will inflate the cuff automatically to the target pressure, "
        "then gradually deflate while the oscillometric algorithm detects oscillations corresponding "
        "to systolic and diastolic pressures. The measurement cycle takes approximately 30–60 seconds. "
        "Do not move or speak during measurement.",
        styles["Body"]
    ))

    story.append(Paragraph("4.4 Reading Results", styles["H2"]))
    story.append(Paragraph(
        "Upon completion, the display shows SYS / DIA (mmHg) and PR (bpm). Values are automatically "
        "stored in the current user's memory slot with a date/time stamp. An IHB (Irregular HeartBeat) "
        "indicator will appear if the pulse rhythm was inconsistent during measurement.",
        styles["Body"]
    ))
    story.append(PageBreak())

    # 5. Alarm and Error Handling
    story.append(Paragraph("5. Alarm and Error Handling", styles["H1"]))
    story.append(Paragraph(
        "This section describes the complete set of alarms, their triggers, and required device "
        "responses. All alarms shall be tested during acceptance testing.",
        styles["Body"]
    ))

    story.append(Paragraph("5.1 Error Code Reference", styles["H2"]))
    data3 = [
        ["Error Code", "Trigger Condition", "Device Response", "User Action"],
        ["E1", "Cuff not detected", "Halt inflation, display E1", "Re-attach cuff"],
        ["E2", "Motion artifact > threshold", "Abort measurement, display E2", "Repeat measurement"],
        ["E3", "Pressure ≥ 295 mmHg", "Deflate within 2 s, display E3, log event", "Contact service"],
        ["E4", "Battery < 5%", "Display E4, allow one more measurement", "Charge device"],
        ["E5", "Sensor fault", "Halt, display E5, log fault code", "Power cycle; if persists, service"],
        ["E6", "BLE pairing fail (3×)", "Display E6, disable BLE for 60 s", "Retry pairing"],
    ]
    t3 = Table(data3, colWidths=[1.0 * inch, 1.8 * inch, 2.2 * inch, 1.3 * inch])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
        ("WORDWRAP", (0, 0), (-1, -1), "CJK"),
    ]))
    story.append(t3)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("5.2 Watchdog Timer", styles["H2"]))
    story.append(Paragraph(
        "The firmware implements a hardware watchdog timer with a 4-second timeout. If the main "
        "application loop fails to service the watchdog within this period (e.g., due to a software "
        "hang), the watchdog resets the microcontroller and logs an unclean shutdown event.",
        styles["Body"]
    ))

    story.append(Paragraph("5.3 Measurement Timeout", styles["H2"]))
    story.append(Paragraph(
        "If a measurement is not completed within 120 seconds of initiation (e.g., cuff leakage "
        "prevents the target pressure from being reached), the firmware shall abort the cycle, "
        "display error code E7, and fully deflate the cuff.",
        styles["Body"]
    ))
    story.append(PageBreak())

    # 6. Data Management
    story.append(Paragraph("6. Data Management", styles["H1"]))
    story.append(Paragraph(
        "The CT-200 stores measurement data locally and optionally synchronises it to the CardioTrack "
        "mobile application over BLE.",
        styles["Body"]
    ))

    story.append(Paragraph("6.1 Local Storage", styles["H2"]))
    story.append(Paragraph(
        "Internal memory holds up to 60 readings per user profile. When memory is full, the oldest "
        "reading is overwritten (circular buffer). Each record contains: date, time, SYS, DIA, PR, "
        "IHB flag, and a measurement quality score (0–100).",
        styles["Body"]
    ))

    story.append(Paragraph("6.2 Bluetooth Synchronisation", styles["H2"]))
    story.append(Paragraph(
        "After a successful measurement, the device advertises a BLE GATT notification containing "
        "the latest reading. The CardioTrack app, if in range and paired, receives the notification "
        "and stores the reading in the app's local database. Full history sync can be triggered manually "
        "from the app.",
        styles["Body"]
    ))

    story.append(Paragraph("6.3 Data Privacy", styles["H2"]))
    story.append(Paragraph(
        "All BLE communications are encrypted using AES-128 CCM as per the BLE specification. "
        "The device does not collect or transmit personally identifiable information (PII). "
        "User profile names stored on the device are limited to 8 alphanumeric characters.",
        styles["Body"]
    ))
    story.append(PageBreak())

    # 7. Maintenance and Service
    story.append(Paragraph("7. Maintenance and Service", styles["H1"]))

    story.append(Paragraph("7.1 Cleaning", styles["H2"]))
    story.append(Paragraph(
        "Clean the exterior of the monitor unit with a soft cloth lightly dampened with 70% isopropyl "
        "alcohol. Do not immerse the device in liquid. The cuff may be hand-washed in lukewarm water "
        "and air-dried. Do not machine-wash the cuff.",
        styles["Body"]
    ))

    story.append(Paragraph("7.2 Calibration", styles["H2"]))
    story.append(Paragraph(
        "The CT-200 requires calibration every 2 years or after any repair that affects the pressure "
        "transducer. Calibration must be performed by an authorized service centre using traceable "
        "reference equipment. Field calibration by the end user is not permitted.",
        styles["Body"]
    ))

    story.append(Paragraph("7.3 Disposal", styles["H2"]))
    story.append(Paragraph(
        "Dispose of the CT-200 in accordance with local electronic waste (WEEE) regulations. "
        "The Li-ion battery must be removed before disposal and recycled separately. "
        "Do not dispose of batteries in municipal waste.",
        styles["Body"]
    ))
    story.append(PageBreak())

    # 8. Technical Specifications
    story.append(Paragraph("8. Technical Specifications", styles["H1"]))
    data4 = [
        ["Parameter", "Specification"],
        ["Measurement Method", "Oscillometric"],
        ["Measurement Range (Pressure)", "20–280 mmHg"],
        ["Measurement Range (Pulse)", "40–200 bpm"],
        ["Accuracy (Pressure)", "±3 mmHg"],
        ["Accuracy (Pulse Rate)", "±5% of reading"],
        ["Max Safe Cuff Pressure", "300 mmHg (hardware limit), 295 mmHg (software limit)"],
        ["Cuff Size (Standard)", "22–42 cm arm circumference"],
        ["Display", "3.5-inch colour LCD, 320×240"],
        ["Battery", "Li-ion 1800 mAh, USB-C charging"],
        ["Battery Life", "≥300 measurements per charge"],
        ["Memory", "60 readings × 2 users"],
        ["Connectivity", "Bluetooth 5.0 LE"],
        ["Operating Temperature", "10–40 °C"],
        ["Storage Temperature", "-20–60 °C"],
        ["Ingress Protection", "IP20"],
        ["Dimensions", "130 × 90 × 50 mm"],
        ["Weight", "280 g (without batteries/cuff)"],
        ["Regulatory", "IEC 60601-1 Ed. 3.2, IEC 60601-1-2, ISO 81060-2"],
    ]
    t4 = Table(data4, colWidths=[2.5 * inch, 3.8 * inch])
    t4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t4)
    story.append(PageBreak())

    # 9. Regulatory Compliance
    story.append(Paragraph("9. Regulatory Compliance", styles["H1"]))
    story.append(Paragraph(
        "The CT-200 has been designed and manufactured in accordance with the following standards "
        "and regulations. Compliance documentation is available upon request.",
        styles["Body"]
    ))
    for item in [
        "IEC 60601-1:2005+AMD1:2012+AMD2:2020 (General requirements for basic safety and essential performance)",
        "IEC 60601-1-2:2014+AMD1:2020 (Electromagnetic disturbances)",
        "ISO 81060-2:2018/AMD1:2020 (Non-invasive sphygmomanometers – clinical investigation)",
        "EU MDR 2017/745 (European Medical Device Regulation)",
        "FDA 21 CFR Part 820 (Quality System Regulation)",
        "ANSI/AAMI SP10:2002/(R)2008 & A1:2003/(R)2008 & A2:2006/(R)2008",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    story.append(Paragraph("9.1 Declaration of Conformity", styles["H2"]))
    story.append(Paragraph(
        "Tri9T Medical Devices Ltd. declares that the CT-200 conforms to the essential requirements "
        "of Annex I of the EU MDR 2017/745. The declaration of conformity is available at "
        "https://tri9t.example.com/doc/CT200.",
        styles["Body"]
    ))

    story.append(Paragraph("9.2 Authorized Representative", styles["H2"]))
    story.append(Paragraph(
        "EU Authorised Representative: MedRep EU GmbH, Berliner Str. 42, 10115 Berlin, Germany. "
        "UK Responsible Person: MedRep UK Ltd., 10 Harley Street, London, W1G 9PF.",
        styles["Body"]
    ))
    story.append(PageBreak())

    # 10. Revision History
    story.append(Paragraph("10. Revision History", styles["H1"]))
    data5 = [
        ["Revision", "Date", "Author", "Description"],
        ["A", "2025-01-10", "J. Smith", "Initial release"],
        ["A.1", "2025-03-15", "L. Patel", "Corrected cuff size table, added E6 error code"],
    ]
    t5 = Table(data5, colWidths=[1.0 * inch, 1.2 * inch, 1.5 * inch, 2.6 * inch])
    t5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t5)
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "End of CT-200 User & Technical Manual — Version 1.0",
        styles["Caption"]
    ))

    return story


def build_v2(styles):
    """
    Version 2: key changes from v1:
    - Section 3.1 Pressure Safety: threshold changed from 295 to 290 mmHg, auto-deflate window
      tightened from 2 seconds to 1.5 seconds.
    - Section 3.4: E7 added to alarm list (was only in 5.3 in v1).
    - Section 5.1: E3 trigger updated to 290 mmHg, deflate window to 1.5 s.
    - Section 6.1: Memory expanded from 60 to 90 readings per user.
    - Section 8: Measurement range pressure extended to 285 mmHg; battery life updated to 350 measurements.
    - New section 10.1 added (Firmware Update Procedure).
    - Revision history entry added.
    """
    story = []

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("CardioTrack CT-200", styles["DocTitle"]))
    story.append(Paragraph("Home Blood Pressure Monitor", styles["DocTitle"]))
    story.append(Paragraph("User & Technical Manual — Version 2.0", styles["H2"]))
    story.append(Paragraph("Document ID: CT200-MAN-001 | Revision: B", styles["Body"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph(
        "WARNING: Read all instructions carefully before use. For home use only. "
        "Not intended as a replacement for professional medical advice.",
        styles["Warning"]
    ))
    story.append(PageBreak())

    story.append(Paragraph("1. Introduction", styles["H1"]))
    story.append(Paragraph(
        "The CardioTrack CT-200 is a clinically validated, oscillometric blood pressure monitor "
        "designed for home use by adults aged 18 years and older. It measures systolic and diastolic "
        "blood pressure, as well as pulse rate, using an upper-arm cuff. The device is intended to "
        "assist users in tracking their cardiovascular health over time under the guidance of a healthcare "
        "professional.",
        styles["Body"]
    ))

    story.append(Paragraph("1.1 Intended Use", styles["H2"]))
    story.append(Paragraph(
        "The CT-200 is indicated for non-invasive blood pressure measurement in adult patients. "
        "It is designed for self-measurement at home and is not intended for use in neonates, "
        "children, or patients with arrhythmia unless specifically directed by a physician. "
        "Results should be interpreted by a qualified healthcare provider.",
        styles["Body"]
    ))

    story.append(Paragraph("1.2 Contraindications", styles["H2"]))
    story.append(Paragraph("Do not use this device if any of the following apply:", styles["Body"]))
    for item in [
        "The patient has a cardiac pacemaker or other implanted electronic device.",
        "The measurement site has lymphedema, fistula, or intravenous lines.",
        "The patient is undergoing infusion therapy on the measured arm.",
        "The cuff is visibly damaged or the tubing is kinked.",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    story.append(Paragraph("1.3 Symbols and Conventions", styles["H2"]))
    story.append(Paragraph("Throughout this manual, the following conventions are used:", styles["Body"]))
    data = [
        ["Symbol / Term", "Meaning"],
        ["WARNING", "Risk of patient injury if instruction not followed."],
        ["CAUTION", "Risk of device damage or inaccurate readings."],
        ["NOTE", "Important information that improves usability."],
        ["SYS", "Systolic pressure (mmHg)"],
        ["DIA", "Diastolic pressure (mmHg)"],
        ["PR", "Pulse rate (bpm)"],
    ]
    t = Table(data, colWidths=[1.8 * inch, 4.5 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(PageBreak())

    story.append(Paragraph("2. Device Description", styles["H1"]))
    story.append(Paragraph(
        "The CT-200 system consists of a main monitor unit, a standard adult upper-arm cuff "
        "(fits arm circumferences 22–42 cm), a latex-free inflation bladder, a USB-C charging cable, "
        "and a carrying case. An optional large cuff (fits 32–52 cm) is available separately.",
        styles["Body"]
    ))

    story.append(Paragraph("2.1 Hardware Components", styles["H2"]))
    for item in [
        "Main unit: 130 mm × 90 mm × 50 mm, 280 g (without batteries)",
        "3.5-inch colour LCD display (320 × 240 resolution)",
        "Rechargeable Li-ion battery: 1800 mAh, rated for 350 measurements per charge",
        "Built-in Bluetooth 5.0 (BLE) for smartphone connectivity",
        "Internal memory: stores up to 90 readings per user (2 users supported)",
        "Operating pressure range: 0–300 mmHg",
        "Accuracy: ±3 mmHg (pressure), ±5% (pulse rate)",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    story.append(Paragraph("2.2 Software Overview", styles["H2"]))
    story.append(Paragraph(
        "The CT-200 runs firmware version 2.2.0. The firmware manages measurement acquisition, "
        "data storage, Bluetooth communication, and safety interlocks. A companion mobile application "
        "(CardioTrack App, iOS 14+ / Android 10+) is available for trend tracking and physician sharing.",
        styles["Body"]
    ))

    story.append(Paragraph("2.3 Physical Interfaces", styles["H2"]))
    story.append(Paragraph("The device exposes the following external interfaces:", styles["Body"]))
    data2 = [
        ["Interface", "Type", "Purpose"],
        ["USB-C Port", "Charging only", "Battery recharging; data export not supported via USB"],
        ["Cuff Connector", "Proprietary pneumatic", "Connects upper-arm cuff to inflation system"],
        ["BLE Radio", "Bluetooth 5.0 LE", "Pairing with CardioTrack mobile app"],
        ["START/STOP Button", "Tactile pushbutton", "Initiates and aborts measurement cycles"],
        ["MODE Button", "Tactile pushbutton", "Cycles through user profiles and history view"],
    ]
    t2 = Table(data2, colWidths=[1.5 * inch, 1.5 * inch, 3.3 * inch])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t2)
    story.append(PageBreak())

    story.append(Paragraph("3. Safety Requirements", styles["H1"]))
    story.append(Paragraph(
        "All safety requirements in this section are mandatory and shall be verified during "
        "production acceptance testing and post-market surveillance.",
        styles["Body"]
    ))

    story.append(Paragraph("3.1 Pressure Safety", styles["H2"]))
    # CHANGED: 295 -> 290 mmHg; 2 seconds -> 1.5 seconds
    story.append(Paragraph(
        "The inflation system shall not exceed a maximum cuff pressure of 300 mmHg under any "
        "operating condition. The firmware enforces this limit via a hardware pressure relief valve "
        "and a software interlock.",
        styles["Body"]
    ))
    story.append(Paragraph(
        "If cuff pressure exceeds 290 mmHg during inflation, the firmware shall:",
        styles["Body"]
    ))
    for item in [
        "Immediately open the exhaust valve to initiate deflation.",
        "Display error code E3 on the LCD.",
        "Log the event with a timestamp to non-volatile memory.",
        "Auto-deflate to 0 mmHg within 1.5 seconds of detection.",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    story.append(Paragraph("3.2 Electrical Safety", styles["H2"]))
    story.append(Paragraph(
        "The CT-200 is classified as a Class II device (IEC 60601-1). The device shall meet "
        "IEC 60601-1 Edition 3.2 requirements for basic safety and essential performance. "
        "Maximum patient leakage current: 10 μA (normal condition), 50 μA (single-fault condition).",
        styles["Body"]
    ))

    story.append(Paragraph("3.3 Electromagnetic Compatibility", styles["H2"]))
    story.append(Paragraph(
        "The CT-200 shall comply with IEC 60601-1-2 for EMC. The device must maintain essential "
        "performance in environments with RF field strengths up to 3 V/m (80 MHz – 2.5 GHz). "
        "The BLE radio shall not interfere with other medical devices within 1 metre.",
        styles["Body"]
    ))

    # Duplicate heading preserved from v1
    story.append(Paragraph("3.3 Battery and Charging Safety", styles["H2"]))
    story.append(Paragraph(
        "The integrated Li-ion battery shall be protected against overcharge, over-discharge, "
        "and short-circuit conditions by the battery management IC. Charging shall cease automatically "
        "when the battery reaches 100% state of charge. The device shall display a low-battery warning "
        "when charge falls below 15%.",
        styles["Body"]
    ))

    story.append(Paragraph("3.4 Alarm Conditions", styles["H2"]))
    story.append(Paragraph(
        "The device shall generate a visual alarm (flashing display) for the following conditions:",
        styles["Body"]
    ))
    # E7 now included (was only in 5.3 in v1)
    for code, desc in [
        ("E1", "Cuff not detected or improperly connected"),
        ("E2", "Arm movement detected during measurement (excessive motion artifact)"),
        ("E3", "Cuff pressure exceeded safe limit — threshold 290 mmHg (see 3.1)"),
        ("E4", "Battery critically low (below 5%)"),
        ("E5", "Internal sensor fault"),
        ("E6", "Bluetooth pairing failure after 3 consecutive attempts"),
        ("E7", "Measurement timeout — cycle not completed within 120 seconds"),
    ]:
        story.append(Paragraph(f"• {code}: {desc}", styles["Bullet"]))
    story.append(PageBreak())

    story.append(Paragraph("4. Measurement Procedure", styles["H1"]))
    story.append(Paragraph(
        "Follow these steps to ensure accurate and reproducible blood pressure measurements.",
        styles["Body"]
    ))

    story.append(Paragraph("4.1 Patient Preparation", styles["H2"]))
    for item in [
        "Rest quietly for at least 5 minutes before measurement.",
        "Avoid caffeine, smoking, and exercise for 30 minutes prior.",
        "Sit upright in a chair with back support; feet flat on floor.",
        "Support the arm at heart level on a flat surface.",
        "Remove tight clothing from the upper arm.",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    story.append(Paragraph("4.2 Cuff Application", styles["H2"]))
    story.append(Paragraph(
        "Place the cuff on the bare upper arm 2–3 cm above the antecubital fossa (elbow crease). "
        "The artery marker on the cuff must align with the brachial artery. Tighten the cuff so "
        "that two fingers can be inserted between the cuff and the arm.",
        styles["Body"]
    ))

    story.append(Paragraph("4.3 Measurement Acquisition", styles["H2"]))
    story.append(Paragraph(
        "Press START/STOP. The device will inflate the cuff automatically to the target pressure, "
        "then gradually deflate while the oscillometric algorithm detects oscillations corresponding "
        "to systolic and diastolic pressures. The measurement cycle takes approximately 30–60 seconds. "
        "Do not move or speak during measurement.",
        styles["Body"]
    ))

    story.append(Paragraph("4.4 Reading Results", styles["H2"]))
    story.append(Paragraph(
        "Upon completion, the display shows SYS / DIA (mmHg) and PR (bpm). Values are automatically "
        "stored in the current user's memory slot with a date/time stamp. An IHB (Irregular HeartBeat) "
        "indicator will appear if the pulse rhythm was inconsistent during measurement.",
        styles["Body"]
    ))
    story.append(PageBreak())

    story.append(Paragraph("5. Alarm and Error Handling", styles["H1"]))
    story.append(Paragraph(
        "This section describes the complete set of alarms, their triggers, and required device "
        "responses. All alarms shall be tested during acceptance testing.",
        styles["Body"]
    ))

    story.append(Paragraph("5.1 Error Code Reference", styles["H2"]))
    # E3 updated: 290 mmHg, 1.5 s
    data3 = [
        ["Error Code", "Trigger Condition", "Device Response", "User Action"],
        ["E1", "Cuff not detected", "Halt inflation, display E1", "Re-attach cuff"],
        ["E2", "Motion artifact > threshold", "Abort measurement, display E2", "Repeat measurement"],
        ["E3", "Pressure ≥ 290 mmHg", "Deflate within 1.5 s, display E3, log event", "Contact service"],
        ["E4", "Battery < 5%", "Display E4, allow one more measurement", "Charge device"],
        ["E5", "Sensor fault", "Halt, display E5, log fault code", "Power cycle; if persists, service"],
        ["E6", "BLE pairing fail (3×)", "Display E6, disable BLE for 60 s", "Retry pairing"],
        ["E7", "Measurement timeout (120 s)", "Abort, deflate, display E7", "Retry; check cuff seal"],
    ]
    t3 = Table(data3, colWidths=[1.0 * inch, 1.8 * inch, 2.2 * inch, 1.3 * inch])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t3)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("5.2 Watchdog Timer", styles["H2"]))
    story.append(Paragraph(
        "The firmware implements a hardware watchdog timer with a 4-second timeout. If the main "
        "application loop fails to service the watchdog within this period (e.g., due to a software "
        "hang), the watchdog resets the microcontroller and logs an unclean shutdown event.",
        styles["Body"]
    ))

    story.append(Paragraph("5.3 Measurement Timeout", styles["H2"]))
    story.append(Paragraph(
        "If a measurement is not completed within 120 seconds of initiation (e.g., cuff leakage "
        "prevents the target pressure from being reached), the firmware shall abort the cycle, "
        "display error code E7, and fully deflate the cuff.",
        styles["Body"]
    ))
    story.append(PageBreak())

    story.append(Paragraph("6. Data Management", styles["H1"]))
    story.append(Paragraph(
        "The CT-200 stores measurement data locally and optionally synchronises it to the CardioTrack "
        "mobile application over BLE.",
        styles["Body"]
    ))

    story.append(Paragraph("6.1 Local Storage", styles["H2"]))
    # CHANGED: 60 -> 90 readings
    story.append(Paragraph(
        "Internal memory holds up to 90 readings per user profile. When memory is full, the oldest "
        "reading is overwritten (circular buffer). Each record contains: date, time, SYS, DIA, PR, "
        "IHB flag, and a measurement quality score (0–100).",
        styles["Body"]
    ))

    story.append(Paragraph("6.2 Bluetooth Synchronisation", styles["H2"]))
    story.append(Paragraph(
        "After a successful measurement, the device advertises a BLE GATT notification containing "
        "the latest reading. The CardioTrack app, if in range and paired, receives the notification "
        "and stores the reading in the app's local database. Full history sync can be triggered manually "
        "from the app.",
        styles["Body"]
    ))

    story.append(Paragraph("6.3 Data Privacy", styles["H2"]))
    story.append(Paragraph(
        "All BLE communications are encrypted using AES-128 CCM as per the BLE specification. "
        "The device does not collect or transmit personally identifiable information (PII). "
        "User profile names stored on the device are limited to 8 alphanumeric characters.",
        styles["Body"]
    ))
    story.append(PageBreak())

    story.append(Paragraph("7. Maintenance and Service", styles["H1"]))

    story.append(Paragraph("7.1 Cleaning", styles["H2"]))
    story.append(Paragraph(
        "Clean the exterior of the monitor unit with a soft cloth lightly dampened with 70% isopropyl "
        "alcohol. Do not immerse the device in liquid. The cuff may be hand-washed in lukewarm water "
        "and air-dried. Do not machine-wash the cuff.",
        styles["Body"]
    ))

    story.append(Paragraph("7.2 Calibration", styles["H2"]))
    story.append(Paragraph(
        "The CT-200 requires calibration every 2 years or after any repair that affects the pressure "
        "transducer. Calibration must be performed by an authorized service centre using traceable "
        "reference equipment. Field calibration by the end user is not permitted.",
        styles["Body"]
    ))

    story.append(Paragraph("7.3 Disposal", styles["H2"]))
    story.append(Paragraph(
        "Dispose of the CT-200 in accordance with local electronic waste (WEEE) regulations. "
        "The Li-ion battery must be removed before disposal and recycled separately. "
        "Do not dispose of batteries in municipal waste.",
        styles["Body"]
    ))
    story.append(PageBreak())

    story.append(Paragraph("8. Technical Specifications", styles["H1"]))
    data4 = [
        ["Parameter", "Specification"],
        ["Measurement Method", "Oscillometric"],
        ["Measurement Range (Pressure)", "20–285 mmHg"],
        ["Measurement Range (Pulse)", "40–200 bpm"],
        ["Accuracy (Pressure)", "±3 mmHg"],
        ["Accuracy (Pulse Rate)", "±5% of reading"],
        ["Max Safe Cuff Pressure", "300 mmHg (hardware limit), 290 mmHg (software limit)"],
        ["Cuff Size (Standard)", "22–42 cm arm circumference"],
        ["Display", "3.5-inch colour LCD, 320×240"],
        ["Battery", "Li-ion 1800 mAh, USB-C charging"],
        ["Battery Life", "≥350 measurements per charge"],
        ["Memory", "90 readings × 2 users"],
        ["Connectivity", "Bluetooth 5.0 LE"],
        ["Operating Temperature", "10–40 °C"],
        ["Storage Temperature", "-20–60 °C"],
        ["Ingress Protection", "IP20"],
        ["Dimensions", "130 × 90 × 50 mm"],
        ["Weight", "280 g (without batteries/cuff)"],
        ["Regulatory", "IEC 60601-1 Ed. 3.2, IEC 60601-1-2, ISO 81060-2"],
    ]
    t4 = Table(data4, colWidths=[2.5 * inch, 3.8 * inch])
    t4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t4)
    story.append(PageBreak())

    story.append(Paragraph("9. Regulatory Compliance", styles["H1"]))
    story.append(Paragraph(
        "The CT-200 has been designed and manufactured in accordance with the following standards "
        "and regulations. Compliance documentation is available upon request.",
        styles["Body"]
    ))
    for item in [
        "IEC 60601-1:2005+AMD1:2012+AMD2:2020 (General requirements for basic safety and essential performance)",
        "IEC 60601-1-2:2014+AMD1:2020 (Electromagnetic disturbances)",
        "ISO 81060-2:2018/AMD1:2020 (Non-invasive sphygmomanometers – clinical investigation)",
        "EU MDR 2017/745 (European Medical Device Regulation)",
        "FDA 21 CFR Part 820 (Quality System Regulation)",
        "ANSI/AAMI SP10:2002/(R)2008 & A1:2003/(R)2008 & A2:2006/(R)2008",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))

    story.append(Paragraph("9.1 Declaration of Conformity", styles["H2"]))
    story.append(Paragraph(
        "Tri9T Medical Devices Ltd. declares that the CT-200 conforms to the essential requirements "
        "of Annex I of the EU MDR 2017/745. The declaration of conformity is available at "
        "https://tri9t.example.com/doc/CT200.",
        styles["Body"]
    ))

    story.append(Paragraph("9.2 Authorized Representative", styles["H2"]))
    story.append(Paragraph(
        "EU Authorised Representative: MedRep EU GmbH, Berliner Str. 42, 10115 Berlin, Germany. "
        "UK Responsible Person: MedRep UK Ltd., 10 Harley Street, London, W1G 9PF.",
        styles["Body"]
    ))
    story.append(PageBreak())

    story.append(Paragraph("10. Revision History", styles["H1"]))
    data5 = [
        ["Revision", "Date", "Author", "Description"],
        ["A", "2025-01-10", "J. Smith", "Initial release"],
        ["A.1", "2025-03-15", "L. Patel", "Corrected cuff size table, added E6 error code"],
        ["B", "2025-09-01", "R. Nguyen",
         "Updated pressure safety threshold to 290 mmHg, tightened deflate window to 1.5 s, "
         "expanded memory to 90 readings, extended measurement range, added E7 to section 3.4, "
         "firmware updated to 2.2.0, added section 10.1"],
    ]
    t5 = Table(data5, colWidths=[1.0 * inch, 1.2 * inch, 1.5 * inch, 2.6 * inch])
    t5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t5)
    story.append(Spacer(1, 0.3 * inch))

    # New section 10.1
    story.append(Paragraph("10.1 Firmware Update Procedure", styles["H2"]))
    story.append(Paragraph(
        "Firmware updates are distributed via the CardioTrack mobile application. To update firmware:",
        styles["Body"]
    ))
    for item in [
        "Ensure device battery is above 50% before initiating an update.",
        "Open the CardioTrack app and navigate to Settings > Device > Firmware Update.",
        "The app will download the update package and transfer it to the device over BLE.",
        "The device will verify the package signature before applying the update.",
        "Do not power off the device or close the app during the update process.",
        "After a successful update, the device will restart automatically.",
    ]:
        story.append(Paragraph(f"• {item}", styles["Bullet"]))
    story.append(Paragraph(
        "WARNING: Interrupting a firmware update may corrupt the device firmware and require "
        "factory servicing. Always ensure stable BLE connectivity before updating.",
        styles["Warning"]
    ))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("End of CT-200 User & Technical Manual — Version 2.0", styles["Caption"]))

    return story


def generate():
    styles = make_styles()

    v1_path = os.path.join(DATA_DIR, "ct200_manual_v1.pdf")
    doc1 = SimpleDocTemplate(
        v1_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    doc1.build(build_v1(styles))
    print(f"Generated: {v1_path}")

    v2_path = os.path.join(DATA_DIR, "ct200_manual_v2.pdf")
    doc2 = SimpleDocTemplate(
        v2_path,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    doc2.build(build_v2(styles))
    print(f"Generated: {v2_path}")


if __name__ == "__main__":
    generate()
