from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import path_helpers

Base = declarative_base()


class TimeStamped(Base):
    __abstract__ = True
    created_time = Column(DateTime)
    modified_time = Column(DateTime)


class Serial(TimeStamped, Base):
    __tablename__ = 'perception_serial'
    id = Column(Integer, primary_key=True)
    controller_port_id = Column(String(128), nullable=True, unique=True, index=True)
    optix_version = Column(String(128), nullable=True)


class Sequence(TimeStamped, Base):
    __tablename__ = 'perception_sequence'
    id = Column(Integer, primary_key=True)
    name = Column(String(1024))
    capture_config_ids = Column(Text)
    controller_port_id = Column(String(128), nullable=True,
                                index=True)
    hardware_index = Column(Integer, nullable=True,
                            index=True)
    optix_version = Column(String(255))


class CaptureConfig(TimeStamped, Base):
    __tablename__ = 'perception_captureconfig'
    id = Column(Integer, primary_key=True)
    name = Column(String(1024))
    pattern = Column(Text)
    exposure_us = Column(Integer, default=0)
    optix_version = Column(String(255))
    wait_us = Column(Integer, default=0)


class OptixPerceptionDB:
    engine = create_engine(f'sqlite:///{path_helpers.OPTIX_DB_PATH.as_posix()}', echo=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    session.query()

    @classmethod
    def query_serial_by_controller_port_id(cls, controller_port_id):
        return cls.session.query(Serial).filter(Serial.controller_port_id == controller_port_id).all()

    @classmethod
    def query_capture_config_by_name(cls, name):
        return cls.session.query(CaptureConfig).filter(CaptureConfig.name == name).all()

    @classmethod
    def query_capture_config_by_names(cls, names):
        return cls.session.query(CaptureConfig).filter(CaptureConfig.name.in_(names)).all()

    @classmethod
    def query_sequence_by_name(cls, name):
        return cls.session.query(Sequence).filter(Sequence.name == name).all()

    @classmethod
    def query_sequence_by_name_and_port_id(cls, name, port_id):
        return cls.session.query(Sequence).filter(
            and_(Sequence.controller_port_id == port_id, Sequence.name == name)).all()

    @classmethod
    def query_sequence_by_port_id_and_hardware_index(cls, controller_port_id, hardware_index):
        return cls.session.query(Sequence).filter(
            and_(Sequence.controller_port_id == controller_port_id, Sequence.hardware_index == hardware_index)).all()
