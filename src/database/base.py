# coding: utf-8
# author: Wang Junfeng

import os
import json
import inspect
from enum import Enum
from sqlalchemy import (create_engine, Column, DateTime, Integer, String, Text, ARRAY, Float,
                        Boolean, ForeignKey, select, distinct)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.inspection import inspect as sql_inspect

from src.database import project_root_path
from log import formatted_logging


logger = formatted_logging.FormattedLogging(__name__).getLog()


Base = declarative_base()


class CommunicationType(Enum):
    # tecomX interaction handshake steps
    STATIC_SHOOTING = 0
    MOTION_SHOOTING = 1


class CommunicationStep(Enum):
    TWO_STEP = 2
    FOUR_STEP = 4


class DetectionDimension(Enum):
    TWO_D = 0
    TWO_POINT_FIVE_D = 1
    THREE_D = 2


# 基类，提供通用的删除和查询方法
class BaseOperations:
    @staticmethod
    def _handle_exception(session: Session, exception: Exception, context_data):
        """Handle exceptions and roll back session."""
        session.rollback()
        logger.error(f"Failed to process {context_data}: {exception}")

    @staticmethod
    def _records_to_dict(records):
        return {column.key: getattr(records, column.key) for column in sql_inspect(records).mapper.column_attrs}

    @classmethod
    def delete_data(cls, session: Session, data_id: int):
        """
        Delete a record from the table corresponding to the class.

        Args:
            session (Session): The SQLAlchemy session object.
            data_id (int): The id of the data record to be deleted.
        """
        try:
            # Retrieve the record
            record_to_delete = session.get(cls, data_id)
            if record_to_delete:
                session.delete(record_to_delete)
                session.commit()
                logger.info(f"{cls.__name__} deleted data successfully with id {data_id}.")
            else:
                logger.info(f"No {cls.__name__} found with id {data_id}.")
        except Exception as e:
            cls._handle_exception(session, e, data_id)

    @classmethod
    def query_data(cls, session: Session, data_dict: dict):
        """
        Query the table corresponding to the class based on a dictionary of filters.

        Args:
            session (Session): The SQLAlchemy session object.
            data_dict (dict): Dictionary of filter conditions, where keys are column names and values are the desired values.

        Returns:
            List: A list of records matching the filter conditions.
        """
        try:
            query = session.query(cls)  # Start building the query
            for key, value in data_dict.items():
                if hasattr(cls, key):  # Dynamically filter based on column names
                    column = getattr(cls, key)
                    # 如果列是字符串类型，则使用 LIKE 进行模糊匹配
                    if isinstance(column.type, String) and isinstance(value, str):
                        query = query.filter(column.like(f"%{value}%"))
                    else:
                        query = query.filter(column == value)

            results = query.all()  # Fetch all matching records

            return [cls._records_to_dict(record) for record in results]

        except Exception as e:
            cls._handle_exception(session, e, data_dict)


class IPCConfig(BaseOperations, Base):
    __tablename__ = "ipc_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    cpu = Column(String, nullable=False)
    gpus = Column(ARRAY(String), nullable=False)  # Array of strings
    ram = Column(String, nullable=False)
    ssds = Column(ARRAY(String), nullable=False)  # Array of strings
    software_version = Column(String, nullable=False)
    create_time = Column(DateTime, default=func.now())  # Automatically set on insert
    modified_time = Column(DateTime, default=func.now(), onupdate=func.now())  # Set and update on modification

    # Define relationship to IPCPerformance
    ipc_performance = relationship('IPCPerformance', back_populates='ipc_config', cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("name", "cpu", "gpus", "ram", "ssds", "software_version", name='uq_ipc_config'),)

    @classmethod
    def add_data(cls, session, data_dict):
        """
        Add new data to the IPCConfig table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to add.
        """
        try:
            # Create a new IPCConfig object
            new_ipc_config = IPCConfig(
                name=data_dict["name"],
                cpu=data_dict["cpu"],
                gpus=data_dict["gpus"],
                ram=data_dict["ram"],
                ssds=data_dict["ssds"],
                software_version=data_dict["software_version"],
            )

            session.add(new_ipc_config)
            session.commit()

            logger.info(f"{cls.__name__} add new data successfully id: {new_ipc_config.id}.")
            return new_ipc_config.id

        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to add data: {e}")

    @classmethod
    def update_data(cls, session, data_dict):
        """
        Update the IPCConfig table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to update. Must include 'id' to identify the row.
        """
        try:
            # Ensure 'id' exists in the dictionary
            if "id" not in data_dict:
                raise ValueError("The dictionary must contain an 'id' key to identify the record.")

            # Retrieve the record
            update_data = session.get(cls, data_dict["id"])
            if not update_data:
                raise NoResultFound(f"No {cls.__name__} found with id {data_dict['id']}")

            # Update fields dynamically
            for key, value in data_dict.items():
                if hasattr(update_data, key) and key != "id":
                    setattr(update_data, key, value)

            # Commit the changes
            session.add(update_data)
            session.commit()
            logger.info(f"{cls.__name__} with id {data_dict['id']} updated successfully.")

        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to update: {e}")

    # @classmethod
    # def delete_data(cls, session: Session, data_id: int):
    #     """
    #     Delete a record from the table corresponding to the class.
    #
    #     Args:
    #         session (Session): The SQLAlchemy session object.
    #         data_id (int): The id of the data record to be deleted.
    #     """
    #     try:
    #         # 查询IPCPerformance中是否有引用该IPCConfig的记录
    #         ipc_performance = session.query(IPCPerformance).filter(
    #             IPCPerformance.ipc_config_id == data_id).first()
    #
    #         if ipc_performance:
    #             # 如果找到引用，不能删除并给出提示
    #             logger.warning(f"IPCConfig with ID {data_id} is in use by IPCPerformance and cannot be deleted.")
    #         else:
    #             super().delete_data(session=session, data_id=data_id)
    #     except Exception as e:
    #         cls._handle_exception(session, e, data_id)


