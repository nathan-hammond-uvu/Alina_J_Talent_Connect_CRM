"""SQLAlchemy ORM database models for Talent Connect CRM.

These models reflect the current (post-migration) schema:
  - Creator  (formerly Client)
  - BrandContact  (formerly BrandRepresentative)

Each model maps to a relational table and can be used with any
SQLAlchemy-supported database (SQLite, PostgreSQL, etc.).

Usage::

    from crm.persistence.db_models import Base, engine
    Base.metadata.create_all(engine)
"""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all CRM ORM models."""


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------

class RoleModel(Base):
    """Maps to the ``roles`` table.

    Columns:
        role_id   – primary key
        role_name – e.g. "Admin", "Manager", "Employee", "User"
    """
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(100), nullable=False)

    users = relationship("UserModel", back_populates="role", lazy="dynamic")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Role {self.role_id}: {self.role_name}>"


# ---------------------------------------------------------------------------
# Person
# ---------------------------------------------------------------------------

class PersonModel(Base):
    """Maps to the ``persons`` table.

    A Person holds contact / identity information shared by Users, Employees,
    Creators, and Brand Contacts.
    """
    __tablename__ = "persons"

    person_id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False, default="")
    last_name = Column(String(100), nullable=False, default="")
    full_name = Column(String(200), nullable=False, default="")
    display_name = Column(String(200), nullable=False, default="")
    email = Column(String(200), nullable=False, default="")
    phone = Column(String(50), nullable=False, default="")
    address = Column(String(200), nullable=False, default="")
    city = Column(String(100), nullable=False, default="")
    state = Column(String(50), nullable=False, default="")
    zip = Column(String(20), nullable=False, default="")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Person {self.person_id}: {self.full_name}>"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserModel(Base):
    """Maps to the ``users`` table.

    Foreign keys:
        role_id   → roles.role_id
        person_id → persons.person_id
    """
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(500), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=True)
    person_id = Column(Integer, ForeignKey("persons.person_id"), nullable=True)

    role = relationship("RoleModel", back_populates="users")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.user_id}: {self.username}>"


# ---------------------------------------------------------------------------
# Employee
# ---------------------------------------------------------------------------

class EmployeeModel(Base):
    """Maps to the ``employees`` table.

    Foreign keys:
        person_id → persons.person_id
    """
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.person_id"), nullable=True)
    position = Column(String(200), nullable=False, default="")
    title = Column(String(200), nullable=False, default="")
    manager_id = Column(Integer, nullable=True, default=0)
    start_date = Column(String(20), nullable=False, default="")
    end_date = Column(String(20), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_manager = Column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Employee {self.employee_id}: {self.position}>"


# ---------------------------------------------------------------------------
# Creator  (formerly Client)
# ---------------------------------------------------------------------------

class CreatorModel(Base):
    """Maps to the ``creators`` table (formerly ``clients``).

    Foreign keys:
        person_id   → persons.person_id  (nullable; resolved at creation time)
        employee_id → employees.employee_id  (nullable; the managing employee)
    """
    __tablename__ = "creators"

    creator_id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.person_id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    description = Column(Text, nullable=False, default="")

    social_media_accounts = relationship(
        "SocialMediaAccountModel", back_populates="creator", lazy="dynamic"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Creator {self.creator_id}>"


# ---------------------------------------------------------------------------
# SocialMediaAccount
# ---------------------------------------------------------------------------

class SocialMediaAccountModel(Base):
    """Maps to the ``social_media_accounts`` table.

    Foreign keys:
        creator_id → creators.creator_id  (nullable)
    """
    __tablename__ = "social_media_accounts"

    social_media_id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("creators.creator_id"), nullable=True)
    account_type = Column(String(100), nullable=False, default="")
    link = Column(String(500), nullable=False, default="")

    creator = relationship("CreatorModel", back_populates="social_media_accounts")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SocialMediaAccount {self.social_media_id}: {self.account_type}>"


# ---------------------------------------------------------------------------
# Brand
# ---------------------------------------------------------------------------

class BrandModel(Base):
    """Maps to the ``brands`` table."""
    __tablename__ = "brands"

    brand_id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, default="")
    industry = Column(String(200), nullable=False, default="")
    website = Column(String(500), nullable=False, default="")
    notes = Column(Text, nullable=False, default="")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Brand {self.brand_id}: {self.name}>"


# ---------------------------------------------------------------------------
# BrandContact  (formerly BrandRepresentative)
# ---------------------------------------------------------------------------

class BrandContactModel(Base):
    """Maps to the ``brand_contacts`` table (formerly ``brand_representatives``).

    Foreign keys:
        person_id → persons.person_id  (nullable)
    """
    __tablename__ = "brand_contacts"

    brand_contact_id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("persons.person_id"), nullable=True)
    brand_id = Column(Integer, nullable=True, default=0)
    notes = Column(Text, nullable=False, default="")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<BrandContact {self.brand_contact_id}>"


# ---------------------------------------------------------------------------
# Deal
# ---------------------------------------------------------------------------

class DealModel(Base):
    """Maps to the ``deals`` table.

    Uses the current (post-migration) field names ``creator_id`` and
    ``brand_contact_id`` (formerly ``client_id`` / ``brand_rep_id``).
    """
    __tablename__ = "deals"

    deal_id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, nullable=True)       # formerly client_id
    brand_id = Column(Integer, nullable=True)
    brand_contact_id = Column(Integer, nullable=True)  # formerly brand_rep_id
    pitch_date = Column(String(20), nullable=False, default="")
    is_active = Column(Boolean, nullable=False, default=True)
    is_successful = Column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Deal {self.deal_id}>"


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

class ContractModel(Base):
    """Maps to the ``contracts`` table."""
    __tablename__ = "contracts"

    contract_id = Column(Integer, primary_key=True)
    deal_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=False, default="")
    payment = Column(Float, nullable=False, default=0.0)
    agency_percentage = Column(Float, nullable=False, default=0.0)
    start_date = Column(String(20), nullable=False, default="")
    end_date = Column(String(20), nullable=False, default="")
    status = Column(String(50), nullable=False, default="")
    is_approved = Column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Contract {self.contract_id}>"


# ---------------------------------------------------------------------------
# Setting  (key/value store for ACM and internal metadata)
# ---------------------------------------------------------------------------

class SettingModel(Base):
    """Maps to the ``settings`` table.

    Stores JSON-encoded values by string key.  Used for:
    - ``access_control_matrix``  – the ACM dict (JSON)
    - ``_next_id``               – global auto-increment counter (JSON int)
    - ``last_import_at``         – ISO-8601 timestamp of last data import
    """
    __tablename__ = "settings"

    key = Column(String(200), primary_key=True)
    value = Column(Text, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Setting {self.key}>"
