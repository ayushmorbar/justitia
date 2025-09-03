"""
JUSTITIA Testing Framework

Validates generated policies against test cases with transparent results.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


class Rule(BaseModel):
    """Individual policy rule with pattern matching"""
    id: str = Field(..., description="Unique rule identifier")
    description: str = Field(..., description="Human-readable rule description")
    pattern: str = Field(..., description="Regex pattern for matching violations")
    threshold: Optional[float] = Field(None, description="Confidence threshold (0.0-1.0)")
    rationale: Optional[str] = Field(None, description="Reasoning for this rule")
    severity: str = Field(default="medium", description="low/medium/high/critical")


class Policy(BaseModel):
    """Complete policy specification"""
    domain: str = Field(..., description="Policy domain (e.g., content-moderation)")
    version: str = Field(default="1.0", description="Policy version")
    rules: List[Rule] = Field(..., description="List of policy rules")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional policy metadata")


class TestCase(BaseModel):
    """Individual test case for policy validation"""
    id: str = Field(..., description="Test case identifier")
    text: str = Field(..., description="Text content to test")
    expected_violations: List[str] = Field(..., description="Rule IDs expected to be triggered")
    description: Optional[str] = Field(None, description="Test case description")
    category: str = Field(default="general", description="Test category")


class TestResult(BaseModel):
    """Result of running a single test case"""
    test_id: str
    violations_found: List[str]
    passed: bool
    false_positives: List[str]  # Rules triggered but not expected
    false_negatives: List[str]  # Rules expected but not triggered
    score: float = Field(default=0.0, description="Test score (0.0-1.0)")


class PolicyTestSuite:
    """Main test runner for policy validation"""
    
    def __init__(self, policy_path: Path = None, cases_path: Path = None, policy_data: Dict[str, Any] = None, test_cases_data: Dict[str, Any] = None):
        if policy_data is not None and test_cases_data is not None:
            # Direct data mode for notebook/in-memory usage
            self.policy = Policy(**policy_data)
            # Handle both single dict and list formats
            if isinstance(test_cases_data, dict):
                cases_list = test_cases_data.get('test_cases', [test_cases_data])
            else:
                cases_list = test_cases_data
            self.test_cases = [TestCase(**case) for case in cases_list]
        elif policy_path is not None and cases_path is not None:
            # File mode for CLI usage
            self.policy_path = policy_path
            self.cases_path = cases_path
            self.policy = self._load_policy()
            self.test_cases = self._load_test_cases()
        else:
            raise ValueError("Either provide file paths (policy_path, cases_path) or data (policy_data, test_cases_data)")
    
    def _load_policy(self) -> Policy:
        """Load and validate policy JSON"""
        if not hasattr(self, 'policy_path') or self.policy_path is None:
            raise ValueError("Policy path not set for file loading")
        try:
            with self.policy_path.open('r', encoding='utf-8') as f:
                policy_data = json.load(f)
            return Policy(**policy_data)
        except Exception as e:
            raise ValueError(f"Failed to load policy from {self.policy_path}: {e}")
    
    def _load_test_cases(self) -> List[TestCase]:
        """Load and validate test cases JSON"""
        if not hasattr(self, 'cases_path') or self.cases_path is None:
            raise ValueError("Test cases path not set for file loading")
        try:
            with self.cases_path.open('r', encoding='utf-8') as f:
                cases_data = json.load(f)
            
            # Handle both single dict and list formats
            if isinstance(cases_data, dict):
                cases_list = cases_data.get('test_cases', [cases_data])
            else:
                cases_list = cases_data
            
            return [TestCase(**case) for case in cases_list]
        except Exception as e:
            raise ValueError(f"Failed to load test cases from {self.cases_path}: {e}")
    
    def run_tests(self, policy_data: Dict[str, Any] = None, test_cases_data: Dict[str, Any] = None):
        """
        Run tests with provided data (for notebook usage).
        If no data provided, uses loaded policy and test cases.
        """
        if policy_data is not None or test_cases_data is not None:
            # Update policy and test cases with provided data
            if policy_data is not None:
                self.policy = Policy(**policy_data)
            if test_cases_data is not None:
                # Handle both single dict and list formats
                if isinstance(test_cases_data, dict):
                    cases_list = test_cases_data.get('test_cases', [test_cases_data])
                else:
                    cases_list = test_cases_data
                self.test_cases = [TestCase(**case) for case in cases_list]
        
        # Run all tests and return results with summary
        results = self.run_all_tests()
        report = self.generate_report(results)
        
        # Create a simple object to hold results for backward compatibility
        class TestResults:
            def __init__(self, results, summary):
                self.test_results = results
                self.total_tests = summary['total_tests']
                self.passed = summary['passed'] 
                self.failed = summary['failed']
                self.pass_rate = summary['pass_rate']
                self.average_score = summary['average_score']
        
        return TestResults(results, report['summary'])
    
    def run_single_test(self, test_case: TestCase) -> TestResult:
        """Run a single test case against the policy"""
        violations_found = []
        
        # Check each rule pattern against the test text
        for rule in self.policy.rules:
            try:
                if re.search(rule.pattern, test_case.text, flags=re.IGNORECASE | re.MULTILINE):
                    violations_found.append(rule.id)
            except re.error as e:
                console.print(f"⚠️ Invalid regex in rule {rule.id}: {e}", style="yellow")
                continue
        
        # Calculate test results
        expected = set(test_case.expected_violations)
        found = set(violations_found)
        
        passed = expected == found
        false_positives = list(found - expected)
        false_negatives = list(expected - found)
        
        # Calculate score (1.0 = perfect, 0.0 = completely wrong)
        if len(expected) == 0 and len(found) == 0:
            score = 1.0
        elif len(expected) == 0:
            score = 0.0  # Found violations when none expected
        else:
            correct = len(expected & found)
            total_errors = len(false_positives) + len(false_negatives)
            score = max(0.0, (correct - total_errors) / len(expected))
        
        return TestResult(
            test_id=test_case.id,
            violations_found=violations_found,
            passed=passed,
            false_positives=false_positives,
            false_negatives=false_negatives,
            score=score
        )
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all test cases and return results"""
        return [self.run_single_test(case) for case in self.test_cases]
    
    def generate_report(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate summary report from test results"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        average_score = sum(r.score for r in results) / total_tests if total_tests > 0 else 0.0
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "pass_rate": passed_tests / total_tests if total_tests > 0 else 0.0,
                "average_score": average_score
            },
            "results": [r.dict() for r in results]
        }
    
    def display_results(self, results: List[TestResult]):
        """Display test results in rich formatted table"""
        table = Table(title=f"Policy Test Results: {self.policy.domain}")
        table.add_column("Test ID", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Score", justify="right")
        table.add_column("Violations", style="dim")
        table.add_column("Issues", style="red")
        
        for result in results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            score = f"{result.score:.2f}"
            violations = ", ".join(result.violations_found) if result.violations_found else "None"
            
            issues = []
            if result.false_positives:
                issues.append(f"FP: {', '.join(result.false_positives)}")
            if result.false_negatives:
                issues.append(f"FN: {', '.join(result.false_negatives)}")
            issue_text = "; ".join(issues) if issues else "None"
            
            table.add_row(result.test_id, status, score, violations, issue_text)
        
        console.print(table)
        
        # Summary panel
        report = self.generate_report(results)
        summary = report["summary"]
        
        summary_text = f"""
Tests: {summary['total_tests']}
Passed: {summary['passed']} ({summary['pass_rate']:.1%})
Failed: {summary['failed']}
Average Score: {summary['average_score']:.3f}
        """
        
        console.print(Panel(summary_text.strip(), title="📊 Test Summary", style="green" if summary['pass_rate'] > 0.8 else "yellow"))


def create_sample_test_cases(domain: str, output_path: Path):
    """Generate sample test cases for a given domain"""
    
    if domain == "content-moderation":
        sample_cases = {
            "test_cases": [
                {
                    "id": "hate_speech_1",
                    "text": "I hate those people, they should all die",
                    "expected_violations": ["hate_speech", "threats"],
                    "description": "Clear hate speech with death threat",
                    "category": "hate_speech"
                },
                {
                    "id": "clean_content_1", 
                    "text": "I love this new feature, great job team!",
                    "expected_violations": [],
                    "description": "Positive, clean content",
                    "category": "clean"
                },
                {
                    "id": "harassment_1",
                    "text": "You're stupid @user stop posting here nobody likes you",
                    "expected_violations": ["harassment", "personal_attacks"],
                    "description": "Personal attack and harassment",
                    "category": "harassment"
                }
            ]
        }
    elif domain == "code-review":
        sample_cases = {
            "test_cases": [
                {
                    "id": "hardcoded_secret_1",
                    "text": "API_KEY = 'sk-1234567890abcdef'",
                    "expected_violations": ["hardcoded_secrets"],
                    "description": "Hardcoded API key",
                    "category": "security"
                },
                {
                    "id": "clean_code_1",
                    "text": "def calculate_sum(a, b):\n    return a + b",
                    "expected_violations": [],
                    "description": "Clean, simple function",
                    "category": "clean"
                }
            ]
        }
    else:
        sample_cases = {
            "test_cases": [
                {
                    "id": "sample_1",
                    "text": "Sample text for testing",
                    "expected_violations": [],
                    "description": "Generic sample case",
                    "category": "general"
                }
            ]
        }
    
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(sample_cases, f, indent=2)