class ControllerConfig(BaseOperations, Base):
    __tablename__ = "controller_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    controller_id = Column(String, nullable=False)
    controller_version = Column(String, nullable=False)
    # 控制器连接的相机的ID，数组，因为V6最多可以连接2个相机
    cameras_id = Column(ARRAY(String), nullable=False)  # Array of String
    cameras_type = Column(ARRAY(String), nullable=False)  # Array of String
    image_width = Column(Integer, nullable=False)
    image_height = Column(Integer, nullable=False)
    image_channel = Column(Integer, nullable=True)
    capture_images_count = Column(Integer, nullable=False)
    network_inference_count = Column(Integer, nullable=False)
    create_time = Column(DateTime, default=func.now())  # Automatically set on insert
    modified_time = Column(DateTime, default=func.now(), onupdate=func.now())  # Set and update on modification

    # Define relationship to WorkstationConfig
    workstation_config = relationship('WorkstationConfig', back_populates='controller_config', cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint(
        "controller_id", "controller_version", "cameras_id", "cameras_type", "image_width", "image_height",
        "image_channel", "capture_images_count", "network_inference_count", name='uq_controller_config'),)

    @classmethod
    def add_data(cls, session, data_dict):
        """
        Add new data to the ControllerConfig table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to add.
        """
        try:
            new_controller_config = ControllerConfig(
                controller_id=data_dict["controller_id"],
                controller_version=data_dict["controller_version"],
                cameras_id=data_dict["cameras_id"],
                cameras_type=data_dict["cameras_type"],
                image_width=data_dict["image_width"],
                image_height=data_dict["image_height"],
                image_channel=data_dict.setdefault("image_channel", 3),
                capture_images_count=data_dict["capture_images_count"],
                network_inference_count=data_dict["network_inference_count"],
            )
            session.add(new_controller_config)
            session.commit()
            logger.info(f"{cls.__name__} add new data successfully id: {new_controller_config.id}.")
            return new_controller_config.id
        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to add data: {e}")

    @classmethod
    def update_data(cls, session, data_dict):
        """
        Update the ControllerConfig table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to update. Must include 'id' to identify the row.
        """
        try:
            # Ensure 'id' exists in the dictionary
            if "id" not in data_dict:
                raise ValueError("The dictionary must contain an 'id' key to identify the record.")

            # Retrieve the record
            update_data = session.get(cls, data_dict["id"])
            if not update_data:
                raise NoResultFound(f"No {cls.__name__} found with id {data_dict['id']}")

            # Update fields dynamically
            for key, value in data_dict.items():
                if hasattr(update_data, key) and key != "id":  # Ensure only valid attributes are updated
                    setattr(update_data, key, value)

            # Commit the changes
            session.add(update_data)
            session.commit()
            logger.info(f"{cls.__name__} updated successfully with id {data_dict['id']}.")

        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to update: {e}")

    @classmethod
    def query_data(cls, session: Session, data_dict: dict):
        """
        Query the table corresponding to the class based on a dictionary of filters.

        Args:
            session (Session): The SQLAlchemy session object.
            data_dict (dict): Dictionary of filter conditions, where keys are column names and values are the desired values.

        Returns:
            List: A list of records matching the filter conditions.
        """
        try:
            query = session.query(cls)  # Start building the query
            for key, value in data_dict.items():
                if hasattr(cls, key):  # Dynamically filter based on column names
                    column = getattr(cls, key)
                    # 特殊处理 cameras_type 数组
                    if key == "cameras_type" and isinstance(value, list):
                        # 使用 PostgreSQL 的 && 操作符检查数组是否有交集
                        query = query.filter(column.op('&&')(value))
                    # 如果列是字符串类型，则使用 LIKE 进行模糊匹配
                    elif isinstance(column.type, String) and isinstance(value, str):
                        query = query.filter(column.like(f"%{value}%"))
                    else:
                        query = query.filter(column == value)

            results = query.all()  # Fetch all matching records

            return [cls._records_to_dict(record) for record in results]

        except Exception as e:
            cls._handle_exception(session, e, data_dict)


