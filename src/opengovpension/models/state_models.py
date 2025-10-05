"""
State-specific models for pension system data.

This module contains Pydantic models for state-specific pension data,
including member information, benefit calculations, and compliance tracking.
"""

from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator

from ..core.state_config import StateCode


class StateMemberProfile(BaseModel):
    """Profile information for a state pension system member."""

    member_id: str = Field(..., description="Unique member identifier")
    state_code: StateCode = Field(..., description="State code for pension system")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: date = Field(..., description="Member's date of birth")
    hire_date: date = Field(..., description="Employment start date")
    termination_date: Optional[date] = Field(None, description="Employment end date")

    # Employment information
    annual_salary: Decimal = Field(..., gt=0, description="Current annual salary")
    employee_contribution_rate: float = Field(..., ge=0, le=100, description="Contribution percentage")

    # State-specific flags
    is_public_safety_employee: bool = Field(False, description="Public safety employee flag")
    is_teacher: bool = Field(False, description="Teacher flag")
    requires_spouse_approval: bool = Field(False, description="Spouse approval required")

    @validator('employee_contribution_rate')
    def validate_contribution_rate(cls, v):
        """Validate contribution rate is reasonable."""
        if v > 50:
            raise ValueError("Employee contribution rate cannot exceed 50%")
        return v

    @property
    def age(self) -> int:
        """Calculate current age."""
        today = date.today()
        age = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age

    @property
    def service_years(self) -> float:
        """Calculate years of service."""
        end_date = self.termination_date or date.today()
        service_days = (end_date - self.hire_date).days
        return service_days / 365.25

    @property
    def is_vested(self) -> bool:
        """Check if member is vested based on state rules."""
        from ..core.state_config import get_state_config

        config = get_state_config(self.state_code)
        return self.service_years >= config.vesting_years_cliff


class StateBenefitCalculation(BaseModel):
    """State-specific benefit calculation parameters."""

    member_profile: StateMemberProfile
    final_average_salary: Decimal = Field(..., gt=0, description="Final average salary")
    service_years: float = Field(..., ge=0, description="Years of service")
    age_at_retirement: int = Field(..., ge=50, le=75, description="Age at retirement")

    # Calculation results
    annual_benefit: Optional[Decimal] = Field(None, description="Calculated annual benefit")
    monthly_benefit: Optional[Decimal] = Field(None, description="Calculated monthly benefit")

    # State-specific factors
    benefit_multiplier: Optional[float] = Field(None, description="State benefit multiplier")
    early_retirement_reduction: Optional[float] = Field(None, description="Early retirement reduction")
    cola_adjustment: Optional[float] = Field(None, description="Cost of living adjustment")

    def calculate_benefit(self) -> Decimal:
        """Calculate annual benefit based on state rules."""
        from ..core.state_config import get_state_config

        config = get_state_config(self.member_profile.state_code)

        # Base calculation
        base_benefit = self.final_average_salary * Decimal(str(config.benefit_multiplier)) * Decimal(str(self.service_years)) / Decimal("100")

        # Apply early retirement reduction if applicable
        if self.age_at_retirement < config.normal_retirement_age:
            reduction_years = config.normal_retirement_age - self.age_at_retirement
            reduction_factor = 1.0 - (reduction_years * 0.06)  # 6% per year reduction
            base_benefit *= Decimal(str(reduction_factor))
            self.early_retirement_reduction = reduction_years * 6.0

        self.annual_benefit = base_benefit
        self.monthly_benefit = base_benefit / 12

        return base_benefit


class StateComplianceReport(BaseModel):
    """Compliance report for state-specific requirements."""

    member_profile: StateMemberProfile
    compliance_date: date = Field(default_factory=date.today)

    # Compliance checks
    contribution_compliant: bool = Field(..., description="Contribution rate compliance")
    vesting_compliant: bool = Field(..., description="Vesting requirement compliance")
    age_compliant: bool = Field(..., description="Age requirement compliance")
    service_compliant: bool = Field(..., description="Service requirement compliance")

    # State-specific compliance
    medical_exam_required: bool = Field(..., description="Medical examination required")
    medical_exam_completed: bool = Field(False, description="Medical examination completed")
    spouse_approval_required: bool = Field(..., description="Spouse approval required")
    spouse_approval_obtained: bool = Field(False, description="Spouse approval obtained")

    # Reporting information
    next_report_due: date = Field(..., description="Next compliance report due date")
    audit_required: bool = Field(..., description="Audit required this year")

    @property
    def is_fully_compliant(self) -> bool:
        """Check if all compliance requirements are met."""
        return all([
            self.contribution_compliant,
            self.vesting_compliant,
            self.age_compliant,
            self.service_compliant,
            not self.medical_exam_required or self.medical_exam_completed,
            not self.spouse_approval_required or self.spouse_approval_obtained
        ])


class StateContributionSummary(BaseModel):
    """Summary of contributions for a state pension system."""

    state_code: StateCode
    fiscal_year: int = Field(..., description="Fiscal year for the summary")

    # Contribution totals
    total_employee_contributions: Decimal = Field(..., description="Total employee contributions")
    total_employer_contributions: Decimal = Field(..., description="Total employer contributions")
    total_member_count: int = Field(..., ge=0, description="Total number of members")

    # Averages
    average_employee_contribution: Decimal = Field(..., description="Average employee contribution")
    average_employer_contribution: Decimal = Field(..., description="Average employer contribution")
    average_salary: Decimal = Field(..., description="Average member salary")

    # State-specific metrics
    funded_ratio: Optional[float] = Field(None, ge=0, le=200, description="Funded ratio percentage")
    unfunded_liability: Optional[Decimal] = Field(None, description="Unfunded liability amount")

    @validator('average_employee_contribution', 'average_employer_contribution')
    def validate_averages(cls, v, values):
        """Validate that averages are reasonable."""
        if 'total_employee_contributions' in values and 'total_member_count' in values:
            if values['total_member_count'] > 0:
                expected_avg = values['total_employee_contributions'] / values['total_member_count']
                if abs(v - expected_avg) > 0.01:  # Allow for small rounding differences
                    raise ValueError("Average contribution does not match total/member_count")
        return v