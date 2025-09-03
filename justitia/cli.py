"""
JUSTITIA CLI - Command Line Interface

Main entry point for the JUSTITIA policy compiler.
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich import pretty
from typing import Optional
from pathlib import Path
from justitia.policy import PolicyGenerator, save_policy_pack

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
        f"🧠 Generating policy with reasoning effort: {effort}",
        style="bold blue"
    ))
    
    if not input_file.exists():
        console.print(f"❌ Input file not found: {input_file}", style="red")
        raise typer.Exit(1)

    # Read norms content
    with input_file.open("r", encoding="utf-8") as f:
        norms_text = f.read()

    # Determine domain and output path
    domain = input_file.parent.name if input_file.parent.name != "." else "default-domain"
    if output:
        output_path = output
        if output_path.is_file():
            output_path = output_path.parent
    else:
        output_path = input_file.parent / "generated"

    console.print(f"📂 Domain: {domain}")
    console.print(f"📄 Input file: {input_file}")
    console.print(f"💾 Output directory: {output_path}")

    # Initialize policy generator
    pg = PolicyGenerator(domain=domain, reasoning_effort=effort)
    
    console.print("⏳ Contacting gpt-oss model via Ollama...")
    console.print("🤖 This may take 30-60 seconds for complex policies...")
    
    try:
        result = pg.generate_policy(norms_text)
        
        policy_json = result["policy_json"]
        audit_notebook = result["audit_notebook"]
        raw_response = result["raw_response"]

        console.print("[green]✅ Policy generated successfully!")
        console.print(f"📄 Saving policy pack to: {output_path}")
        
        save_policy_pack(policy_json, audit_notebook, output_path)
        
        # Show previews
        console.print("\n[bold cyan]� Policy JSON Preview:[/bold cyan]")
        if policy_json:
            pretty.pprint(policy_json, console=console, max_length=3, max_string=100)
        else:
            console.print("⚠️ JSON parsing failed; see audit notebook for details", style="yellow")

        console.print("\n[bold cyan]📝 Audit Notebook Preview:[/bold cyan]")
        audit_preview = audit_notebook[:300] + "..." if len(audit_notebook) > 300 else audit_notebook
        console.print(audit_preview if audit_preview.strip() else "No reasoning captured")

        console.print(f"\n[bold green]🎉 Policy generation complete!")
        console.print(f"📁 Files saved:")
        console.print(f"   • {output_path}/policy.json")
        console.print(f"   • {output_path}/audit_notebook.md")
        
    except RuntimeError as e:
        console.print(f"❌ Error generating policy: {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
        raise typer.Exit(1)

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