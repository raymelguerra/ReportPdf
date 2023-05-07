from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


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