class WorkstationConfig(BaseOperations, Base):
    __tablename__ = "workstation_config"
    id = Column(Integer, primary_key=True, autoincrement="auto")
    workstation_id = Column(Integer, nullable=False)
    # 工位连接的控制器的配置的ID
    controller_config_id=Column(Integer, ForeignKey('controller_config.id'), nullable=False)

    # 当前工位到下一个工位的距离-时间间隔，单位s如果当前工位是最后一个工位，则该距离是到part end的距离
    to_next_ws_offset = Column(Float, nullable=False)
    # 当前工位的控制器连接的相机的复位时间间隔，单位s,飞拍需要，定拍不需要。如果当前工位被选中，则需要设置，否则，不需要设置
    camera_reset_time = Column(Float, nullable=False)
    # 当前工位中的sequence数量
    sequence_count = Column(Integer, nullable=False)
    # 数组，当前PLC的工位需要触发的sequence的id，按照需要触发的先后顺序填写；
    # 如果sequence id 1的repeat=2,则其在数组中需要写2次，类似[…,1, 1, …]
    sequences_id = Column(ARRAY(Integer), nullable=False)  # Array of Integer
    # 数组，当前PLC的工位需要触发的sequence的时间间隔，即PLC需要触发的sequence的时间点位,单位ms，
    # 数组的第一个元素是first sequence delay，PLC需要触发的第一个sequence的时间间隔，
    # 第2个革元素是第一个sequence到第二个sequence之间的触发时间间隔；以此类推
    sequences_interval = Column(ARRAY(Integer), nullable=False)  # Array of Integer
    create_time = Column(DateTime, default=func.now())  # Automatically set on insert
    modified_time = Column(DateTime, default=func.now(), onupdate=func.now())  # Set and update on modification

    # Optional: Define a relationship
    controller_config = relationship('ControllerConfig', back_populates='workstation_config')

    __table_args__ = (UniqueConstraint(
        "workstation_id", "controller_config_id", "to_next_ws_offset", "camera_reset_time",
        "sequence_count", "sequences_id", "sequences_interval", name='uq_workstation_config'),)

    @classmethod
    def add_data(cls, session, data_dict):
        """
        Add new data to the WorkstationConfig table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to add.
        """
        try:
            new_workstation_config = WorkstationConfig(
                workstation_id=data_dict["workstation_id"],
                controller_config_id=data_dict["controller_config_id"],
                to_next_ws_offset=data_dict["to_next_ws_offset"],
                camera_reset_time=data_dict.setdefault("camera_reset_time", 0),
                sequence_count=data_dict["sequence_count"],
                sequences_id=data_dict["sequences_id"],
                sequences_interval=data_dict["sequences_interval"],
            )
            session.add(new_workstation_config)
            session.commit()
            logger.info(f"{cls.__name__} add new data successfully id: {new_workstation_config.id}.")
            return new_workstation_config.id
        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to add data: {e}")

    @classmethod
    def update_data(cls, session, data_dict):
        """
        Update the WorkstationConfig table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to update. Must include 'id' to identify the row.
        """
        try:
            # Ensure 'id' exists in the dictionary
            if "id" not in data_dict:
                raise ValueError("The dictionary must contain an 'id' key to identify the record.")

            # Retrieve the record
            update_data = session.get(cls, data_dict["id"])
            if not update_data:
                raise NoResultFound(f"No {cls.__name__} found with id {data_dict['id']}")

            # Update fields dynamically
            for key, value in data_dict.items():
                if hasattr(update_data, key) and key != "id":
                    setattr(update_data, key, value)

            # Commit the changes
            session.add(update_data)
            session.commit()
            logger.info(f"{cls.__name__} with id {data_dict['id']} updated successfully.")

        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to update: {e}")

    @classmethod
    def query_data(cls, session: Session, data_dict: dict):
        """
        Query the table corresponding to the class based on a dictionary of filters.

        Args:
            session (Session): The SQLAlchemy session object.
            data_dict (dict): Dictionary of filter conditions, where keys are column names and values are the desired values.

        Returns:
            List: A list of records matching the filter conditions.
        """
        try:
            query = session.query(cls).join(ControllerConfig)  # Start building the query
            for key, value in data_dict.items():
                if hasattr(cls, key):  # Dynamically filter based on column names
                    column = getattr(cls, key)
                    # 特殊处理 cameras_type 数组
                    if key == "cameras_type" and isinstance(value, list):
                        # 使用 PostgreSQL 的 && 操作符检查数组是否有交集
                        query = query.filter(column.op('&&')(value))
                    # 如果列是字符串类型，则使用 LIKE 进行模糊匹配
                    elif isinstance(column.type, String) and isinstance(value, str):
                        query = query.filter(column.like(f"%{value}%"))
                    else:
                        query = query.filter(column == value)

            results = query.all()  # Fetch all matching records
            return_result = []
            for workstation in results:
                result = {
                    "workstation_config": BaseOperations._records_to_dict(workstation),
                    "controller_config": BaseOperations._records_to_dict(workstation.controller_config)
                }
                return_result.append(result)

            return return_result

        except Exception as e:
            cls._handle_exception(session, e, data_dict)


