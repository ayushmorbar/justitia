import json
import re
from pathlib import Path
from typing import Optional, Dict, Tuple
import ollama
from justitia.harmony import (
    create_system_message,
    create_user_message,
    create_conversation,
    encode_conversation,
    create_policy_generation_prompt,
)


class PolicyGenerator:
    def __init__(
        self,
        domain: str,
        model_name: str = "gpt-oss:20b",
        reasoning_effort: str = "medium",
        use_browser: bool = False,
        use_python: bool = True,
    ):
        self.domain = domain
        self.model_name = model_name
        self.reasoning_effort = reasoning_effort
        self.use_browser = use_browser
        self.use_python = use_python

    def generate_policy(
        self,
        norms_text: str,
        developer_message: str = "",
        max_tokens: int = 2048,
    ) -> Dict[str, any]:
        """
        Generate policy rules JSON and chain-of-thought reasoning text.

        Args:
            norms_text: Free text norms or policy descriptions.
            developer_message: Optional developer instructions.
            max_tokens: Maximum tokens to generate.

        Returns:
            Dictionary with:
              - policy_json: Parsed policy JSON object from output (dict)
              - audit_notebook: Chain-of-thought reasoning text (str)
              - raw_response: Full raw model output (str)
        """
        # Create structured prompt for policy generation
        prompt_template = f"""You are JUSTITIA, an AI policy compiler for the "{self.domain}" domain.

Your task is to transform organizational norms into executable, auditable policies with transparent reasoning.

## Input Norms:
{norms_text}

## Instructions:
1. Analyze the norms carefully using chain-of-thought reasoning
2. Generate a structured policy in JSON format
3. Include clear decision criteria and examples
4. Provide audit trail of your reasoning process
5. Create test cases to validate the policy

## Output Format:
Please structure your response as:

**THINKING:**
[Your detailed chain-of-thought analysis here]

**POLICY:**
```json
{{
  "domain": "{self.domain}",
  "version": "1.0",
  "rules": [
    {{
      "id": "rule_001",
      "description": "Clear rule description",
      "criteria": ["specific criteria"],
      "examples": {{
        "allowed": ["example 1", "example 2"],
        "prohibited": ["example 1", "example 2"]
      }},
      "severity": "high|medium|low"
    }}
  ],
  "exceptions": [
    {{
      "rule_id": "rule_001",
      "condition": "exception condition",
      "rationale": "why this exception exists"
    }}
  ]
}}
```

Generate the policy now:"""

        try:
            # Send request to Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are JUSTITIA, an AI policy compiler. Use {self.reasoning_effort} reasoning effort."
                    },
                    {
                        "role": "user", 
                        "content": prompt_template
                    }
                ],
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": max_tokens,
                }
            )
            
            full_output = response.get("message", {}).get("content", "")
            
            # Extract JSON policy and chain-of-thought
            policy_json, audit_notebook = self._extract_policy_and_cot(full_output)

            return {
                "policy_json": policy_json,
                "audit_notebook": audit_notebook,
                "raw_response": full_output,
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to query Ollama model '{self.model_name}': {e}")

    def _extract_policy_and_cot(self, output_text: str) -> Tuple[Dict, str]:
        """
        Parses model output into structured JSON policy and chain-of-thought reasoning.

        Args:
            output_text: Full model response text

        Returns:
            (policy_dict, audit_text)
        """
        try:
            # Extract thinking/reasoning section
            thinking_match = re.search(r"\*\*THINKING:\*\*(.*?)\*\*POLICY:\*\*", output_text, re.DOTALL | re.IGNORECASE)
            audit_text = thinking_match.group(1).strip() if thinking_match else ""
            
            # Extract JSON block from text
            json_match = re.search(r"```json\s*(\{.*?\})\s*```", output_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
                policy_data = json.loads(json_text)
                return policy_data, audit_text
            else:
                # Try to find any JSON-like structure
                json_match = re.search(r"(\{.*\})", output_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(1)
                    policy_data = json.loads(json_text)
                    return policy_data, audit_text if audit_text else output_text
                else:
                    # If no JSON found, return empty policy with full text as audit
                    return {}, output_text
                    
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return empty policy with full text as audit
            return {}, f"JSON parsing failed: {e}\n\nFull response:\n{output_text}"
        except Exception as e:
            return {}, f"Error extracting policy: {e}\n\nFull response:\n{output_text}"


def save_policy_pack(policy: Dict, audit_text: str, output_dir: Path):
    """
    Save policy.json and audit_notebook.md to output directory.
    
    Args:
        policy: Policy dictionary to save as JSON
        audit_text: Chain-of-thought reasoning to save as Markdown
        output_dir: Directory to save files in
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save policy JSON
    policy_path = output_dir / "policy.json"
    with policy_path.open("w", encoding="utf-8") as f:
        json.dump(policy, f, indent=2, ensure_ascii=False)
    
    # Save audit notebook
    audit_path = output_dir / "audit_notebook.md"
    with audit_path.open("w", encoding="utf-8") as f:
        f.write("# JUSTITIA Policy Generation Audit Notebook\n\n")
        f.write(f"**Domain:** {policy.get('domain', 'Unknown')}\n\n")
        f.write(f"**Generated:** {policy.get('version', 'Unknown')}\n\n")
        f.write("## Chain-of-Thought Reasoning\n\n")
        f.write(audit_text if audit_text else "No reasoning captured.")
        f.write("\n\n---\n\n")
        f.write("*Generated by JUSTITIA AI Policy Compiler*\n")