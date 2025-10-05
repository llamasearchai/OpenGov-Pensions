"""Data models for OpenPension."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class MemberBase(BaseModel):
    """Base model for Member."""

    name: str = Field(..., description="Member name")
    description: str = Field(..., description="Member description")


class MemberCreate(MemberBase):
    """Model for creating new Member."""


class Member(MemberBase):
    """Complete Member model."""

    id: UUID = Field(default_factory=uuid4, description="Unique database identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    class Config:
        from_attributes = True


class ContributionBase(BaseModel):
    """Base model for Contribution."""

    title: str = Field(..., description="Contribution title")
    content: str = Field(..., description="Contribution content")


class ContributionCreate(ContributionBase):
    """Model for creating new Contribution."""


class Contribution(ContributionBase):
    """Complete Contribution model."""

    id: UUID = Field(default_factory=uuid4, description="Unique database identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")

    class Config:
        from_attributes = True