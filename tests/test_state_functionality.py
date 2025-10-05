"""
Tests for state-specific pension functionality.

This module tests the state-specific features including configuration,
validation, benefit calculations, and compliance checking.
"""

import pytest
from datetime import date
from decimal import Decimal

from src.opengovpension.core.state_config import StateCode, get_state_config, validate_state_compliance
from src.opengovpension.models.state_models import StateMemberProfile, StateBenefitCalculation
from src.opengovpension.services.state_service import state_service


class TestStateConfiguration:
    """Test state configuration functionality."""

    def test_get_state_config_california(self):
        """Test getting California state configuration."""
        config = get_state_config(StateCode.CALIFORNIA)

        assert config.state_code == StateCode.CALIFORNIA
        assert config.state_name == "California"
        assert config.normal_retirement_age == 62
        assert config.benefit_multiplier == 2.5
        assert config.employee_contribution_min == 7.0
        assert config.employee_contribution_max == 12.0

    def test_get_state_config_indiana(self):
        """Test getting Indiana state configuration."""
        config = get_state_config(StateCode.INDIANA)

        assert config.state_code == StateCode.INDIANA
        assert config.state_name == "Indiana"
        assert config.normal_retirement_age == 65
        assert config.benefit_multiplier == 1.1
        assert config.employee_contribution_min == 3.0
        assert config.employee_contribution_max == 6.0

    def test_get_state_config_ohio(self):
        """Test getting Ohio state configuration."""
        config = get_state_config(StateCode.OHIO)

        assert config.state_code == StateCode.OHIO
        assert config.state_name == "Ohio"
        assert config.normal_retirement_age == 60
        assert config.benefit_multiplier == 2.2
        assert config.employee_contribution_min == 10.0
        assert config.employee_contribution_max == 14.0

    def test_unsupported_state(self):
        """Test that unsupported states raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported state"):
            # This would be an invalid state code - let's test with a non-existent enum value
            from src.opengovpension.core.state_config import StateCode
            # Create an invalid StateCode that doesn't exist
            invalid_config = get_state_config("INVALID")


class TestStateValidation:
    """Test state-specific validation functionality."""

    def test_validate_state_compliance_california(self):
        """Test compliance validation for California."""
        compliance = validate_state_compliance(
            StateCode.CALIFORNIA,
            employee_contribution=8.0,
            service_years=10,
            age=65
        )

        assert compliance["contribution_rate_valid"] is True
        assert compliance["service_years_sufficient"] is True
        assert compliance["age_eligible"] is True

    def test_validate_state_compliance_invalid_contribution(self):
        """Test compliance validation with invalid contribution rate."""
        compliance = validate_state_compliance(
            StateCode.CALIFORNIA,
            employee_contribution=15.0,  # Above max
            service_years=10,
            age=65
        )

        assert compliance["contribution_rate_valid"] is False

    def test_validate_state_compliance_insufficient_service(self):
        """Test compliance validation with insufficient service years."""
        compliance = validate_state_compliance(
            StateCode.CALIFORNIA,
            employee_contribution=8.0,
            service_years=3,  # Below minimum
            age=65
        )

        assert compliance["service_years_sufficient"] is False


class TestStateMemberProfile:
    """Test state member profile functionality."""

    def test_member_profile_creation(self):
        """Test creating a member profile."""
        profile = StateMemberProfile(
            member_id="test123",
            state_code=StateCode.CALIFORNIA,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 1),
            hire_date=date(2010, 1, 1),
            annual_salary=Decimal("75000"),
            employee_contribution_rate=8.0
        )

        assert profile.member_id == "test123"
        assert profile.state_code == StateCode.CALIFORNIA
        assert profile.age == 45  # Based on current date
        assert profile.service_years > 14  # Based on hire date

    def test_member_profile_vesting(self):
        """Test vesting calculation."""
        # Create profile with enough service for vesting
        profile = StateMemberProfile(
            member_id="test123",
            state_code=StateCode.CALIFORNIA,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 1),
            hire_date=date(2010, 1, 1),  # 14+ years ago
            annual_salary=Decimal("75000"),
            employee_contribution_rate=8.0
        )

        assert profile.is_vested is True

    def test_member_profile_invalid_contribution_rate(self):
        """Test validation of contribution rate."""
        with pytest.raises(ValueError, match="Employee contribution rate cannot exceed 50%"):
            StateMemberProfile(
                member_id="test123",
                state_code=StateCode.CALIFORNIA,
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1980, 1, 1),
                hire_date=date(2010, 1, 1),
                annual_salary=Decimal("75000"),
                employee_contribution_rate=60.0  # Too high
            )


class TestStateBenefitCalculation:
    """Test state benefit calculation functionality."""

    def test_california_benefit_calculation(self):
        """Test benefit calculation for California."""
        # Create a sample member profile
        profile = StateMemberProfile(
            member_id="test123",
            state_code=StateCode.CALIFORNIA,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1955, 1, 1),
            hire_date=date(1985, 1, 1),
            annual_salary=Decimal("80000"),
            employee_contribution_rate=8.0
        )

        calculation = StateBenefitCalculation(
            member_profile=profile,
            final_average_salary=Decimal("85000"),
            service_years=30,
            age_at_retirement=62
        )

        annual_benefit = calculation.calculate_benefit()

        # California: 2.5% * 30 years * $85,000 = $63,750
        expected_benefit = Decimal("85000") * Decimal("2.5") * Decimal("30") / Decimal("100")
        assert annual_benefit == expected_benefit
        assert calculation.monthly_benefit == annual_benefit / 12

    def test_indiana_benefit_calculation(self):
        """Test benefit calculation for Indiana."""
        profile = StateMemberProfile(
            member_id="test123",
            state_code=StateCode.INDIANA,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1955, 1, 1),
            hire_date=date(1985, 1, 1),
            annual_salary=Decimal("80000"),
            employee_contribution_rate=3.0
        )

        calculation = StateBenefitCalculation(
            member_profile=profile,
            final_average_salary=Decimal("85000"),
            service_years=30,
            age_at_retirement=65
        )

        annual_benefit = calculation.calculate_benefit()

        # Indiana: 1.1% * 30 years * $85,000 = $28,050
        expected_benefit = Decimal("85000") * Decimal("1.1") * Decimal("30") / Decimal("100")
        assert annual_benefit == expected_benefit

    def test_early_retirement_reduction(self):
        """Test early retirement reduction calculation."""
        profile = StateMemberProfile(
            member_id="test123",
            state_code=StateCode.CALIFORNIA,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1965, 1, 1),
            hire_date=date(1995, 1, 1),
            annual_salary=Decimal("80000"),
            employee_contribution_rate=8.0
        )

        calculation = StateBenefitCalculation(
            member_profile=profile,
            final_average_salary=Decimal("85000"),
            service_years=25,
            age_at_retirement=55  # Early retirement
        )

        annual_benefit = calculation.calculate_benefit()

        # Should be reduced from normal retirement age of 62
        # 7 years early * 6% reduction = 42% reduction
        base_benefit = Decimal("85000") * Decimal("2.5") * Decimal("25") / Decimal("100")
        expected_reduced = base_benefit * Decimal("0.58")  # 1.0 - 0.42
        assert calculation.early_retirement_reduction == 42.0
        assert annual_benefit < base_benefit


class TestStateService:
    """Test state service functionality."""

    def test_service_initialization(self):
        """Test state service initialization."""
        service = state_service
        assert service is not None

    def test_get_config_via_service(self):
        """Test getting config through service."""
        config = state_service.get_config(StateCode.CALIFORNIA)
        assert config.state_code == StateCode.CALIFORNIA
        assert config.benefit_multiplier == 2.5

    def test_validate_member_eligibility(self):
        """Test member eligibility validation through service."""
        profile = StateMemberProfile(
            member_id="test123",
            state_code=StateCode.CALIFORNIA,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1955, 1, 1),
            hire_date=date(1980, 1, 1),
            annual_salary=Decimal("80000"),
            employee_contribution_rate=8.0
        )

        eligibility = state_service.validate_member_eligibility(profile)

        assert "age_eligible" in eligibility
        assert "service_eligible" in eligibility
        assert "contribution_eligible" in eligibility
        assert "vested" in eligibility

    def test_calculate_benefit_via_service(self):
        """Test benefit calculation through service."""
        profile = StateMemberProfile(
            member_id="test123",
            state_code=StateCode.CALIFORNIA,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1955, 1, 1),
            hire_date=date(1985, 1, 1),
            annual_salary=Decimal("80000"),
            employee_contribution_rate=8.0
        )

        calculation = state_service.calculate_benefit(
            profile,
            Decimal("85000"),
            62
        )

        assert calculation.annual_benefit > 0
        assert calculation.monthly_benefit > 0
        assert calculation.benefit_multiplier == 2.5

    def test_generate_compliance_report(self):
        """Test compliance report generation."""
        profile = StateMemberProfile(
            member_id="test123",
            state_code=StateCode.CALIFORNIA,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1955, 1, 1),
            hire_date=date(1980, 1, 1),
            annual_salary=Decimal("80000"),
            employee_contribution_rate=8.0
        )

        report = state_service.generate_compliance_report(profile)

        assert report.member_profile == profile
        assert isinstance(report.contribution_compliant, bool)
        assert isinstance(report.vesting_compliant, bool)
        assert isinstance(report.age_compliant, bool)
        assert isinstance(report.service_compliant, bool)
        assert report.next_report_due > date.today()

    def test_retirement_readiness_score(self):
        """Test retirement readiness score calculation."""
        profile = StateMemberProfile(
            member_id="test123",
            state_code=StateCode.CALIFORNIA,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1955, 1, 1),
            hire_date=date(1980, 1, 1),
            annual_salary=Decimal("80000"),
            employee_contribution_rate=8.0
        )

        scores = state_service.get_retirement_readiness_score(profile)

        assert "age_readiness" in scores
        assert "service_readiness" in scores
        assert "contribution_readiness" in scores
        assert "overall_readiness" in scores

        # All scores should be between 0 and 100
        for score in scores.values():
            assert 0 <= score <= 100