"""
JUSTITIA Textual User Interface

Interactive terminal-based UI for policy generation and testing.
"""

import asyncio
import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Input, Button, Static, Log, 
    Select, TabbedContent, TabPane, DataTable
)
from textual.containers import Vertical, Horizontal, Container
from textual.reactive import reactive
from rich.text import Text

from justitia.policy import PolicyGenerator, save_policy_pack
from justitia.tests import PolicyTestSuite, create_sample_test_cases


class JustitiaTUI(App):
    """JUSTITIA Terminal User Interface"""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    .container {
        width: 100%;
        height: 100%;
        padding: 1;
    }
    
    #norms_input {
        height: 8;
        width: 100%;
        border: round $primary;
    }
    
    #output_log {
        height: 20;
        width: 100%;
        border: round $accent;
        scrollbar-gutter: stable;
    }
    
    .controls {
        height: auto;
        width: 100%;
        padding: 1 0;
    }
    
    .button-row {
        height: 3;
        align: center middle;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    TITLE = "🏛️ JUSTITIA - Policy Compiler"
    SUB_TITLE = "Transparent AI Policy Generation with gpt-oss"
    
    current_domain: reactive[str] = reactive("content-moderation")
    current_effort: reactive[str] = reactive("medium")
    
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header(show_clock=True)
        
        with TabbedContent(initial="generate"):
            with TabPane("Generate Policy", id="generate"):
                yield Container(
                    Horizontal(
                        Select(
                            [
                                ("Content Moderation", "content-moderation"),
                                ("Code Review", "code-review"),
                                ("General Policy", "general")
                            ],
                            value="content-moderation",
                            id="domain_select"
                        ),
                        Select(
                            [("Low", "low"), ("Medium", "medium"), ("High", "high")],
                            value="medium", 
                            id="effort_select"
                        ),
                        classes="controls"
                    ),
                    Input(
                        placeholder="Enter your policy norms here...\n\nExample:\nOur platform prohibits hate speech and harassment.\nRules:\n1. No personal attacks\n2. No discriminatory language\n3. No threats or intimidation",
                        id="norms_input"
                    ),
                    Horizontal(
                        Button("Generate Policy 🧠", id="generate_btn", variant="primary"),
                        Button("Load Sample 📝", id="load_sample_btn"),
                        Button("Clear ✨", id="clear_btn"),
                        classes="button-row"
                    ),
                    Log(id="output_log", highlight=True),
                    classes="container"
                )
            
            with TabPane("Test Policy", id="test"):
                yield Container(
                    Static("Policy testing will be implemented here", id="test_content"),
                    classes="container"
                )
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the app"""
        log = self.query_one("#output_log", Log)
        log.write_line("🏛️ Welcome to JUSTITIA Policy Compiler!")
        log.write_line("📝 Enter your policy norms above and click 'Generate Policy'")
        log.write_line("🎯 Built for OpenAI Open Model Hackathon 2025")
        log.write_line("")
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle dropdown changes"""
        if event.select.id == "domain_select":
            self.current_domain = event.value
            log = self.query_one("#output_log", Log)
            log.write_line(f"📂 Domain changed to: {event.value}")
        elif event.select.id == "effort_select":
            self.current_effort = event.value
            log = self.query_one("#output_log", Log)
            log.write_line(f"⚙️ Reasoning effort set to: {event.value}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks"""
        button_id = event.button.id
        
        if button_id == "generate_btn":
            await self.generate_policy()
        elif button_id == "load_sample_btn":
            self.load_sample_norms()
        elif button_id == "clear_btn":
            self.clear_interface()
    
    async def generate_policy(self) -> None:
        """Generate policy from input norms"""
        norms_input = self.query_one("#norms_input", Input)
        output_log = self.query_one("#output_log", Log)
        
        norms_text = norms_input.value.strip()
        if not norms_text:
            output_log.write_line("[red]❌ Please enter policy norms before generating.[/red]")
            return
        
        output_log.write_line("[green]🧠 Generating policy with gpt-oss...[/green]")
        output_log.write_line(f"📂 Domain: {self.current_domain}")
        output_log.write_line(f"⚙️ Effort: {self.current_effort}")
        output_log.write_line("")
        
        try:
            # Show loading message
            output_log.write_line("[yellow]⏳ Contacting Ollama server...[/yellow]")
            
            # Create policy generator
            pg = PolicyGenerator(
                domain=self.current_domain,
                reasoning_effort=self.current_effort
            )
            
            # Generate policy (run in thread to avoid blocking UI)
            result = await asyncio.to_thread(pg.generate_policy, norms_text)
            
            policy_json = result.get("policy_json", {})
            audit_notebook = result.get("audit_notebook", "")
            
            # Display results
            output_log.write_line("[green]✅ Policy generated successfully![/green]")
            output_log.write_line("")
            
            if policy_json:
                rules_count = len(policy_json.get("rules", []))
                output_log.write_line(f"[bold cyan]📋 Generated {rules_count} policy rules:[/bold cyan]")
                
                for i, rule in enumerate(policy_json.get("rules", []), 1):
                    output_log.write_line(f"  {i}. {rule.get('description', 'No description')}")
                    output_log.write_line(f"     Pattern: [dim]{rule.get('pattern', 'N/A')}[/dim]")
                    output_log.write_line(f"     Severity: [{'red' if rule.get('severity') == 'high' else 'yellow' if rule.get('severity') == 'medium' else 'green'}]{rule.get('severity', 'unknown')}[/]")
                    output_log.write_line("")
            
            # Show audit notebook preview
            if audit_notebook:
                output_log.write_line("[bold magenta]🔍 Reasoning Process (Preview):[/bold magenta]")
                preview = audit_notebook[:300] + "..." if len(audit_notebook) > 300 else audit_notebook
                output_log.write_line(f"[dim]{preview}[/dim]")
                output_log.write_line("")
            
            # Save files
            output_dir = Path(f"./output/{self.current_domain}")
            save_policy_pack(policy_json, audit_notebook, output_dir)
            output_log.write_line(f"[green]💾 Files saved to: {output_dir.absolute()}[/green]")
            
        except Exception as e:
            output_log.write_line(f"[red]❌ Generation failed: {str(e)}[/red]")
            output_log.write_line("[yellow]💡 Make sure Ollama is running: ollama serve[/yellow]")
    
    def load_sample_norms(self) -> None:
        """Load sample norms for the current domain"""
        norms_input = self.query_one("#norms_input", Input)
        output_log = self.query_one("#output_log", Log)
        
        samples = {
            "content-moderation": """Content Moderation Policy

Our platform prohibits:
1. Hate speech targeting individuals or groups based on protected characteristics
2. Harassment including personal attacks, threats, and bullying behavior  
3. Explicit content including graphic violence and adult material
4. Spam and misleading information

Generate JSON rules with regex patterns to detect these violations.
Include rationale for each rule and appropriate severity levels.""",
            
            "code-review": """Code Review Security Policy

Security requirements:
1. No hardcoded secrets, API keys, or passwords in source code
2. Proper input validation and sanitization required
3. No use of deprecated or vulnerable functions
4. All database queries must use parameterized statements

Generate JSON rules to automatically detect these security issues.""",
            
            "general": """General Policy Framework

Define clear rules for:
1. Acceptable behavior and conduct
2. Prohibited actions and content
3. Enforcement mechanisms and consequences
4. Exception handling procedures

Create structured, testable policy rules with clear rationale."""
        }
        
        sample_text = samples.get(self.current_domain, samples["general"])
        norms_input.value = sample_text
        output_log.write_line(f"[green]📝 Loaded sample norms for {self.current_domain}[/green]")
    
    def clear_interface(self) -> None:
        """Clear input and output"""
        norms_input = self.query_one("#norms_input", Input)
        output_log = self.query_one("#output_log", Log)
        
        norms_input.value = ""
        output_log.clear()
        output_log.write_line("🏛️ Interface cleared. Ready for new policy generation!")


def main():
    """Main entry point for TUI"""
    app = JustitiaTUI()
    app.run()


if __name__ == "__main__":
    main()