class CommunicationConfig(BaseOperations, Base):
    __tablename__ = "communication_config"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 通讯的名，比如用于哪个项目的仿真
    name = Column(String, nullable=False)
    # 物料类型
    part_type = Column(String, nullable=False)
    # 物料时间间隔，单位S
    part_interval = Column(Float, nullable=False)
    # part start 到第一个工位的距离，用时间间隔表示，单位S
    part_start_to_ws1_interval = Column(Float, nullable=False)
    # 通讯的类型，定拍还是飞拍
    communication_type = Column(Integer, nullable=False)
    # 握手步数，设计支持2步和4步， 在定拍的时候需要，飞拍不需要
    communication_step = Column(Integer, nullable=True)
    # 使用的工位的数量
    workstation_count = Column(Integer, nullable=False)
    # 工位通信配置的id
    workstation_config_ids = Column(ARRAY(Integer), nullable=False)  # Array of Integer

    # bool数组，数组长度为6，如果使用全部6个工位，则填写
    # [True, True, True, True, True, True]；
    # 如果只是使用工位2,4,则填写
    # [False, True, False, True, False, False]
    workstations_in_use = Column(ARRAY(Boolean), nullable=False)  # Array of Integer
    create_time = Column(DateTime, default=func.now())  # Automatically set on insert
    modified_time = Column(DateTime, default=func.now(), onupdate=func.now())  # Set and update on modification

    __table_args__ = (UniqueConstraint(
        "name", "part_type", "part_interval", "part_start_to_ws1_interval", "communication_type",
        "communication_step", "workstation_count", "workstation_config_ids", "workstations_in_use",
        name='uq_communication_config'),)

    @classmethod
    def add_data(cls, session, data_dict):
        """
       Add new data to the CommunicationConfig table using a dictionary.

       Args:
           session: SQLAlchemy session object.
           data_dict: Dictionary containing fields to add.
       """
        try:
            workstation_ids = set(session.scalars(select(WorkstationConfig.id)).all())
            if all(workstation_id in workstation_ids for workstation_id in data_dict["workstation_config_ids"]):
                if data_dict["communication_type"] == CommunicationType.MOTION_SHOOTING.value:
                    data_dict["communication_step"] = CommunicationStep.TWO_STEP.value

                if (data_dict["communication_type"] == CommunicationType.STATIC_SHOOTING.value
                        and data_dict["communication_step"] not in CommunicationStep._value2member_map_):
                        logger.error(f"{inspect.currentframe().f_code.co_name} failed: data_dict[communication_step] "
                                     f"{data_dict['communication_step']} value not correct.")
                else:
                    new_communication_config = CommunicationConfig(
                        name=data_dict["name"],
                        part_type=data_dict["part_type"],
                        part_interval=data_dict["part_interval"],
                        part_start_to_ws1_interval=data_dict["part_start_to_ws1_interval"],
                        communication_type=data_dict["communication_type"],
                        communication_step=data_dict["communication_step"],
                        workstation_count=data_dict["workstation_count"],
                        workstation_config_ids=data_dict["workstation_config_ids"],
                        workstations_in_use=data_dict["workstations_in_use"],
                    )
                    session.add(new_communication_config)
                    session.commit()

                    logger.info(f"{cls.__name__} add new data successfully id: {new_communication_config.id}.")
                    return new_communication_config.id
            else:
                logger.error(f"{inspect.currentframe().f_code.co_name} failed: "
                             f"data_dict[workstation_config_ids] {data_dict['workstation_config_ids']} "
                             f"not all in WorkstationConfig.id {workstation_ids}")
        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to add data: {e}")

    @classmethod
    def update_data(cls, session, data_dict):
        """
        Update the CommunicationConfig table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to update. Must include 'id' to identify the row.
        """
        try:
            # Ensure 'id' exists in the dictionary
            if "id" not in data_dict:
                raise ValueError("The dictionary must contain an 'id' key to identify the record.")

            if data_dict["communication_type"] == CommunicationType.MOTION_SHOOTING.value:
                data_dict["communication_step"] = CommunicationStep.TWO_STEP.value

            if (data_dict["communication_type"] == CommunicationType.STATIC_SHOOTING.value
                    and data_dict["communication_step"] not in CommunicationStep._value2member_map_):
                raise ValueError(f"The dictionary communication_step {data_dict['communication_step']} not correct!.")

            # Retrieve the record
            update_data = session.get(cls, data_dict["id"])
            if not update_data:
                raise NoResultFound(f"No {cls.__name__}  found with id {data_dict['id']}")

            # Update fields dynamically
            for key, value in data_dict.items():
                if hasattr(update_data, key) and key != "id":
                    setattr(update_data, key, value)

            # Commit the changes
            session.add(update_data)
            session.commit()
            logger.info(f"{cls.__name__}  with id {data_dict['id']} updated successfully.")

        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to update: {e}")

    @classmethod
    def query_data(cls, session, data_dict):
        """
        Query the CommunicationConfig table based on a dictionary of filters.

        Args:
            session (Session): The SQLAlchemy session object.
            data_dict (dict): Dictionary of filter conditions, where keys are column names and values are the desired values.

        Returns:
            List[CommunicationConfig]: A list of CommunicationConfig objects matching the filter conditions.
        """
        try:
            # Step 1: Separate filters for CommunicationConfig and WorkstationConfig
            filter_communication = {}
            filter_workstation = {}

            for key, value in data_dict.items():
                if hasattr(CommunicationConfig, key):
                    filter_communication[key] = value
                elif hasattr(WorkstationConfig, key) or hasattr(ControllerConfig, key):
                    filter_workstation[key] = value

            # Step 2: Query CommunicationConfig based on filter_communication
            query = session.query(CommunicationConfig)
            for key, value in filter_communication.items():
                column = getattr(CommunicationConfig, key)
                query = query.filter(column == value)

            queried_communication_configs = query.all()

            # Step 3: Query WorkstationConfig based on filter_workstation
            query = session.query(WorkstationConfig).join(ControllerConfig)
            for key, value in filter_workstation.items():
                if hasattr(WorkstationConfig, key):
                    column = getattr(WorkstationConfig, key)
                else:
                    column = getattr(ControllerConfig, key)
                query = query.filter(column == value)

            queried_workstation_configs = WorkstationConfig.query_data(session, filter_workstation)
            queried_workstation_config_ids = {ws["workstation_config"]["id"] for ws in queried_workstation_configs}

            # Step 4: Filter CommunicationConfig based on WorkstationConfig
            filtered_communication_configs = []
            for comm_config in queried_communication_configs:
                if set(comm_config.workstation_config_ids).issubset(queried_workstation_config_ids):
                    result = {"communication_config": (BaseOperations._records_to_dict(comm_config)),
                              "workstation_configs": []}
                    for workstation_config_id in comm_config.workstation_config_ids:
                        result["workstation_configs"].extend(
                            WorkstationConfig.query_data(session, {"id": workstation_config_id})
                        )
                    filtered_communication_configs.append(result)

            return filtered_communication_configs

        except Exception as e:
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to query: {e}")


