"""Pydantic request models + validation-error mapping."""
from datetime import date
from typing import Annotated, Literal, Optional

from pydantic import (
    BaseModel, EmailStr, Field, ValidationError, field_validator, model_validator,
)

from .helpers import PHONE_RE, err


Species = Literal["dog", "cat"]


class CitizenRegistration(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=200)]
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    county: Annotated[str, Field(pattern=r"^[A-Z]{1,2}$")]
    locality: Annotated[str, Field(min_length=1, max_length=200)]
    species: Annotated[list[Species], Field(min_length=1)]
    dog_count: Optional[int] = Field(default=None, ge=0, le=50, alias="dogCount")
    cat_count: Optional[int] = Field(default=None, ge=0, le=50, alias="catCount")
    gdpr_consent: Literal[True] = Field(alias="gdprConsent")
    turnstile_token: Annotated[str, Field(min_length=1, alias="turnstileToken")]

    model_config = {"populate_by_name": True, "str_strip_whitespace": True}

    @field_validator("phone")
    @classmethod
    def _valid_phone(cls, v):
        if v and not PHONE_RE.match(v):
            raise ValueError("invalid phone format")
        return v

    @model_validator(mode="after")
    def _phone_or_email(self):
        if not self.phone and not self.email:
            raise ValueError("phone or email required")
        return self


class CampaignSubmission(BaseModel):
    organization_name: Annotated[str, Field(min_length=1, max_length=200, alias="organizationName")]
    contact_email: EmailStr = Field(alias="contactEmail")
    contact_phone: Annotated[str, Field(min_length=7, max_length=20, alias="contactPhone")]
    phone_public: Annotated[str, Field(min_length=7, max_length=20, alias="phonePublic")]
    county: Annotated[str, Field(pattern=r"^[A-Z]{1,2}$")]
    locality: Annotated[str, Field(min_length=1, max_length=200)]
    address: Annotated[str, Field(min_length=1, max_length=500)]
    date_start: date = Field(alias="dateStart")
    date_end: Optional[date] = Field(default=None, alias="dateEnd")
    time_start: str = Field(alias="timeStart", pattern=r"^\d{2}:\d{2}$")
    time_end: str = Field(alias="timeEnd", pattern=r"^\d{2}:\d{2}$")
    species: Annotated[list[Species], Field(min_length=1)]
    slots_dogs: Optional[int] = Field(default=None, ge=1, le=10000, alias="slotsDogs")
    slots_cats: Optional[int] = Field(default=None, ge=1, le=10000, alias="slotsCats")
    doctor: Optional[Annotated[str, Field(max_length=200)]] = None
    gdpr_consent: Literal[True] = Field(alias="gdprConsent")
    turnstile_token: Annotated[str, Field(min_length=1, alias="turnstileToken")]

    model_config = {"populate_by_name": True, "str_strip_whitespace": True}

    @field_validator("contact_phone", "phone_public")
    @classmethod
    def _valid_phone(cls, v):
        if not PHONE_RE.match(v):
            raise ValueError("invalid phone format")
        return v

    @model_validator(mode="after")
    def _coherent(self):
        if self.date_start < date.today():
            raise ValueError("dateStart must be today or in the future")
        if self.date_end and self.date_end < self.date_start:
            raise ValueError("dateEnd must be >= dateStart")
        if self.date_end is None and self.time_end <= self.time_start:
            raise ValueError("timeEnd must be after timeStart")
        if "dog" in self.species and not self.slots_dogs:
            raise ValueError("slotsDogs required when species includes dog")
        if "cat" in self.species and not self.slots_cats:
            raise ValueError("slotsCats required when species includes cat")
        return self


def pydantic_errors_to_response(e: ValidationError) -> dict:
    """Map Pydantic errors to the docs' validation_failed shape."""
    errors = [
        {"field": ".".join(str(x) for x in err["loc"]), "message": err["msg"]}
        for err in e.errors()
    ]
    return err(400, "validation_failed", errors=errors)


