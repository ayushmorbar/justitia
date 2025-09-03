# 🏛️ JUSTITIA ⚖️

**Justified System for Transparent Institutional Trust Intelligence & Audit**

Transform organizational norms into executable, auditable policies with transparent reasoning.

## 🎯 OpenAI Open Model Hackathon 2025

Built with gpt-oss models showcasing:
- 🔧 **Harmony format** for structured policy generation
- 🧠 **Transparent chain-of-thought** reasoning for audit trails  
- 🐍 **Python tool integration** for executable policy tests
- 🔒 **Offline-first operation** for sensitive organizational data
- ⚖️ **Apache 2.0 licensed** for enterprise adoption

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Linux/macOS:**
```bash
git clone https://github.com/ayushmorbar/justitia.git
cd justitia
chmod +x setup.sh
./setup.sh
```

**Windows PowerShell:**
```powershell
git clone https://github.com/YOUR-USERNAME/justitia.git
cd justitia
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser # If needed
.\setup.ps1
```

### Option 2: Manual Setup

**Install Ollama**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull gpt-oss:20b
```

**Setup Python environment**
```bash
python -m venv venv
source venv/bin/activate # Linux/macOS
# or: venv\Scripts\activate # Windows
pip install -r requirements.txt
pip install -e .
```

## 🖥️ Usage Options

### Interactive Terminal UI (Recommended)
```bash
python run_tui.py
```
- Beautiful terminal interface
- Real-time policy generation
- Sample templates included
- Visual feedback and progress

### Command Line Interface
```bash
# Create sample project
justitia create-samples content-moderation

# Generate policy from norms
justitia generate --input examples/content-moderation/norms.txt --effort high --output ./policy-output/

# Test generated policy
justitia test --policy policy-output/policy.json --cases examples/content-moderation/test_cases.json

# View all options
justitia --help
```

## 📁 Project Structure

```
justitia/
├── justitia/           # Core package
│   ├── cli.py          # Command-line interface
│   ├── tui.py          # Terminal user interface
│   ├── harmony.py      # gpt-oss Harmony integration
│   ├── policy.py       # Policy generation engine
│   └── tests.py        # Testing framework
├── examples/           # Sample domains
│   ├── content_moderation/
│   └── code_review/
├── run_tui.py          # TUI launcher
└── setup.sh            # Environment setup
```

## 🎬 Demo Video

[![JUSTITIA Demo](https://img.shields.io/badge/▶️-Watch%20Demo-red?style=for-the-badge)](YOUR_DEMO_VIDEO_URL)

## 🏆 Hackathon Categories

- 🥇 **Best Overall** - Unique gpt-oss application with transparent governance
- 🤖 **Best Local Agent** - Complete offline operation for privacy  
- 🔧 **Most Useful Fine-Tune** - Domain-tailored policy generation

## 🔍 What Makes JUSTITIA Unique

Unlike generic chatbots or RAG systems, JUSTITIA:

1. **Compiles executable policies** - Not just text, but runnable tests
2. **Shows transparent reasoning** - Full audit trail of AI decisions
3. **Works completely offline** - No data leaves your system
4. **Validates with evidence** - Measure false positives/negatives
5. **Scales across domains** - Content, code, compliance, and more

## 📊 Example Output

**Input Norms:**
```
Our platform prohibits hate speech and harassment.
No personal attacks or discriminatory language allowed.
```

**Generated Policy:**
```json
{
  "domain": "content-moderation",
  "rules": [
    {
      "id": "hate_speech_detection",
      "description": "Detect hate speech and discriminatory language",
      "pattern": "\\b(hate|despise|loathe)\\s+(those|these)\\s+(people|users|folks)",
      "severity": "high",
      "rationale": "Targets groups with derogatory language indicating hate speech"
    }
  ]
}
```

**Test Results:**
```
✅ PASS: hate_speech_1 (Score: 1.00)
❌ FAIL: edge_case_2 (Score: 0.67) - FN: personal_attacks
✅ PASS: clean_content_1 (Score: 1.00)

📊 Summary: 67% pass rate, 0.89 average score
```

## 🛠️ Technical Architecture

- **Frontend**: Textual TUI + Typer CLI
- **AI Engine**: gpt-oss-20b via Ollama
- **Format**: OpenAI Harmony for structured prompts
- **Testing**: Regex + Python execution sandbox
- **Storage**: Local JSON + SQLite
- **Deployment**: Single-command setup scripts

## 🤝 Contributing

Built for the OpenAI Open Model Hackathon 2025. Contributions welcome after the competition!

## 📄 License

Apache 2.0 - See [LICENSE](LICENSE) for details.

---

**Built with ❤️ for transparent governance and AI accountability by [Offbeats Labs](https://github.com/Offbeatshq)**

*"Making AI decision-making visible, testable, and trustworthy"*
