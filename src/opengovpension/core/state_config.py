"""
State-specific configuration for pension systems.

This module provides state-specific configurations for Indiana, Ohio, and California
pension systems, including regulatory requirements, contribution limits, and
compliance rules.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class StateCode(Enum):
    """Supported state codes for pension systems."""
    CALIFORNIA = "CA"
    INDIANA = "IN"
    OHIO = "OH"


@dataclass
class StatePensionConfig:
    """Configuration for state-specific pension requirements."""

    # Basic state information
    state_code: StateCode
    state_name: str

    # Retirement eligibility
    normal_retirement_age: int
    early_retirement_age: int
    minimum_service_years: int

    # Contribution limits (as percentage of salary)
    employee_contribution_min: float
    employee_contribution_max: float
    employer_contribution_rate: float

    # Vesting requirements
    vesting_years_cliff: int
    vesting_years_graduated: int

    # Benefit calculation factors
    benefit_multiplier: float
    cola_adjustment: float  # Annual cost-of-living adjustment

    # Regulatory compliance
    requires_spouse_approval: bool
    requires_medical_exam: bool
    state_tax_exempt: bool

    # Reporting requirements
    annual_report_due_date: str  # MM-DD format
    audit_frequency_years: int


# State-specific configurations
STATE_CONFIGS: Dict[StateCode, StatePensionConfig] = {
    StateCode.CALIFORNIA: StatePensionConfig(
        state_code=StateCode.CALIFORNIA,
        state_name="California",
        normal_retirement_age=62,
        early_retirement_age=55,
        minimum_service_years=5,
        employee_contribution_min=7.0,
        employee_contribution_max=12.0,
        employer_contribution_rate=15.0,
        vesting_years_cliff=5,
        vesting_years_graduated=10,
        benefit_multiplier=2.5,
        cola_adjustment=2.0,
        requires_spouse_approval=True,
        requires_medical_exam=False,
        state_tax_exempt=True,
        annual_report_due_date="09-30",
        audit_frequency_years=3
    ),

    StateCode.INDIANA: StatePensionConfig(
        state_code=StateCode.INDIANA,
        state_name="Indiana",
        normal_retirement_age=65,
        early_retirement_age=55,
        minimum_service_years=10,
        employee_contribution_min=3.0,
        employee_contribution_max=6.0,
        employer_contribution_rate=11.2,
        vesting_years_cliff=10,
        vesting_years_graduated=15,
        benefit_multiplier=1.1,
        cola_adjustment=1.5,
        requires_spouse_approval=False,
        requires_medical_exam=True,
        state_tax_exempt=False,
        annual_report_due_date="06-30",
        audit_frequency_years=2
    ),

    StateCode.OHIO: StatePensionConfig(
        state_code=StateCode.OHIO,
        state_name="Ohio",
        normal_retirement_age=60,
        early_retirement_age=55,
        minimum_service_years=5,
        employee_contribution_min=10.0,
        employee_contribution_max=14.0,
        employer_contribution_rate=14.0,
        vesting_years_cliff=5,
        vesting_years_graduated=15,
        benefit_multiplier=2.2,
        cola_adjustment=3.0,
        requires_spouse_approval=True,
        requires_medical_exam=False,
        state_tax_exempt=True,
        annual_report_due_date="12-31",
        audit_frequency_years=3
    )
}


def get_state_config(state_code: StateCode) -> StatePensionConfig:
    """Get configuration for a specific state."""
    if state_code not in STATE_CONFIGS:
        raise ValueError(f"Unsupported state: {state_code}")
    return STATE_CONFIGS[state_code]


def get_supported_states() -> Dict[str, str]:
    """Get mapping of state codes to state names."""
    return {config.state_code.value: config.state_name for config in STATE_CONFIGS.values()}


def validate_state_compliance(
    state_code: StateCode,
    employee_contribution: float,
    service_years: int,
    age: int
) -> Dict[str, bool]:
    """
    Validate compliance with state-specific requirements.

    Returns a dictionary with compliance check results.
    """
    config = get_state_config(state_code)

    compliance = {
        "contribution_rate_valid": (
            config.employee_contribution_min <= employee_contribution <= config.employee_contribution_max
        ),
        "service_years_sufficient": service_years >= config.minimum_service_years,
        "age_eligible": age >= config.early_retirement_age,
        "vesting_eligible": service_years >= config.vesting_years_cliff
    }

    return compliance