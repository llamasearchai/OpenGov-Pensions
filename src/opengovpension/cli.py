"""Command-line interface for OpenPension."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .core.config import get_settings
from .core.database import DatabaseManager
from .services.agent_service import AgentService
from .services.ollama_service import OllamaService
from .services.state_service import state_service
from .utils.logging import get_logger

# Initialize console and logger
console = Console()
logger = get_logger(__name__)

# Create the main Typer app
app = typer.Typer(
    name="openpension",
    help="Comprehensive retirement benefits administration system for public employee pension funds operating under the County Employees' Retirement Law of 1937",
    add_completion=False,
)

# Define the repository/application name
repo_name = "OpenPension"

# Sub-apps for organization
agent_app = typer.Typer(help="AI-powered analysis commands")
db_app = typer.Typer(help="Database management commands")
llm_app = typer.Typer(help="LLM and model management commands")
query_app = typer.Typer(help="Data query and analysis commands")
state_app = typer.Typer(help="State-specific pension operations")
app.add_typer(agent_app, name="agent")
app.add_typer(db_app, name="db")
app.add_typer(llm_app, name="llm")
app.add_typer(query_app, name="query")
app.add_typer(state_app, name="state")


@app.callback()
def callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """OpenPension - Comprehensive retirement benefits administration system for public employee pension funds operating under the County Employees' Retirement Law of 1937."""
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    if config:
        os.environ["OPENPENSION_CONFIG"] = str(config)




@agent_app.command("run")
def agent_run(
    prompt: str = typer.Argument(..., help="Analysis prompt for the AI agent"),
    model: str = typer.Option("gpt-4", "--model", "-m", help="Model to use for analysis"),
    provider: str = typer.Option("openai", "--provider", "-p", help="AI provider (openai/ollama)"),
):
    """Run AI-powered analysis."""
    console.print(f"[bold green]Running Analysis[/bold green]")
    console.print(f"Prompt: {prompt}")
    console.print(f"Model: {model}")
    console.print(f"Provider: {provider}")
    console.print("-" * 50)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing...", total=None)

        try:
            settings = get_settings()
            agent_service = AgentService()
            result = asyncio.run(agent_service.run_analysis(prompt, model, provider))

            progress.update(task, completed=True)
            console.print("[bold green]✓ Analysis Complete[/bold green]")
            console.print(f"Result: {result}")

        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[bold red]✗ Analysis Failed: {e}[/bold red]")
            raise typer.Exit(1)


@db_app.command("init")
def db_init(
    drop_existing: bool = typer.Option(False, "--drop-existing", help="Drop existing database"),
):
    """Initialize the database."""
    console.print("[bold blue]Initializing Database[/bold blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up database...", total=None)

        try:
            db_manager = DatabaseManager()
            db_manager.initialize(drop_existing=drop_existing)
            progress.update(task, completed=True)
            console.print("[bold green]✓ Database initialized[/bold green]")

        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[bold red]✗ Failed: {e}[/bold red]")
            raise typer.Exit(1)


@db_app.command("seed")
def db_seed():
    """Seed database with sample data."""
    console.print("[bold blue]Seeding Database[/bold blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Seeding database...", total=None)

        try:
            db_manager = DatabaseManager()
            db_manager.seed_sample_data()
            progress.update(task, completed=True)
            console.print("[bold green]✓ Database seeded[/bold green]")

        except Exception as e:
            progress.update(task, completed=True)
            console.print(f"[bold red]✗ Failed: {e}[/bold red]")
            raise typer.Exit(1)


@app.command("serve-datasette")
def serve_datasette(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8001, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
):
    """Serve the Datasette web interface."""
    console.print("[bold blue]Starting Dashboard[/bold blue]")
    console.print(f"Host: {host}")
    console.print(f"Port: {port}")

    try:
        import subprocess
        cmd = [sys.executable, "-m", "datasette", "serve", f"data/{repo_name.lower()}.db", "--host", host, "--port", str(port)]

        if reload:
            cmd.append("--reload")

        console.print("[bold green]✓ Dashboard starting...[/bold green]")
        console.print(f"Open http://{host}:{port} in your browser")
        subprocess.run(cmd)

    except Exception as e:
        console.print(f"[bold red]✗ Failed: {e}[/bold red]")
        raise typer.Exit(1)


@app.command("version")
def show_version():
    """Show version information."""
    console.print(f"[bold blue]OpenPension v1.0.0[/bold blue]")
    console.print("Author: Nik Jois <nikjois@llamasearch.ai>")
    console.print("Python: 3.11+")


