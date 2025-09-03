from openai_harmony import (
    SystemContent,
    Message,
    Conversation,
    Role,
    load_harmony_encoding,
    HarmonyEncodingName
)
from pathlib import Path
from typing import List
from datetime import datetime


def decode_tokens(token_ids: List[int]) -> str:
    """
    Decode token IDs back to text using Harmony encoding.

    Args:
        token_ids: List of token IDs from model response

    Returns:
        Decoded text string
    """
    encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
    return encoding.decode(token_ids)


def create_system_message(
    domain: str,
    reasoning_effort: str = "medium",
    developer_message: str = "",
    use_browser: bool = False,
    use_python: bool = True,
) -> Message:
    """
    Creates the SYSTEM message content with Harmony format for gpt-oss.

    Args:
        domain: Policy domain for context (e.g., 'content moderation')
        reasoning_effort: Str 'low'/'medium'/'high' controlling model effort
        developer_message: Optional instructions for the model developer
        use_browser: Enable Browser tool usage
        use_python: Enable Python tool usage

    Returns:
        A Harmony SYSTEM Message
    """
    # Capitalize reasoning effort for Harmony format
    effort_map = {
        "low": "Low",
        "medium": "Medium", 
        "high": "High"
    }
    capitalized_effort = effort_map.get(reasoning_effort.lower(), "Medium")
    
    system_content = SystemContent.new()\
        .with_conversation_start_date(datetime.now().strftime("%Y-%m-%d"))\
        .with_reasoning_effort(capitalized_effort)\
        .with_model_identity("gpt-oss")

    if use_browser:
        system_content = system_content.with_browser_tool()
    if use_python:
        system_content = system_content.with_python_tool()

    return Message.from_role_and_content(Role.SYSTEM, system_content)


def create_user_message(content: str) -> Message:
    """
    Create a USER message with given content.

    Args:
        content: The user prompt (e.g., the policy norms text)

    Returns:
        A Harmony USER Message
    """
    return Message.from_role_and_content(Role.USER, content)


def create_conversation(system_msg: Message, user_msg: Message) -> Conversation:
    """
    Combine SYSTEM and USER messages into a Conversation

    Args:
        system_msg: SYSTEM message
        user_msg: USER message

    Returns:
        Conversation ready for tokenization
    """
    return Conversation.from_messages([system_msg, user_msg])


def encode_conversation(conversation: Conversation) -> List[int]:
    """
    Render conversation to token IDs using Harmony encoding.

    Args:
        conversation: A Harmony Conversation object

    Returns:
        List of token IDs (integers)
    """
    encoding = load_harmony_encoding(HarmonyEncodingName.HARMONY_GPT_OSS)
    return encoding.render_conversation_for_completion(conversation, Role.ASSISTANT)


def create_policy_generation_prompt(
    domain: str,
    norms_content: str,
    reasoning_effort: str = "medium",
    use_python: bool = True
) -> List[int]:
    """
    Create a complete policy generation prompt and encode it for gpt-oss.

    Args:
        domain: Policy domain (e.g., 'content-moderation', 'code-review')
        norms_content: The organizational norms/rules text
        reasoning_effort: Reasoning effort level ('low', 'medium', 'high')
        use_python: Whether to enable Python tool for policy testing

    Returns:
        Token IDs ready for gpt-oss model inference
    """
    prompt_template = f"""You are JUSTITIA, an AI policy compiler for the "{domain}" domain.

Your task is to transform organizational norms into executable, auditable policies with transparent reasoning.

## Input Norms:
{norms_content}

## Instructions:
1. Analyze the norms carefully using chain-of-thought reasoning
2. Generate a structured policy in JSON format
3. Include clear decision criteria and examples
4. Provide audit trail of your reasoning process
5. If Python tools are available, create test cases

## Output Format:
```json
{{
  "domain": "{domain}",
  "policy": {{
    "rules": [...],
    "criteria": [...],
    "examples": [...]
  }},
  "reasoning": "Your detailed chain-of-thought process",
  "test_cases": [...] 
}}
```

Generate the policy now:"""

    system_msg = create_system_message(domain, reasoning_effort, use_python=use_python)
    user_msg = create_user_message(prompt_template)
    conversation = create_conversation(system_msg, user_msg)
    
    return encode_conversation(conversation)