from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Role:
    role_id: int
    role_name: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Role":
        return cls(role_id=d["role_id"], role_name=d["role_name"])


@dataclass
class Person:
    person_id: int
    first_name: str
    last_name: str
    full_name: str
    display_name: str
    email: str
    phone: str
    address: str
    city: str
    state: str
    zip: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Person":
        return cls(
            person_id=d["person_id"],
            first_name=d["first_name"],
            last_name=d["last_name"],
            full_name=d["full_name"],
            display_name=d["display_name"],
            email=d["email"],
            phone=d["phone"],
            address=d["address"],
            city=d["city"],
            state=d["state"],
            zip=d["zip"],
        )


@dataclass
class User:
    user_id: int
    username: str
    password: str
    role_id: int
    person_id: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "User":
        return cls(
            user_id=d["user_id"],
            username=d["username"],
            password=d["password"],
            role_id=d["role_id"],
            person_id=d["person_id"],
        )


@dataclass
class Employee:
    employee_id: int
    person_id: int
    position: str
    title: str
    manager_id: int
    start_date: str
    end_date: Optional[str]
    is_active: bool
    is_manager: bool

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Employee":
        return cls(
            employee_id=d["employee_id"],
            person_id=d["person_id"],
            position=d["position"],
            title=d["title"],
            manager_id=d["manager_id"],
            start_date=d["start_date"],
            end_date=d.get("end_date"),
            is_active=d["is_active"],
            is_manager=d["is_manager"],
        )


@dataclass
class Client:
    client_id: int
    employee_id: int
    description: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Client":
        return cls(
            client_id=d["client_id"],
            employee_id=d["employee_id"],
            description=d["description"],
        )


@dataclass
class SocialMediaAccount:
    social_media_id: int
    client_id: int
    account_type: str
    link: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SocialMediaAccount":
        return cls(
            social_media_id=d["social_media_id"],
            client_id=d["client_id"],
            account_type=d["account_type"],
            link=d["link"],
        )


@dataclass
class Brand:
    brand_id: int
    description: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Brand":
        return cls(brand_id=d["brand_id"], description=d["description"])


@dataclass
class BrandRepresentative:
    brand_rep_id: int
    person_id: int
    brand_id: int
    notes: str
    is_active: bool

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "BrandRepresentative":
        return cls(
            brand_rep_id=d["brand_rep_id"],
            person_id=d["person_id"],
            brand_id=d["brand_id"],
            notes=d["notes"],
            is_active=d["is_active"],
        )


@dataclass
class Deal:
    deal_id: int
    client_id: int
    brand_id: int
    brand_rep_id: int
    pitch_date: str
    is_active: bool
    is_successful: bool

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Deal":
        return cls(
            deal_id=d["deal_id"],
            client_id=d["client_id"],
            brand_id=d["brand_id"],
            brand_rep_id=d["brand_rep_id"],
            pitch_date=d["pitch_date"],
            is_active=d["is_active"],
            is_successful=d["is_successful"],
        )


@dataclass
class Contract:
    contract_id: int
    deal_id: int
    details: str
    payment: float
    agency_percentage: float
    start_date: str
    end_date: str
    status: str
    is_approved: bool

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Contract":
        return cls(
            contract_id=d["contract_id"],
            deal_id=d["deal_id"],
            details=d["details"],
            payment=d["payment"],
            agency_percentage=d["agency_percentage"],
            start_date=d["start_date"],
            end_date=d["end_date"],
            status=d["status"],
            is_approved=d["is_approved"],
        )