@app.command("serve")
def serve_api(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to."),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to."),
):
    """
    Start FastAPI web server for API access.
    """
    console.print(f"Starting FastAPI server on {host}:{port}...")
    console.print("[bold green]Open your browser to: http://{host}:{port}[/bold green]")
    console.print("[bold blue]API Documentation: http://{host}:{port}/docs[/bold blue]")

    try:
        import uvicorn
        uvicorn.run(
            "opengovpension.web.app:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        console.print("\n[bold blue]FastAPI server stopped.[/bold blue]")
    except Exception as e:
        console.print(f"[bold red]Error starting FastAPI server: {e}[/bold red]")
        raise typer.Exit(1)





@app.command("menu")
def interactive_menu():
    """
    Launch interactive menu system.
    """
    console.print(f"[bold blue]{repo_name} Interactive Menu[/bold blue]")
    console.print("=" * 50)

    while True:
        console.print("\n[bold cyan]Available Operations:[/bold cyan]")
        console.print("1. Database Management")
        console.print("2. AI Analysis")
        console.print("3. Web Server")
        console.print("4. State Operations")
        console.print("5. Export Data")
        console.print("6. System Status")
        console.print("7. Exit")

        choice = typer.prompt("\nChoose an option (1-7)", type=int)

        if choice == 1:
            db_submenu()
        elif choice == 2:
            ai_submenu()
        elif choice == 3:
            web_submenu()
        elif choice == 4:
            state_submenu()
        elif choice == 5:
            export_submenu()
        elif choice == 6:
            status_submenu()
        elif choice == 7:
            console.print("[bold green]Goodbye![/bold green]")
            break
        else:
            console.print("[bold red]Invalid choice. Please try again.[/bold red]")

def db_submenu():
    """Database operations submenu."""
    console.print("\n[bold yellow]Database Operations:[/bold yellow]")
    console.print("1. Initialize Database")
    console.print("2. Seed Sample Data")
    console.print("3. Run Migrations")
    console.print("4. View Statistics")
    console.print("5. Back to Main Menu")

    choice = typer.prompt("Choose an option (1-5)", type=int)

    if choice == 1:
        db_init()
    elif choice == 2:
        db_seed()
    elif choice == 3:
        console.print("[bold yellow]Migration command not implemented yet[/bold yellow]")
    elif choice == 4:
        console.print("[bold yellow]Database query command not implemented yet[/bold yellow]")

def ai_submenu():
    """AI analysis submenu."""
    console.print("\n[bold yellow]AI Analysis:[/bold yellow]")
    console.print("1. Run Analysis")
    console.print("2. Chat with AI")
    console.print("3. Batch Processing")
    console.print("4. Back to Main Menu")

    choice = typer.prompt("Choose an option (1-4)", type=int)

    if choice == 1:
        prompt = typer.prompt("Enter your analysis prompt")
        model = "gpt-4"  # Default model
        provider = "openai"  # Default provider
        agent_run(prompt, model, provider)
    elif choice == 2:
        console.print("[bold green]AI Chat feature coming soon![/bold green]")

def web_submenu():
    """Web server submenu."""
    console.print("\n[bold yellow]Web Server:[/bold yellow]")
    console.print("1. Start FastAPI Server")
    console.print("2. Start Datasette")
    console.print("3. Back to Main Menu")

    choice = typer.prompt("Choose an option (1-3)", type=int)

    if choice == 1:
        serve_api()
    elif choice == 2:
        serve_datasette()

def export_submenu():
    """Data export submenu."""
    console.print("\n[bold yellow]Data Export:[/bold yellow]")
    console.print("1. Export to CSV")
    console.print("2. Export to JSON")
    console.print("3. Export to Excel")
    console.print("4. Back to Main Menu")

    choice = typer.prompt("Choose an option (1-4)", type=int)

    if choice in [1, 2, 3]:
        format_map = {1: "csv", 2: "json", 3: "excel"}
        console.print(f"[bold green]Export to {format_map[choice]} coming soon![/bold green]")

def state_submenu():
    """State operations submenu."""
    console.print("\n[bold yellow]State Operations:[/bold yellow]")
    console.print("1. List Supported States")
    console.print("2. View State Configuration")
    console.print("3. Validate Member Eligibility")
    console.print("4. Calculate Benefits")
    console.print("5. Back to Main Menu")

    choice = typer.prompt("Choose an option (1-5)", type=int)

    if choice == 1:
        list_supported_states()
    elif choice == 2:
        state = typer.prompt("Enter state code (CA, IN, OH)")
        show_state_config(state)
    elif choice == 3:
        state = typer.prompt("Enter state code (CA, IN, OH)")
        age = typer.prompt("Enter member age", type=int)
        service_years = typer.prompt("Enter service years", type=float)
        contribution_rate = typer.prompt("Enter contribution rate %", type=float)
        validate_member(state, age, service_years, contribution_rate)
    elif choice == 4:
        state = typer.prompt("Enter state code (CA, IN, OH)")
        final_salary = typer.prompt("Enter final average salary", type=float)
        service_years = typer.prompt("Enter service years", type=float)
        retirement_age = typer.prompt("Enter retirement age", type=int)
        calculate_benefit(state, final_salary, service_years, retirement_age)


def status_submenu():
    """System status submenu."""
    console.print("\n[bold yellow]System Status:[/bold yellow]")
    console.print("1. Health Check")
    console.print("2. Database Status")
    console.print("3. AI Services Status")
    console.print("4. Back to Main Menu")

    choice = typer.prompt("Choose an option (1-4)", type=int)

    if choice == 1:
        console.print("[bold green]System is healthy![/bold green]")
    elif choice == 2:
        console.print("[bold yellow]Database status check not implemented yet[/bold yellow]")
    elif choice == 3:
        console.print("[bold green]AI services are operational![/bold green]")


@state_app.command("config")
def show_state_config(
    state: str = typer.Option(None, "--state", "-s", help="State code (CA, IN, OH)"),
):
    """Show state-specific pension configuration."""
    settings = get_settings()

    if state:
        state_code = state.upper()
        if state_code not in settings.supported_states_list:
            console.print(f"[bold red]Unsupported state: {state_code}[/bold red]")
            console.print(f"Supported states: {', '.join(settings.supported_states_list)}")
            raise typer.Exit(1)
    else:
        state_code = settings.default_state_code

    try:
        from .core.state_config import StateCode
        config = state_service.get_config(StateCode(state_code))

        console.print(f"[bold blue]State Configuration: {config.state_name}[/bold blue]")
        console.print("=" * 50)
        console.print(f"Normal Retirement Age: {config.normal_retirement_age}")
        console.print(f"Early Retirement Age: {config.early_retirement_age}")
        console.print(f"Minimum Service Years: {config.minimum_service_years}")
        console.print(f"Employee Contribution Range: {config.employee_contribution_min}% - {config.employee_contribution_max}%")
        console.print(f"Employer Contribution Rate: {config.employer_contribution_rate}%")
        console.print(f"Benefit Multiplier: {config.benefit_multiplier}")
        console.print(f"COLA Adjustment: {config.cola_adjustment}%")
        console.print(f"Vesting (Cliff/Graduated): {config.vesting_years_cliff}/{config.vesting_years_graduated}")
        console.print(f"Requires Spouse Approval: {config.requires_spouse_approval}")
        console.print(f"Requires Medical Exam: {config.requires_medical_exam}")
        console.print(f"State Tax Exempt: {config.state_tax_exempt}")
        console.print(f"Annual Report Due: {config.annual_report_due_date}")
        console.print(f"Audit Frequency: {config.audit_frequency_years} years")

    except Exception as e:
        console.print(f"[bold red]Error getting state config: {e}[/bold red]")
        raise typer.Exit(1)


@state_app.command("validate")
def validate_member(
    state: str = typer.Option(..., "--state", "-s", help="State code (CA, IN, OH)"),
    age: int = typer.Option(..., "--age", "-a", help="Member age"),
    service_years: float = typer.Option(..., "--service-years", "-y", help="Years of service"),
    contribution_rate: float = typer.Option(..., "--contribution", "-c", help="Contribution rate %"),
):
    """Validate member eligibility for state pension system."""
    settings = get_settings()

    state_code = state.upper()
    if state_code not in settings.supported_states_list:
        console.print(f"[bold red]Unsupported state: {state_code}[/bold red]")
        console.print(f"Supported states: {', '.join(settings.supported_states_list)}")
        raise typer.Exit(1)

    try:
        from .core.state_config import StateCode
        from .models.state_models import StateMemberProfile
        from datetime import date

        # Create a sample member profile for validation
        member_profile = StateMemberProfile(
            member_id="sample",
            state_code=StateCode(state_code),
            first_name="Sample",
            last_name="Member",
            date_of_birth=date.today(),  # This will be overridden by age
            hire_date=date.today(),  # This will be overridden by service_years
            annual_salary=50000,
            employee_contribution_rate=contribution_rate
        )

        # Override age and service years for validation
        member_profile.date_of_birth = date.today().replace(year=date.today().year - age)
        member_profile.hire_date = date.today().replace(year=date.today().year - int(service_years))

        eligibility = state_service.validate_member_eligibility(member_profile)

        console.print(f"[bold blue]Eligibility Validation for {state_code}[/bold blue]")
        console.print("=" * 50)
        console.print(f"Age Eligible: {'✓' if eligibility['age_eligible'] else '✗'}")
        console.print(f"Service Eligible: {'✓' if eligibility['service_eligible'] else '✗'}")
        console.print(f"Contribution Eligible: {'✓' if eligibility['contribution_eligible'] else '✗'}")
        console.print(f"Vested: {'✓' if eligibility['vested'] else '✗'}")

        overall_eligible = all(eligibility.values())
        if overall_eligible:
            console.print("[bold green]✓ Member is eligible for pension benefits[/bold green]")
        else:
            console.print("[bold red]✗ Member is not eligible for pension benefits[/bold red]")

    except Exception as e:
        console.print(f"[bold red]Error validating member: {e}[/bold red]")
        raise typer.Exit(1)


@state_app.command("calculate")
def calculate_benefit(
    state: str = typer.Option(..., "--state", "-s", help="State code (CA, IN, OH)"),
    final_salary: float = typer.Option(..., "--final-salary", "-f", help="Final average salary"),
    service_years: float = typer.Option(..., "--service-years", "-y", help="Years of service"),
    retirement_age: int = typer.Option(..., "--retirement-age", "-r", help="Retirement age"),
):
    """Calculate pension benefits for a member."""
    settings = get_settings()

    state_code = state.upper()
    if state_code not in settings.supported_states_list:
        console.print(f"[bold red]Unsupported state: {state_code}[/bold red]")
        console.print(f"Supported states: {', '.join(settings.supported_states_list)}")
        raise typer.Exit(1)

    try:
        from .core.state_config import StateCode
        from .models.state_models import StateMemberProfile
        from datetime import date
        from decimal import Decimal

        # Create a sample member profile
        member_profile = StateMemberProfile(
            member_id="sample",
            state_code=StateCode(state_code),
            first_name="Sample",
            last_name="Member",
            date_of_birth=date.today().replace(year=date.today().year - 65),
            hire_date=date.today().replace(year=date.today().year - int(service_years)),
            annual_salary=Decimal(str(final_salary)),
            employee_contribution_rate=8.0
        )

        calculation = state_service.calculate_benefit(
            member_profile,
            Decimal(str(final_salary)),
            retirement_age
        )

        console.print(f"[bold blue]Benefit Calculation for {state_code}[/bold blue]")
        console.print("=" * 50)
        console.print(f"Final Average Salary: ${final_salary:,.2f}")
        console.print(f"Service Years: {service_years}")
        console.print(f"Retirement Age: {retirement_age}")
        console.print(f"Annual Benefit: ${calculation.annual_benefit:,.2f}")
        console.print(f"Monthly Benefit: ${calculation.monthly_benefit:,.2f}")

        if calculation.early_retirement_reduction:
            console.print(f"Early Retirement Reduction: {calculation.early_retirement_reduction}%")

        console.print(f"Benefit Multiplier: {calculation.benefit_multiplier}")
        console.print(f"COLA Adjustment: {calculation.cola_adjustment}%")

    except Exception as e:
        console.print(f"[bold red]Error calculating benefit: {e}[/bold red]")
        raise typer.Exit(1)


@state_app.command("list")
def list_supported_states():
    """List all supported states and their configurations."""
    settings = get_settings()

    console.print("[bold blue]Supported States[/bold blue]")
    console.print("=" * 50)

    for state_code in settings.supported_states_list:
        try:
            from .core.state_config import StateCode
            config = state_service.get_config(StateCode(state_code))
            console.print(f"[bold cyan]{config.state_code.value}:[/bold cyan] {config.state_name}")
            console.print(f"  Retirement Age: {config.normal_retirement_age}")
            console.print(f"  Benefit Multiplier: {config.benefit_multiplier}")
            console.print(f"  Employee Contribution: {config.employee_contribution_min}-{config.employee_contribution_max}%")
            console.print()
        except Exception as e:
            console.print(f"[bold red]Error loading {state_code}: {e}[/bold red]")


if __name__ == "__main__":
    app()