"""
JUSTITIA CLI - Command Line Interface

Main entry point for the JUSTITIA policy compiler.
"""

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich import pretty
from typing import Optional
from pathlib import Path
from justitia.policy import PolicyGenerator, save_policy_pack
from justitia.tests import PolicyTestSuite, create_sample_test_cases

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
    cases_file: Path = typer.Option(..., "--cases", "-c", help="Test cases JSON file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output report file")
):
    """Test policy against test cases"""
    console.print(Panel.fit(
        "🧪 Running policy validation tests",
        style="bold yellow"
    ))
    
    if not policy_file.exists():
        console.print(f"❌ Policy file not found: {policy_file}", style="red")
        raise typer.Exit(1)
    
    if not cases_file.exists():
        console.print(f"❌ Cases file not found: {cases_file}", style="red")
        raise typer.Exit(1)
    
    try:
        # Initialize test suite
        test_suite = PolicyTestSuite(policy_file, cases_file)
        
        # Run tests
        console.print(f"🔍 Testing {len(test_suite.test_cases)} cases against {len(test_suite.policy.rules)} rules...")
        results = test_suite.run_all_tests()
        
        # Display results
        test_suite.display_results(results)
        
        # Save report if requested
        if output:
            report = test_suite.generate_report(results)
            with output.open('w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            console.print(f"📄 Report saved to: {output}")
        
        # Exit with error code if tests failed
        failed_count = sum(1 for r in results if not r.passed)
        if failed_count > 0:
            console.print(f"⚠️ {failed_count} tests failed", style="red")
            raise typer.Exit(1)
        else:
            console.print("🎉 All tests passed!", style="green")
            
    except Exception as e:
        console.print(f"❌ Test execution failed: {e}", style="red")
        raise typer.Exit(1)

@app.command() 
def create_samples(
    domain: str = typer.Argument(..., help="Domain for sample generation"),
    output_dir: Path = typer.Option("./examples", "--output", "-o", help="Output directory")
):
    """Create sample norms and test cases for a domain"""
    console.print(Panel.fit(
        f"� Creating sample files for domain: {domain}",
        style="bold cyan"
    ))
    
    domain_dir = output_dir / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    
    # Create sample test cases
    cases_file = domain_dir / "test_cases.json"
    create_sample_test_cases(domain, cases_file)
    
    # Create sample norms based on domain
    norms_file = domain_dir / "norms.txt"
    if domain == "content-moderation":
        norms_content = """Content Moderation Policy

Our platform prohibits:
1. Hate speech targeting individuals or groups based on protected characteristics
2. Harassment including personal attacks, threats, and bullying behavior  
3. Explicit content including graphic violence and adult material
4. Spam and misleading information

Generate JSON rules with regex patterns to detect these violations.
Include rationale for each rule and appropriate severity levels.
"""
    elif domain == "code-review":
        norms_content = """Code Review Policy

Security requirements:
1. No hardcoded secrets, API keys, or passwords in source code
2. Proper input validation and sanitization required
3. No use of deprecated or vulnerable functions
4. All database queries must use parameterized statements

Generate JSON rules to automatically detect these security issues.
"""
    else:
        norms_content = f"Sample policy norms for {domain} domain.\n\nAdd your specific requirements here."
    
    norms_file.write_text(norms_content, encoding='utf-8')
    
    console.print(f"✅ Created sample files:")
    console.print(f"  📄 Norms: {norms_file}")
    console.print(f"  🧪 Test cases: {cases_file}")
    console.print(f"\n📋 Next steps:")
    console.print(f"1. Edit {norms_file} with your specific requirements")
    console.print(f"2. Run: justitia generate --input {norms_file}")
    console.print(f"3. Run: justitia test --policy policy.json --cases {cases_file}")

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