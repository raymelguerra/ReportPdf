import base64
import io
import tempfile
from datetime import datetime
from io import BytesIO

from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

from fastapi.responses import Response
from fastapi import HTTPException
from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse


from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image as ReportLabImage
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors

Base = declarative_base()


class ContractorServiceLog(Base):
    __tablename__ = "ContractorServiceLog"
    Id = Column(Integer, primary_key=True, index=True)
    ServiceLogId = Column(Integer, ForeignKey('ServiceLog.Id'))
    Signature = Column(String)
    SignatureDate = Column(DateTime)

    servicelog = relationship("ServiceLog", back_populates="contrator_servicelog")


class ServiceLog(Base):
    __tablename__ = "ServiceLog"
    Id = Column(Integer, primary_key=True, index=True)
    PeriodId = Column(Integer, ForeignKey('Period.Id'))
    period = relationship("Period", back_populates="servicelogp")
    ContractorId = Column(Integer, ForeignKey('Contractor.Id'))
    contractor = relationship("Contractor", back_populates="servicelogc")
    ClientId = Column(Integer, ForeignKey('Client.Id'))
    client = relationship("Client", back_populates="servicelogL")

    contrator_servicelog = relationship("ContractorServiceLog", back_populates="servicelog")
    unitdetails = relationship("UnitDetail", back_populates="servicelog")


class Period(Base):
    __tablename__ = "Period"
    Id = Column(Integer, primary_key=True, index=True)

    servicelogp = relationship("ServiceLog", back_populates="period")


class Contractor(Base):
    __tablename__ = "Contractor"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    servicelogc = relationship("ServiceLog", back_populates="contractor")
    payroll = relationship("Payroll", back_populates="contractor")


class Client(Base):
    __tablename__ = "Client"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)

    servicelogL = relationship("ServiceLog", back_populates="client")


class UnitDetail(Base):
    __tablename__ = "UnitDetail"
    Id = Column(Integer, primary_key=True, index=True)
    Modifiers = Column(String)
    PlaceOfServiceId = Column(Integer, ForeignKey('PlaceOfService.Id'))
    placeofservice = relationship("PlaceOfService", back_populates="unitdetail")
    DateOfService = Column(DateTime)
    Unit = Column(Integer)
    ServiceLogId = Column(Integer, ForeignKey('ServiceLog.Id'))
    servicelog = relationship("ServiceLog", back_populates="unitdetails")
    SubProcedureId = Column(Integer, ForeignKey('SubProcedure.Id'))
    subprocedure = relationship("SubProcedure", back_populates="unitdetailsp")
    patientunitdetail = relationship("PatientUnitDetail", back_populates="unitdetailp")


class PatientUnitDetail(Base):
    __tablename__ = "PatientUnitDetail"
    Id = Column(Integer, primary_key=True, index=True)
    UnitDetailId = Column(Integer, ForeignKey('UnitDetail.Id'))
    unitdetailp = relationship("UnitDetail", back_populates="patientunitdetail")
    SignatureDate = Column(DateTime)
    Signature = Column(String)
    EntryTime = Column(String)
    DepartureTime = Column(String)


class PlaceOfService(Base):
    __tablename__ = "PlaceOfService"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    Value = Column(String)

    unitdetail = relationship("UnitDetail", back_populates="placeofservice")


class SubProcedure(Base):
    __tablename__ = "SubProcedure"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    Rate = Column(Integer)
    unitdetailsp = relationship("UnitDetail", back_populates="subprocedure")
    ProcedureId = Column(Integer, ForeignKey('Procedure.Id'))
    procedure = relationship("Procedure", back_populates="subprocedure")


class Procedure(Base):
    __tablename__ = "Procedure"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    Rate = Column(Integer)
    subprocedure = relationship("SubProcedure", back_populates="procedure")
    payroll = relationship("Payroll", back_populates="procedure")


class Payroll(Base):
    __tablename__ = "Payroll"
    Id = Column(Integer, primary_key=True, index=True)
    ContractorId = Column(Integer, ForeignKey('Contractor.Id'))
    contractor = relationship("Contractor", back_populates="payroll")
    ContractorTypeId = Column(Integer, ForeignKey('ContractorType.Id'))
    contractortype = relationship("ContractorType", back_populates="payroll")
    ProcedureId = Column(Integer, ForeignKey('Procedure.Id'))
    procedure = relationship("Procedure", back_populates="payroll")
    CompanyId = Column(Integer, ForeignKey('Company.Id'))
    company = relationship("Company", back_populates="payroll")


