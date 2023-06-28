
import tempfile
from io import BytesIO
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from fastapi import HTTPException
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from db_conection.settings import get_db
from models.schemas import ServiceLog, ContractorServiceLog, Contractor, ContractorType, PlaceOfService, Period, Client, \
    Payroll, Company, UnitDetail, PatientUnitDetail, SubProcedure, Agreement
from pdf_print import create_pdf
app = FastAPI()
# Cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





@app.get("/generar/{id}/pdf")
def read_report(id: int, db: Session = Depends(get_db)):
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
    #company = db.query(Company).join(Agreement, Agreement.CompanyId ==Company.Id,isouter=True) \
    #                            .join(Payroll, Payroll.Id == Agreement.PayrollId, isouter=True) \
    #                            .join(Contractor, Contractor.Id ==Payroll.ContractorId , isouter=True) \
    #                           .join(ServiceLog,ServiceLog.ContractorId ==Contractor.Id, isouter=True) \
    #                           .join(Client, Client.Id == ServiceLog.ClientId, isouter=True) \
    #                           .filter(ServiceLog.Id==id,).first()
    agreement = db.query(Agreement).join(ServiceLog, ServiceLog.ClientId == Agreement.ClientId) \
                                   .filter(ServiceLog.Id ==id).first()
    if agreement:
        company = db.query(Company).filter(Company.Id==agreement.CompanyId).first()
    else:
        raise Exception("Dont have company")
    pdf_bytes = create_pdf(BytesIO(), db_report, contractor_service_log,company)

    with open("pdf_report.pdf", mode="wb") as f:
        f.write(pdf_bytes)

    headers = {'Content-Disposition': f'inline;filename=sala_{db_report}.pdf'}

    return FileResponse("pdf_report.pdf",media_type='application/pdf', headers=headers)





if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
