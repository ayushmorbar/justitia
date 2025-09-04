import json
import re
from pathlib import Path
from typing import Optional, Dict, Tuple

# Try to import ollama, fallback to ollama_python with adapter
try:
    import ollama
except ImportError:
    # Fallback to ollama_python with adapter
    from ollama_python.endpoints.generate import GenerateAPI

    class OllamaAdapter:
        """Adapter to make ollama_python compatible with ollama API"""

        @staticmethod
        def chat(model: str, messages: list, options: dict = None):
            """Adapter method to provide ollama.chat() compatible interface"""
            try:
                # Extract model name from the model string if it includes :tag
                model_name = model
                api = GenerateAPI(model=model_name)

                # Convert messages to the format expected by ollama_python
                formatted_messages = []
                for msg in messages:
                    formatted_messages.append(
                        {"role": msg["role"], "content": msg["content"]}
                    )

                # Call the generate_chat_completion method
                result = api.generate_chat_completion(
                    messages=formatted_messages, options=options or {}
                )

                # Convert response to ollama format
                return {
                    "message": {
                        "content": result.message[0].content if result.message else ""
                    }
                }
            except Exception as e:
                raise RuntimeError(
                    f"Failed to communicate with Ollama via ollama_python: {e}"
                )

    # Replace ollama module with our adapter
    ollama = OllamaAdapter()

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
        # Enhanced developer message for better JSON output
        enhanced_dev_message = f"""
        You are a policy compiler. Generate a JSON policy specification from the given norms.
        
        Output format:
        {{
          "domain": "{self.domain}",
          "version": "1.0",
          "rules": [
            {{
              "id": "rule_1",
              "description": "Clear description",
              "pattern": "regex_pattern",
              "severity": "low|medium|high|critical",
              "rationale": "Why this rule exists"
            }}
          ],
          "metadata": {{}}
        }}
        
        Reasoning effort: {self.reasoning_effort}
        {developer_message}
        """

        # Create user prompt
        user_prompt = f"""
        Transform the following organizational norms into a structured JSON policy:

        {norms_text}

        Requirements:
        - Generate regex patterns that can detect violations
        - Provide clear rationale for each rule
        - Include appropriate severity levels
        - Show your reasoning process in audit_notebook

        **THINKING:**
        [Detailed chain-of-thought analysis]

        **POLICY:**
        ```json
        {{
          "domain": "{self.domain}",
          "version": "1.0",
          "rules": [
            {{
              "id": "rule_001",
              "description": "Rule description",
              "pattern": "regex_pattern_for_detection",
              "severity": "high|medium|low",
              "rationale": "Explanation for this rule"
            }}
          ],
          "metadata": {{}}
        }}
        ```
        """

        try:
            # Send request to Ollama
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": enhanced_dev_message},
                    {"role": "user", "content": user_prompt},
                ],
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": max_tokens,
                },
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
            thinking_match = re.search(
                r"\*\*THINKING:\*\*(.*?)\*\*POLICY:\*\*",
                output_text,
                re.DOTALL | re.IGNORECASE,
            )
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