class IPCPerformance(BaseOperations, Base):
    __tablename__ = "ipc_performance"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # ForeignKey references ipc_config.id
    ipc_config_id=Column(Integer, ForeignKey('ipc_config.id'))
    # ForeignKey references simulation_result.id
    simulation_result_id=Column(Integer, ForeignKey('simulation_result.id'))

    # IPC 上运行的模型信息
    model_size = Column(String, nullable=False)
    network_architecture = Column(String, nullable=False)

    # IPC性能和资源消耗
    cpu_usage_avg = Column(Float, nullable=False)
    gpus_usage_avg = Column(ARRAY(Float), nullable=False)  # Array of Float
    gpus_memory_usage_avg = Column(ARRAY(Float), nullable=False)  # Array of Float
    memory_usage_avg = Column(Float, nullable=False)
    disk_usage_avg = Column(Float, nullable=False)
    disk_read_speed_avg = Column(Float, nullable=False)
    disk_write_speed_avg = Column(Float, nullable=False)
    create_time = Column(DateTime, default=func.now())  # Automatically set on insert
    modified_time = Column(DateTime, default=func.now(), onupdate=func.now())  # Set and update on modification

    # Optional: Define a relationship
    ipc_config = relationship('IPCConfig', back_populates='ipc_performance')
    simulation_result = relationship('SimulationResult', back_populates='ipc_performance')

    __table_args__ = (UniqueConstraint(
        "ipc_config_id", "simulation_result_id", "model_size", "network_architecture", "cpu_usage_avg",
        "gpus_usage_avg", "gpus_memory_usage_avg", "memory_usage_avg", "disk_usage_avg", "disk_read_speed_avg",
        "disk_write_speed_avg", name='uq_ipc_performance'),)

    @classmethod
    def add_data(cls, session, data_dict):
        """
        Add new data to the IPCPerformance table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to add.
        """
        try:
            new_ipc_performance = IPCPerformance(
                # ForeignKey references ipc_config.id
                ipc_config_id=data_dict["ipc_config_id"],
                # ForeignKey references simulation_result.id
                simulation_result_id=data_dict["simulation_result_id"],
                # IPC 上运行的模型信息
                model_size=data_dict["model_size"],
                network_architecture=data_dict["network_architecture"],
                # IPC性能和资源消耗
                cpu_usage_avg=data_dict["cpu_usage_avg"],
                gpus_usage_avg=data_dict["gpus_usage_avg"],
                gpus_memory_usage_avg=data_dict["gpus_memory_usage_avg"],
                memory_usage_avg=data_dict["memory_usage_avg"],
                disk_usage_avg=data_dict["disk_usage_avg"],
                disk_read_speed_avg=data_dict["disk_read_speed_avg"],
                disk_write_speed_avg=data_dict["disk_write_speed_avg"],
            )
            session.add(new_ipc_performance)

            session.flush()

            # 更新 SimulationResult.ipc_performance_ids
            simulation_result = session.query(SimulationResult).get(new_ipc_performance.simulation_result_id)
            if simulation_result:
                if simulation_result.ipc_performance_ids is None:
                    simulation_result.ipc_performance_ids = []
                updated_list = simulation_result.ipc_performance_ids + [new_ipc_performance.id]
                seen = set()
                unique_list = [x for x in updated_list if not (x in seen or seen.add(x))]
                simulation_result.ipc_performance_ids = unique_list  # 显式赋值
            session.commit()

            logger.info(f"{cls.__name__} add new data successfully id: {new_ipc_performance.id}.")
            return new_ipc_performance.id
        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to add data: {e}")

    @classmethod
    def update_data(cls, session, data_dict):
        """
        Update the IPCPerformance table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to update. Must include 'id' to identify the row.
        """
        try:
            # Ensure 'id' exists in the dictionary
            if "id" not in data_dict:
                raise ValueError("The dictionary must contain an 'id' key to identify the record.")

            # Retrieve the record
            update_data = session.get(cls, data_dict["id"])
            if not update_data:
                raise NoResultFound(f"No {cls.__name__} found with id {data_dict['id']}")

            # Update fields dynamically
            for key, value in data_dict.items():
                if hasattr(update_data, key) and key != "id":
                    setattr(update_data, key, value)

            # Commit the changes
            session.add(update_data)
            session.commit()
            logger.info(f"{cls.__name__} with id {data_dict['id']} updated successfully.")

        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to update: {e}")

    @classmethod
    def query_data(cls, session: Session, data_dict: dict):
        """
        Query the table corresponding to the class based on a dictionary of filters.

        Args:
            session (Session): The SQLAlchemy session object.
            data_dict (dict): Dictionary of filter conditions, where keys are column names and values are the desired values.

        Returns:
            List: A list of records matching the filter conditions.
        """
        try:
            query = session.query(cls).join(IPCConfig)  # Start building the query
            for key, value in data_dict.items():
                if hasattr(cls, key):  # Dynamically filter based on column names
                    column = getattr(cls, key)
                    # 如果列是字符串类型，则使用 LIKE 进行模糊匹配
                    if isinstance(column.type, String) and isinstance(value, str):
                        query = query.filter(column.like(f"%{value}%"))
                    else:
                        query = query.filter(column == value)

            results = query.all()  # Fetch all matching records

            return_result = []
            for performance in results:
                result = {
                    "ipc_performance": (BaseOperations._records_to_dict(performance)),
                    "ipc_config": BaseOperations._records_to_dict(performance.ipc_config)
                }
                return_result.append(result)
            return return_result

        except Exception as e:
            cls._handle_exception(session, e, data_dict)

    @classmethod
    def delete_data(cls, session: Session, data_id: int):
        """
        Delete a record from the table corresponding to the class.

        Args:
            session (Session): The SQLAlchemy session object.
            data_id (int): The id of the data record to be deleted.
        """
        try:
            # 查询IPCPerformance中是否有引用该IPCConfig的记录
            simulation_result = session.query(SimulationResult).filter(
                SimulationResult.ipc_performance_ids.any(data_id)).first()

            if simulation_result:
                # 如果找到引用，不能删除并给出提示
                logger.warning(f"IPCPerformance with ID {data_id} is in use by SimulationResult and cannot be deleted.")
            else:
                super().delete_data(session=session, data_id=data_id)
        except Exception as e:
            cls._handle_exception(session, e, data_id)