class ContractorType(Base):
    __tablename__ = "ContractorType"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    payroll = relationship("Payroll", back_populates="contractortype")


class Company(Base):
    __tablename__ = "Company"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    Acronym = Column(String)
    Enabled = Column(Boolean)
    payroll = relationship("Payroll", back_populates="company")


metadata = MetaData()
engine = create_engine(
    'postgresql://linpostgres:HxywGpAs2-2CnbGh@lin-13704-4133-pgsql-primary.servers.linodedb.net:5432/aba_test')
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/generar/{id}/pdf")
def read_report(id: int, db: Session = Depends(get_db))-> FileResponse:
    db_report = db.query(ServiceLog) \
        .join(Contractor, Contractor.Id == ServiceLog.ContractorId, isouter=True) \
        .join(Client, Client.Id == ServiceLog.ClientId, isouter=True) \
        .join(Period, Period.Id == ServiceLog.PeriodId, isouter=True) \
        .join(Payroll, Payroll.ContractorId == Contractor.Id, isouter=True) \
        .join(Company, Company.Id == Payroll.CompanyId, isouter=True) \
        .join(ContractorType, ContractorType.Id == Payroll.ContractorTypeId, isouter=True) \
        .join(UnitDetail, UnitDetail.ServiceLogId == ServiceLog.Id, isouter=True) \
        .join(PlaceOfService, PlaceOfService.Id == UnitDetail.PlaceOfServiceId, isouter=True) \
        .join(SubProcedure, SubProcedure.Id == UnitDetail.SubProcedureId, isouter=True) \
        .join(PatientUnitDetail, PatientUnitDetail.UnitDetailId == UnitDetail.Id, isouter=True) \
        .join(ContractorServiceLog, ContractorServiceLog.ServiceLogId == ServiceLog.Id,
              isouter=True) \
        .filter(ServiceLog.Id == id) \
        .first()
    if db_report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    contractor_service_log = db.query(ContractorServiceLog).filter(ContractorServiceLog.ServiceLogId == id).first()
    company = db.query(Company).join(Payroll, Payroll.CompanyId ==Company.Id,isouter=True) \
                               .join(Contractor, Contractor.Id ==Payroll.ContractorId , isouter=True) \
                               .join(ServiceLog,ServiceLog.ContractorId ==Contractor.Id, isouter=True) \
                               .filter(ServiceLog.Id==id).first()
    pdf_bytes = create_pdf(BytesIO(), db_report, contractor_service_log,company)

    headers = {'Content-Disposition': f'inline;filename=sala_{db_report}.pdf'}

    return Response(content=pdf_bytes, media_type='application/pdf', headers=headers)


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
    c.line(420, 598, 570, 598)
    c.drawString(305, 600, "Therapist Signature:")
    c.line(40, 70, 550, 70)
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
             'Visit at\n(1)home\n(2)Comunity\n(3)School', 'Behavior\nTherapist\nInitials',
             'Caregiver/Client\nSignature']]

    for unitdetail in db_report.unitdetails:
        for patient_unit in unitdetail.patientunitdetail:
            formatted_date = datetime.strftime(patient_unit.unitdetailp.DateOfService, '%Y-%m-%d')
            entry_time = datetime.strptime(patient_unit.EntryTime, '%H:%M:%S')
            departure_time = datetime.strptime(patient_unit.DepartureTime, '%H:%M:%S')
            time_difference = departure_time - entry_time
            hours = time_difference
            signature = patient_unit.Signature
            # Decodificar la imagen en base64 y crear un objeto Image
            imagen_bytes = base64.b64decode(signature)
            # Crear el objeto Image
            imagen_reader = io.BytesIO(imagen_bytes)
            imagen = ReportLabImage(imagen_reader, width=0.7 * inch, height=0.3 * inch)
            data.append([formatted_date, patient_unit.EntryTime, patient_unit.DepartureTime,
                         patient_unit.unitdetailp.Unit, hours, patient_unit.unitdetailp.subprocedure.Name,
                         patient_unit.unitdetailp.placeofservice.Value, '', imagen])
    #
    t = Table(data, colWidths=[70] + [60] * 2 + [40] + [60] * 4 + [80])
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
    t.drawOn(c, 20, 450)

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
