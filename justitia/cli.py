"""
JUSTITIA CLI - Command Line Interface

Main entry point for the JUSTITIA policy compiler.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from typing import Optional
from pathlib import Path

app = typer.Typer(
    name="justitia",
    help="🏛️ JUSTITIA: Transparent AI Policy Compiler",
    add_completion=False,
)

console = Console()

@app.command()
def init(
    domain: str = typer.Argument(..., help="Policy domain (e.g., content-moderation, code-review)"),
    output_dir: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory")
):
    """Initialize a new policy project"""
    console.print(Panel.fit(
        f"🎯 Initializing JUSTITIA policy project: {domain}",
        style="bold green"
    ))
    
    # Create project directory
    project_dir = output_dir or Path(f"./justitia-{domain}")
    project_dir.mkdir(exist_ok=True)
    
    # Create basic structure
    (project_dir / "norms.txt").touch()
    (project_dir / "cases.json").touch()
    (project_dir / "config.json").write_text('{"domain": "' + domain + '", "version": "0.1.0"}')
    
    console.print(f"✅ Created project in: {project_dir.absolute()}")
    console.print("📝 Next steps:")
    console.print("1. Edit norms.txt with your organizational policies")
    console.print("2. Add test cases to cases.json")
    console.print("3. Run: justitia generate --input norms.txt")

@app.command()
def generate(
    input_file: Path = typer.Option(..., "--input", "-i", help="Input norms file"),
    effort: str = typer.Option("medium", "--effort", "-e", help="Reasoning effort: low/medium/high"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory")
):
    """Generate policy from norms"""
    console.print(Panel.fit(
        f"🧠 Generating policy with {effort} reasoning effort",
        style="bold blue"
    ))
    
    if not input_file.exists():
        console.print(f"❌ Input file not found: {input_file}", style="red")
        raise typer.Exit(1)
    
    # TODO: This will be implemented in next steps
    console.print("🚧 Policy generation coming in next step...")
    console.print(f"📄 Input: {input_file}")
    console.print(f"🎚️ Effort: {effort}")

@app.command()
def test(
    policy_file: Path = typer.Option(..., "--policy", "-p", help="Policy JSON file"),
    cases_file: Path = typer.Option(..., "--cases", "-c", help="Test cases JSON file")
):
    """Test policy against cases"""
    console.print(Panel.fit(
        "🧪 Running policy tests",
        style="bold yellow"
    ))
    
    # TODO: Implementation coming
    console.print("🚧 Policy testing coming in next step...")

@app.command()
def version():
    """Show version info"""
    from justitia import __version__, __description__
    console.print(Panel.fit(
        f"JUSTITIA v{__version__}\n{__description__}\n\n🏆 OpenAI Open Model Hackathon 2025",
        style="bold cyan"
    ))

if __name__ == "__main__":
    app()