class SimulationResult(BaseOperations, Base):
    __tablename__ = "simulation_result"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 当前有2D，2.5D，未来可能会有3D
    detection_dimension = Column(Integer, nullable=True)
    part_type = Column(String, nullable=False)
    # 物料时间间隔，单位S
    part_interval = Column(Float, nullable=False)
    # 单个物料需要拍摄的图片总数量
    total_image_count = Column(Integer, nullable=False)
    # 单个物料的图片需要推理的总次数
    total_inference_count = Column(Integer, nullable=False)
    ng_type_count = Column(Integer, nullable=False)
    each_ng_type_defect_count = Column(Integer, nullable=False)

    # IPC的个数, 当前遇到过一台IPC无法满足性能的项目，在设计数据库时需要考虑这种情况
    ipc_count = Column(Integer, nullable=False)
    # IPC的硬件配置表ID, 数组，数组中的元素是IPC配置表中的ID
    ipcs_config_id = Column(ARRAY(Integer), nullable=False)  # Array of Integer
    # PLC触发程序的配置，包括控制器，相机，sequence以及工位之间的距离
    communication_config_ids = Column(ARRAY(Integer), nullable=False)  # Array of Integer

    # 是否开启了存图，默认开启
    is_image_saving = Column(Boolean, nullable=False)
    # 测试的物料总数量
    part_count = Column(Integer, nullable=False)
    # 测试的总用时
    total_time_used = Column(Float, nullable=False)
    fps = Column(Float, nullable=False)
    mps = Column(Float, nullable=False)

    # 物料处理用时
    max_part_use_time = Column(Float, nullable=False)
    min_part_use_time = Column(Float, nullable=False)
    avg_part_use_time = Column(Float, nullable=False)
    max_image_capture_time = Column(Float, nullable=False)
    min_image_capture_time = Column(Float, nullable=False)
    avg_image_capture_time = Column(Float, nullable=False)
    max_cortex_infer_time = Column(Float, nullable=False)
    min_cortex_infer_time = Column(Float, nullable=False)
    avg_cortex_infer_time = Column(Float, nullable=False)
    max_25d_mean_time = Column(Float, nullable=True)
    min_25d_mean_time = Column(Float, nullable=True)
    avg_25d_mean_time = Column(Float, nullable=True)
    max_25d_normal_time = Column(Float, nullable=True)
    min_25d_normal_time = Column(Float, nullable=True)
    avg_25d_normal_time = Column(Float, nullable=True)
    max_25d_height_time = Column(Float, nullable=True)
    min_25d_height_time = Column(Float, nullable=True)
    avg_25d_height_time = Column(Float, nullable=True)

    # IPC性能和资源消耗
    ipc_performance_ids = Column(ARRAY(Integer), nullable=False)  # Array of Integer
    # IPC 的核心分配
    core_allocation = Column(Text, nullable=False)

    create_time = Column(DateTime, default=func.now())  # Automatically set on insert
    modified_time = Column(DateTime, default=func.now(), onupdate=func.now())  # Set and update on modification

    # Define relationship to IPCPerformance
    ipc_performance = relationship('IPCPerformance', back_populates='simulation_result', cascade="all, delete-orphan")

    @classmethod
    def add_data(cls, session, data_dict):
        """
        Add new data to the SimulationResult table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to add.
        """
        try:
            # 删除表中的所有数据
            # self.session.query(SimulationResult).delete()
            # self.session.commit()

            communication_config_ids = set(session.scalars(select(CommunicationConfig.id)).all())
            if all(item in communication_config_ids for item in data_dict["communication_config_ids"]):
                if data_dict.setdefault("detection_dimension", 0) == DetectionDimension.TWO_D.value:
                    data_dict.setdefault("max_25d_mean_time", 0),
                    data_dict.setdefault("min_25d_mean_time", 0),
                    data_dict.setdefault("avg_25d_mean_time", 0),
                    data_dict.setdefault("max_25d_normal_time", 0),
                    data_dict.setdefault("min_25d_normal_time", 0),
                    data_dict.setdefault("avg_25d_normal_time", 0),
                    data_dict.setdefault("max_25d_height_time", 0),
                    data_dict.setdefault("min_25d_height_time", 0),
                    data_dict.setdefault("avg_25d_height_time", 0),

                new_communication_result = SimulationResult(
                    # part information
                    detection_dimension=data_dict["detection_dimension"],
                    part_type=data_dict["part_type"],
                    part_interval=data_dict["part_interval"],
                    total_image_count=data_dict["total_image_count"],
                    total_inference_count=data_dict["total_inference_count"],
                    ng_type_count=data_dict["ng_type_count"],
                    each_ng_type_defect_count=data_dict["each_ng_type_defect_count"],

                    # ipc information
                    ipc_count=data_dict["ipc_count"],
                    ipcs_config_id=data_dict["ipcs_config_id"],
                    # communication information
                    communication_config_ids=data_dict["communication_config_ids"],
                    is_image_saving=data_dict["is_image_saving"],

                    # ipc process result
                    part_count=data_dict["part_count"],
                    total_time_used=data_dict["total_time_used"],
                    fps=data_dict["fps"],
                    mps=data_dict["mps"],

                    max_part_use_time=data_dict["max_part_use_time"],
                    min_part_use_time=data_dict["min_part_use_time"],
                    avg_part_use_time=data_dict["avg_part_use_time"],
                    max_image_capture_time=data_dict["max_image_capture_time"],
                    min_image_capture_time=data_dict["min_image_capture_time"],
                    avg_image_capture_time=data_dict["avg_image_capture_time"],
                    max_cortex_infer_time=data_dict["max_cortex_infer_time"],
                    min_cortex_infer_time=data_dict["min_cortex_infer_time"],
                    avg_cortex_infer_time=data_dict["avg_cortex_infer_time"],
                    # 2.5D project use
                    max_25d_mean_time=data_dict["max_25d_mean_time"],
                    min_25d_mean_time=data_dict["min_25d_mean_time"],
                    avg_25d_mean_time=data_dict["avg_25d_mean_time"],
                    max_25d_normal_time=data_dict["max_25d_normal_time"],
                    min_25d_normal_time=data_dict["min_25d_normal_time"],
                    avg_25d_normal_time=data_dict["avg_25d_normal_time"],
                    max_25d_height_time=data_dict["max_25d_height_time"],
                    min_25d_height_time=data_dict["min_25d_height_time"],
                    avg_25d_height_time=data_dict["avg_25d_height_time"],

                    ipc_performance_ids=data_dict["ipc_performance_ids"],
                    core_allocation=data_dict["core_allocation"],
                )
                session.add(new_communication_result)
                session.commit()
                logger.info(f"{cls.__name__} add new data successfully id: {new_communication_result.id}.")
                return new_communication_result.id
            else:
                logger.error(f"{inspect.currentframe().f_code.co_name} failed: "
                             f"data_dict[communication_config_ids] {data_dict['communication_config_ids']} "
                             f"not all in CommunicationConfig.id {communication_config_ids}")
        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to add data: {e}")

    @classmethod
    def update_data(cls, session, data_dict):
        """
        Update the SimulationResult table using a dictionary.

        Args:
            session: SQLAlchemy session object.
            data_dict: Dictionary containing fields to update. Must include 'id' to identify the row.
        """
        try:
            # Ensure 'id' exists in the dictionary
            if "id" not in data_dict:
                raise ValueError("The dictionary must contain an 'id' key to identify the record.")
            if data_dict.setdefault("detection_dimension", 0) not in DetectionDimension._value2member_map_:
                raise ValueError(f"The dictionary detection_dimension {data_dict['detection_dimension']} not correct!.")

            # Retrieve the record
            update_data = session.get(cls, data_dict["id"])
            if not update_data:
                raise NoResultFound(f"No {cls.__name__} found with id {data_dict['id']}")

            # Update fields dynamically
            for key, value in data_dict.items():
                if hasattr(update_data, key) and key != "id":  # Ensure only valid attributes are updated
                    setattr(update_data, key, value)

            # Commit the changes
            session.add(update_data)
            session.commit()
            logger.info(f"{cls.__name__} with id {data_dict['id']} updated successfully.")

        except Exception as e:
            session.rollback()
            logger.error(f"{cls.__name__} {inspect.currentframe().f_code.co_name} Failed to update: {e}")

    @classmethod
    def query_data(cls, session: Session, data_dict: dict):
        """
        Query the table corresponding to the class based on a dictionary of filters.

        Args:
            session (Session): The SQLAlchemy session object.
            data_dict (dict): Dictionary of filter conditions, where keys are column names and values are the desired values.

        Returns:
            List: A list of records matching the filter conditions.
        """
        try:
            # Step 1: Separate filters for SimulationResult and CommunicationConfig
            filter_simulation = {}
            filter_communication = {}
            filter_ipc_config = {}

            for key, value in data_dict.items():
                if hasattr(SimulationResult, key) or hasattr(IPCPerformance, key):
                    filter_simulation[key] = value
                elif hasattr(WorkstationConfig, key) or hasattr(ControllerConfig, key) or hasattr(CommunicationConfig, key):
                    filter_communication[key] = value
                elif hasattr(IPCConfig, key):
                    filter_ipc_config[key] = value

            # Step 2: Query SimulationResult based on filter_simulation
            query = session.query(cls).join(IPCPerformance).join(IPCConfig)  # Start building the query
            for key, value in filter_simulation.items():
                if hasattr(cls, key):  # Dynamically filter based on column names
                    column = getattr(cls, key)
                    # 如果列是字符串类型，则使用 LIKE 进行模糊匹配
                    if isinstance(column.type, String) and isinstance(value, str):
                        query = query.filter(column.like(f"%{value}%"))
                    else:
                        query = query.filter(column == value)

            queried_simulation_results = query.all() # Fetch all matching records
            filtered_queried_simulation_results = []
            for simulation_result in queried_simulation_results:
                query_ipc_config_data = []
                for ipc_config_id in simulation_result.ipcs_config_id:
                    query_ipc_config_data_dict = {"id": ipc_config_id}
                    query_ipc_config_data_dict.update(filter_ipc_config)
                    query_data = IPCConfig.query_data(session, data_dict=query_ipc_config_data_dict)
                    query_ipc_config_data.extend(query_data)
                if query_ipc_config_data:
                    filtered_queried_simulation_results.append(simulation_result)
            queried_simulation_results = filtered_queried_simulation_results

            # Step 3: Query CommunicationConfig based on filter_communication
            queried_communication_configs = CommunicationConfig.query_data(session, filter_communication)
            queried_communication_config_ids = {ws["communication_config"]["id"] for ws in queried_communication_configs}


            # Step 4: Filter SimulationResult based on                 elif hasattr(WorkstationConfig, key) or hasattr(ControllerConfig, key) or hasattr(CommunicationConfig, key):
            filtered_simulation_results = []
            for simulation_result in queried_simulation_results:
                if set(simulation_result.communication_config_ids).issubset(queried_communication_config_ids):
                    result = {
                        "simulation_result": (BaseOperations._records_to_dict(simulation_result)),
                        "ipc_performances": [],
                        "communication_configs": [],
                    }
                    for perf in simulation_result.ipc_performance:
                        result["ipc_performances"].append(
                            {
                                "ipc_performance": BaseOperations._records_to_dict(perf),
                                "ipc_config": BaseOperations._records_to_dict(perf.ipc_config)
                             }
                        )
                    for com_id in simulation_result.communication_config_ids:
                        result["communication_configs"].extend(CommunicationConfig.query_data(session, {"id": com_id}))
                    filtered_simulation_results.append(result)
            return filtered_simulation_results

        except Exception as e:
            cls._handle_exception(session, e, data_dict)


