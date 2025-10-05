"""
State-specific service for pension system operations.

This service provides business logic for state-specific pension operations,
including compliance checking, benefit calculations, and reporting.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from ..core.state_config import (
    get_state_config,
    validate_state_compliance,
    StateCode,
    StatePensionConfig
)
from ..models.state_models import (
    StateMemberProfile,
    StateBenefitCalculation,
    StateComplianceReport,
    StateContributionSummary
)


class StateService:
    """Service for state-specific pension operations."""

    def __init__(self):
        """Initialize the state service."""
        self._configs = {}

    def get_config(self, state_code: StateCode) -> StatePensionConfig:
        """Get configuration for a specific state."""
        if state_code not in self._configs:
            self._configs[state_code] = get_state_config(state_code)
        return self._configs[state_code]

    def validate_member_eligibility(
        self,
        member_profile: StateMemberProfile
    ) -> Dict[str, bool]:
        """
        Validate member eligibility for pension benefits.

        Returns a dictionary with eligibility check results.
        """
        config = self.get_config(member_profile.state_code)

        eligibility = {
            "age_eligible": member_profile.age >= config.early_retirement_age,
            "service_eligible": member_profile.service_years >= config.minimum_service_years,
            "contribution_eligible": (
                config.employee_contribution_min <= member_profile.employee_contribution_rate <= config.employee_contribution_max
            ),
            "vested": member_profile.service_years >= config.vesting_years_cliff
        }

        return eligibility

    def calculate_benefit(
        self,
        member_profile: StateMemberProfile,
        final_average_salary: Decimal,
        retirement_age: int
    ) -> StateBenefitCalculation:
        """
        Calculate pension benefits for a member.

        Args:
            member_profile: Member's profile information
            final_average_salary: Final average salary for benefit calculation
            retirement_age: Age at retirement

        Returns:
            Benefit calculation with all relevant details
        """
        calculation = StateBenefitCalculation(
            member_profile=member_profile,
            final_average_salary=final_average_salary,
            service_years=member_profile.service_years,
            age_at_retirement=retirement_age
        )

        # Apply state-specific rules
        config = self.get_config(member_profile.state_code)

        # Set state-specific factors
        calculation.benefit_multiplier = config.benefit_multiplier
        calculation.cola_adjustment = config.cola_adjustment

        # Calculate early retirement reduction if applicable
        if retirement_age < config.normal_retirement_age:
            reduction_years = config.normal_retirement_age - retirement_age
            calculation.early_retirement_reduction = reduction_years * 6.0  # 6% per year

        # Perform calculation
        calculation.calculate_benefit()

        return calculation

    def generate_compliance_report(
        self,
        member_profile: StateMemberProfile
    ) -> StateComplianceReport:
        """
        Generate a compliance report for a member.

        Args:
            member_profile: Member's profile information

        Returns:
            Compliance report with all requirement checks
        """
        config = self.get_config(member_profile.state_code)

        # Perform compliance validation
        compliance = validate_state_compliance(
            member_profile.state_code,
            member_profile.employee_contribution_rate,
            int(member_profile.service_years),
            member_profile.age
        )

        # Calculate next report due date
        today = date.today()
        next_report_due = date(
            today.year + (1 if today.month > int(config.annual_report_due_date.split('-')[0]) else 0),
            int(config.annual_report_due_date.split('-')[0]),
            int(config.annual_report_due_date.split('-')[1])
        )

        # Determine if audit is required this year
        audit_required = (today.year % config.audit_frequency_years) == 0

        return StateComplianceReport(
            member_profile=member_profile,
            contribution_compliant=compliance["contribution_rate_valid"],
            vesting_compliant=compliance["service_years_sufficient"],
            age_compliant=compliance["age_eligible"],
            service_compliant=compliance["service_years_sufficient"],
            medical_exam_required=config.requires_medical_exam,
            spouse_approval_required=config.requires_spouse_approval,
            next_report_due=next_report_due,
            audit_required=audit_required
        )

    def generate_state_summary(
        self,
        state_code: StateCode,
        fiscal_year: int,
        members: List[StateMemberProfile],
        total_employee_contributions: Decimal,
        total_employer_contributions: Decimal
    ) -> StateContributionSummary:
        """
        Generate a summary of contributions for a state.

        Args:
            state_code: State code
            fiscal_year: Fiscal year for the summary
            members: List of member profiles
            total_employee_contributions: Total employee contributions
            total_employer_contributions: Total employer contributions

        Returns:
            Summary of state contributions and metrics
        """
        if not members:
            raise ValueError("Members list cannot be empty")

        # Calculate averages
        member_count = len(members)
        avg_employee_contribution = total_employee_contributions / member_count
        avg_employer_contribution = total_employer_contributions / member_count
        avg_salary = sum(member.annual_salary for member in members) / member_count

        # Create summary
        summary = StateContributionSummary(
            state_code=state_code,
            fiscal_year=fiscal_year,
            total_employee_contributions=total_employee_contributions,
            total_employer_contributions=total_employer_contributions,
            total_member_count=member_count,
            average_employee_contribution=avg_employee_contribution,
            average_employer_contribution=avg_employer_contribution,
            average_salary=avg_salary
        )

        return summary

    def get_retirement_readiness_score(
        self,
        member_profile: StateMemberProfile
    ) -> Dict[str, float]:
        """
        Calculate retirement readiness score for a member.

        Returns a dictionary with different readiness metrics.
        """
        config = self.get_config(member_profile.state_code)

        # Age readiness (0-100)
        age_progress = min(member_profile.age / config.normal_retirement_age * 100, 100)

        # Service readiness (0-100)
        service_progress = min(member_profile.service_years / config.vesting_years_cliff * 100, 100)

        # Contribution readiness (0-100)
        min_rate = config.employee_contribution_min
        max_rate = config.employee_contribution_max
        contribution_progress = (
            (member_profile.employee_contribution_rate - min_rate) / (max_rate - min_rate) * 100
            if max_rate > min_rate else 100
        )

        # Overall readiness (weighted average)
        overall_readiness = (age_progress * 0.3 + service_progress * 0.5 + contribution_progress * 0.2)

        return {
            "age_readiness": age_progress,
            "service_readiness": service_progress,
            "contribution_readiness": contribution_progress,
            "overall_readiness": overall_readiness
        }


# Global service instance
state_service = StateService()