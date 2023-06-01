from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image as ReportLabImage
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors

from io import BytesIO
import base64
import io

from datetime import datetime

def create_pdf(buffer, db_report, contractor_service_log,company):
    c = canvas.Canvas(buffer, pagesize=A4)
    # Creando las entradas
    if company.Name=="Expanding Possibilities":
       c.drawImage('expanding.png', 260, 720, 100, 100)
    elif company.Name == "Villa Lyan":
        c.drawImage('villa.png', 260, 720, 100, 100)
    c.line(30, 700, 580, 700)
    c.drawString(400, 703, "ANALYST SERVICE LOG")
    c.line(100, 650, 300, 650)
    c.drawString(30, 652, f"Client Name: {db_report.client.Name}")
    c.line(380, 650, 450, 650)
    c.drawString(305, 652, f"Recipient ID :")
    c.drawString(383, 652, 'ON FILE')
    c.line(120, 598, 300, 598)
    c.drawString(30, 600, f"Therapist Name:{db_report.contractor.Name}")
   # c.line(420, 598, 570, 598)
  #  c.drawString(305, 600, "Therapist Signature:")
  #  c.line(40, 70, 550, 70)
    c.drawString(450, 30, 'BY:')
    c.line(470, 30, 510, 30)
    c.drawString(515, 30, 'DATE:')
    c.line(550, 30, 590, 30)

    try:
        if contractor_service_log is not None:
            contractorsig = contractor_service_log.Signature
            img_data = base64.b64decode(contractorsig)
            img = ImageReader(BytesIO(img_data))
            c.drawImage(img, 440, 600, 70, 30)

        else:
            c.setStrokeColorRGB(1, 1, 1)
            c.setFillColorRGB(1, 1, 1)
            c.rect(440, 605, 70, 30, fill=True)
    except:
        c.setStrokeColorRGB(1, 1, 1)
        c.setFillColorRGB(1, 1, 1)
        c.rect(440, 605, 70, 30, fill=True)



    width, height = A4
    data = [['Date', 'Arrival time', 'Depart time', 'Units', 'Hours', 'CPT Code',
             'Visit at\n(1)home\n(2)Comunity\n(3)School',
             'Caregiver/Client\nSignature']]

    for unitdetail in db_report.unitdetails:
        for patient_unit in unitdetail.patientunitdetail:
            formatted_date = datetime.strftime(patient_unit.unitdetailp.DateOfService, '%Y-%m-%d')
            entry_time_string = patient_unit.EntryTime
            if ":" in entry_time_string and entry_time_string.count(":") == 2:
                entry_time_format_string = "%H:%M:%S"
            else:
                entry_time_format_string = "%H:%M"
            entry_time = datetime.strptime(entry_time_string, entry_time_format_string)
            departure_time_string = patient_unit.DepartureTime
            if ":" in departure_time_string and departure_time_string.count(":") == 2:
                departure_time_format_string = "%H:%M:%S"
            else:
                departure_time_format_string = "%H:%M"
            departure_time = datetime.strptime(departure_time_string, departure_time_format_string)
            time_difference = departure_time - entry_time
            hours = time_difference
            signature = patient_unit.Signature
            pic_split=signature.split(",")[1]
            imagen_bytes = base64.b64decode(pic_split)
            imagen_reader = io.BytesIO(imagen_bytes)
            imagen = ReportLabImage(imagen_reader, width=0.7 * inch, height=0.3 * inch)
            data.append([formatted_date, patient_unit.EntryTime, patient_unit.DepartureTime,
                         patient_unit.unitdetailp.Unit, hours, patient_unit.unitdetailp.subprocedure.Name,
                         patient_unit.unitdetailp.placeofservice.Value, imagen])
    #
    t = Table(data, colWidths=[70] + [60] * 2 + [40] + [60] * 3 + [80])
    t.setStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'Courier-Bold'),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                ('WORDWRAP', (0, 0), (-1, -1)),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ("MAXSIZE", (0, 1), (-1, -1), 50),
                ('MAXSIZE', (-1, 1), (-1, -1), 80)
                ])

    t.wrapOn(c, width, height)
    t.autoColumnWidths = True
    t.drawOn(c, 40, 450)

    # Nuevo
    styles = getSampleStyleSheet()

    ptext = "<u><b>CPT CODES</b></u>"
    p = Paragraph(ptext, style=styles["Normal"])
    p.wrapOn(c, 300, 650)
    p.drawOn(c, 280, 330)

    p1text = "<b>51-</b>Assessment"
    p = Paragraph(p1text, style=styles["Normal"])
    p.wrapOn(c, 300, 650)
    p.drawOn(c, 230, 310)

    p2text = "<b>51TS-</b>Reassessment"
    p = Paragraph(p2text, style=styles["Normal"])
    p.wrapOn(c, 300, 650)
    p.drawOn(c, 320, 310)

    p3text = "<b>BCaBA</b><br/>" \
             "<b>53-</b>Treatment by Protocol<br/>" \
             "<b>55XP-</b>BCaBA Supervision(Non-Reimbursable)<br/>" \
             "<b>55HN-</b>Treatment with Protocol<br/>" \
             "<b>56HN-</b>Family Training<br/>"
    p = Paragraph(p3text, style=styles["Normal"])
    p.wrapOn(c, 300, 650)
    p.drawOn(c, 110, 230)

    p4text = "<b>BCBA</b><br/>" \
             "<b>53-</b>Treatment by Protocol<br/>" \
             "<b>55-</b>Treatment with Protocol<br/>" \
             "<b>56-</b>Family Training<br/>"
    p = Paragraph(p4text, style=styles["Normal"])
    p.wrapOn(c, 300, 550)
    p.drawOn(c, 340, 245)

    ptext = "<font size=7><u><b>*Staff/Client/Guardian:I CERTIFY THAT HOURS SHOW ABOVE ARE CORRECT & THE WORK WAS PERFORMED IN A SATISFACTORY MANNER.</b></u></font>"
    p = Paragraph(ptext, style=styles["Normal"])
    p.wrapOn(c, 600, 650)
    p.drawOn(c, 58, 58)



    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.seek(0)
    buffer.close()


    return pdf