class TableFactory:
    """工厂类，动态获取 Table 处理类"""
    TABLE_MAPPING = {
        "ipc_config": IPCConfig,
        "controller_config": ControllerConfig,
        "workstation_config": WorkstationConfig,
        "communication_config": CommunicationConfig,
        "ipc_performance": IPCPerformance,
        "simulation_result": SimulationResult,
    }

    @classmethod
    def get_table(cls, table_name):
        table_class = cls.TABLE_MAPPING.get(table_name)
        if not table_class:
            raise ValueError(f"Table {table_name} not existed!")
        return table_class


class ConfigurableSimulationSystemDB:
    json_file = os.path.abspath(os.path.join(project_root_path, "config/settings.json"))
    with open(json_file, "r") as f:
        database_settings = json.load(f)
    database_url = (f"postgresql://{database_settings['USERNAME']}:{database_settings['PASSWORD']}"
                    f"@{database_settings['LOCAL_HOST']}/{database_settings['DATABASE_NAME']}")

    def __init__(self):
        self.engine = self.init_database()
        self.init_table()
        self.session_maker = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.session_maker()

    def init_database(self):
        if not database_exists(self.database_url):
            create_database(self.database_url)
        return create_engine(self.database_url)

    def init_table(self):
        Base.metadata.create_all(bind=self.engine)

    def get_db(self):
        db = self.session_maker()
        try:
            yield db
        finally:
            db.close()

    def add_data(self, table_name, data_dict):
        try:
            table_class = TableFactory.get_table(table_name)
            if not table_class:
                raise Exception(f"Table {table_name} does not exist!")

            new_data_id = table_class.add_data(session=self.session, data_dict=data_dict)
            return new_data_id

        except KeyError as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} failed {e}")
        except IntegrityError:
            self.session.rollback()
            logger.warning(f"Duplicate entry detected table {table_name} {data_dict}.")
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} failed {e}")

    def update_data(self, table_name, data_dict):
        try:
            table_class = TableFactory.get_table(table_name)
            if not table_class:
                raise Exception(f"Table {table_name} does not exist!")

            table_class.update_data(session=self.session, data_dict=data_dict)

        except KeyError as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} failed {e}")
        except IntegrityError:
            self.session.rollback()
            logger.warning(f"Duplicate entry detected table {table_name} {data_dict}.")
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} failed {e}")

    def query_data(self, table_name, data_dict):
        try:
            table_class = TableFactory.get_table(table_name)
            if not table_class:
                raise Exception(f"Table {table_name} does not exist!")

            query_data = table_class.query_data(session=self.session, data_dict=data_dict)
            return query_data

        except KeyError as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} failed {e}")
        except IntegrityError:
            logger.warning(f"Duplicate entry detected table {table_name} {data_dict}.")
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} failed {e}")

    def delete_data(self, table_name, data_id):
        try:
            table_class = TableFactory.get_table(table_name)
            if not table_class:
                raise Exception(f"Table {table_name} does not exist!")

            table_class.delete_data(session=self.session, data_id=data_id)

        except KeyError as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} failed {e}")
        except IntegrityError:
            self.session.rollback()
            logger.warning(f"Duplicate entry detected table {table_name} {data_id}.")
        except Exception as e:
            logger.error(f"{inspect.currentframe().f_code.co_name} failed {e}")

    def get_all_controller_ids(self):
        """
        return the controller_config table id and the controller id
        :return: [(controller_config_id, controller_id),]
        """
        results = self.session.query(ControllerConfig.id, ControllerConfig.controller_id).all()
        return [(result.id, result.controller_id) for result in results]

    def get_used_controller_ids(self):
        controller_ids = self.session.query(WorkstationConfig.controller_config_id).distinct().all()
        return [cid[0] for cid in controller_ids]  # 转换成 ID 列表

    def is_controller_used(self, controller_id: int):
        return self.session.query(WorkstationConfig).filter_by(controller_config_id=controller_id).first() is not None

    def get_controller_usage(self):
        # 列表 [(controller_id, workstation_id), ...]
        results = self.session.query(
            ControllerConfig.id, WorkstationConfig.id
        ).join(WorkstationConfig, ControllerConfig.id == WorkstationConfig.controller_config_id).all()

        return results

    def get_used_cpu(self):
        # 查询去重后的CPU和GPU配置
        results = self.session.query(distinct(IPCConfig.cpu)).join(
            IPCPerformance, IPCPerformance.ipc_config_id == IPCConfig.id
        ).join(
            SimulationResult, SimulationResult.ipc_performance_ids.any(IPCPerformance.id)
        ).all()

        return [cpu for (cpu,) in results]

    def get_used_gpus(self):
        # 查询去重的gpus信息
        result = self.session.query(distinct(IPCConfig.gpus)).join(
            IPCPerformance, IPCPerformance.ipc_config_id == IPCConfig.id
        ).join(
            SimulationResult, SimulationResult.ipc_performance_ids.any(IPCPerformance.id)
        ).all()

        # 返回结果中的GPU列表
        return [gpus for (gpus,) in result]





