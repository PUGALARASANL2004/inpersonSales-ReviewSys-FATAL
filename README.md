# In-Person Review System

A comprehensive call quality review system for real estate pre-sales calls. This system transcribes audio calls, analyzes transcripts against detailed quality rubrics, and generates comprehensive scoring reports with audio analysis and emotion detection.

## 🎯 Overview

The In-Person Review System evaluates sales/support calls using:
- **Audio Transcription**: Speaker diarization and transcription via Soniox STT
- **Intelligent Scoring**: LLM-powered evaluation against YAML rubrics (OpenAI GPT-4)
- **Dual Scoring Systems**: V1 (binary yes/no) and V2 (granular 0-max scoring)
- **Audio Analysis**: Emotion detection, talk-time metrics, and poor segment flagging
- **Comprehensive Reporting**: Detailed scoring reports with evidence, timestamps, and recommendations

## ✨ Features

### Core Capabilities
- **Multi-Speaker Transcription**: Automatic speaker diarization with timestamps
- **Rubric-Based Scoring**: Configurable YAML rubrics for different projects (Empire, GSquare)
- **Granular Scoring (V2)**: 0-max point scoring system with partial credit support
- **Project Knowledge Validation**: Strict validation against Ready Reckoner and FAQ data
- **Evidence-Based Evaluation**: All scores backed by timestamped transcript evidence
- **Audio Metrics**: Talk-time share, pause detection, pace analysis
- **Emotion Detection**: Text and audio-based emotion analysis with fusion
- **Deal Management**: SQLite database for storing reviews and comments
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Modern UI**: React-based dashboard for review management

### Scoring Systems

**V1 (Binary)**: Traditional yes/no/NA scoring for quick evaluations

**V2 (Granular)**: Advanced 0-max scoring system with:
- Partial credit for incomplete execution
- NA scoring (-1) for genuinely inapplicable parameters
- Strict project knowledge validation
- Comprehensive evidence collection with timestamps
- Category-wise and parameter-wise breakdowns

## 🏗️ Architecture

### Tech Stack

**Backend:**
- FastAPI (Python 3.10+)
- OpenAI GPT-4 for scoring
- Soniox for speech-to-text transcription
- SQLite for data storage
- PyYAML for rubric management

**Frontend:**
- React 19
- Modern responsive UI

**Key Libraries:**
- `boto3` - AWS integration (SageMaker SER)
- `librosa` - Audio processing
- `transformers` - ML models
- `pydantic` - Data validation

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm
- API Keys:
  - OpenAI API key (for scoring)
  - Soniox API key (for transcription)
  - AWS credentials (optional, for SER endpoint)

### Installation

#### 1. Backend Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

# Install dependencies
# Option 1: Using pip
pip install -r requirements.txt

# Option 2: Using uv (recommended for faster installation)
uv pip install -r requirements.txt
```

#### 2. Environment Configuration

Create a `.env` file in the repository root:

```env
# Required
OPENAI_API_KEY=your_openai_api_key
SONIOX_API_KEY=your_soniox_api_key

# Optional - Soniox Configuration
SONIOX_API_BASE_URL=https://api.soniox.com
SONIOX_MODEL_ID=stt-async-v3

# Optional - OpenAI Configuration
OPENAI_MODEL=gpt-4o-mini

# Optional - AWS Configuration (for SER)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
SAGEMAKER_SER_ENDPOINT_NAME=your-ser-endpoint
```

#### 3. Frontend Setup

```bash
cd ui
npm install

# Optional: Create ui/.env for API configuration
# REACT_APP_API_BASE=http://localhost:8000
```

#### 4. Run the Application

**Start Backend:**
```bash
# Make sure venv is activated or use uv:
# Windows: .venv\Scripts\activate
# Then run:
uvicorn api.main:app --reload --port 8000

# Or using uv directly (no activation needed):
uv run uvicorn api.main:app --reload --port 8000
```

**Start Frontend:**
```bash
cd ui
npm start
```

Open http://localhost:3000 in your browser.

## 📁 Project Structure

```
InPerson-ReviewSys/
├── api/                          # FastAPI backend
│   ├── main.py                  # API endpoints
│   ├── config.py                # Configuration management
│   ├── transcription.py         # Audio transcription logic
│   ├── scoring.py               # V1 scoring system
│   ├── scoring_v2.py            # V2 granular scoring system
│   ├── reporting.py             # Report generation
│   ├── schemas.py               # Pydantic models
│   ├── empire_rubric.yaml       # V1 rubric (Empire)
│   ├── empire_rubric_v2.yaml    # V2 rubric (Empire)
│   └── gsquare_pointing.yaml    # GSquare rubric
├── ui/                          # React frontend
│   ├── src/
│   │   ├── App.js               # Main application component
│   │   └── ...
│   └── package.json
├── examples/                    # Example scripts
│   ├── score_single_call.py     # Single call scoring example
│   └── compare_v1_v2.py         # V1 vs V2 comparison
├── fuel-docs/                   # Project documentation
│   ├── Empire/                  # Empire project docs
│   ├── HappiNest/               # HappiNest project docs
│   └── GSquare/                 # GSquare project docs
├── scripts/                     # Utility scripts
│   ├── extract_empire_files.py  # Extract Empire data from PDFs/Excel
│   ├── extract_happinest_files.py # Extract HappiNest data from Excel
│   └── validate_v2_system.py    # V2 system validation
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔧 Configuration

### Scoring Configuration

Edit `api/config.py` or use environment variables:

- **Provider**: OpenAI (default) or Bedrock
- **Model**: `gpt-4o-mini` (default) or other OpenAI models
- **Temperature**: Controls randomness (default: 0.7)
- **Max Tokens**: Response length limit
- **Consensus Attempts**: Number of scoring runs for stability (default: 1)

### Rubric Configuration

Rubrics are YAML files in `api/` directory:
- `empire_rubric.yaml` - V1 binary scoring
- `empire_rubric_v2.yaml` - V2 granular scoring (100 points, 5 categories, 18 parameters)
- `gsquare_pointing.yaml` - GSquare project rubric

Each rubric defines:
- Categories and sub-parameters
- Point allocations
- Scoring criteria
- Project-specific knowledge validation rules

## 📡 API Endpoints

### Transcription

**POST `/transcribe-audio`**
- Upload audio file for transcription
- Returns: `{ transcription, speaker_segments, language_code }`
- Supports: WAV, M4A, MP3 formats

### Scoring

**POST `/score-transcript`**
- Score a transcript against the rubric
- Input: `{ transcription, speaker_segments, version: "v1" | "v2" }`
- Returns: Detailed scoring report with evidence

**POST `/generate-report`**
- Generate comprehensive review report
- Input: `{ transcript_data, score_data }`
- Returns: Formatted report with recommendations

### Root

**GET `/`**
- API information and available endpoints

## 💻 Usage Examples

### Python Script Example

```python
from api.scoring_v2 import score_transcript_main

transcript_data = {
    "transcription": "Agent: Good morning sir. This is Uma from Adityaram Property...",
    "speaker_segments": [
        {
            "speaker": "Agent",
            "start_time": 0.0,
            "end_time": 5.0,
            "text": "Good morning sir..."
        }
    ]
}

result = score_transcript_main(transcript_data)
print(f"Total Score: {result['summary']['total_score']}/100")
```

### Command Line Examples

**Note:** Make sure your virtual environment is activated (`.venv\Scripts\activate` on Windows) or use `uv run python` instead of `python`.

**Score a single call:**
```bash
# Using activated venv:
python examples/score_single_call.py
# Or using uv:
uv run python examples/score_single_call.py
```

**Compare V1 vs V2 scoring:**
```bash
python examples/compare_v1_v2.py
# Or: uv run python examples/compare_v1_v2.py
```

**Validate V2 system:**
```bash
python scripts/validate_v2_system.py
# Or: uv run python scripts/validate_v2_system.py
```

**Extract Empire project data:**
```bash
python scripts/extract_empire_files.py
# Or: uv run python scripts/extract_empire_files.py
```

**Extract all projects (Empire + HappiNest) into combined knowledge file:**
```bash
python scripts/extract_all_projects.py
# Or: uv run python scripts/extract_all_projects.py
```

**Note:** The combined extraction script creates a single `fuel-docs/project_knowledge.json` file containing both Empire and HappiNest data. This is the preferred method going forward.

## 📊 Scoring System Details

### V2 Granular Scoring

The V2 system evaluates calls across 5 categories (100 total points):

1. **Greeting** (9 points)
   - Brand introduction
   - Self-introduction
   - Customer identity confirmation

2. **Project Knowledge** (48 points)
   - Project details accuracy
   - Pricing and plot size accuracy
   - Location information
   - Amenities knowledge

3. **Process Knowledge** (10 points)
   - Booking process
   - Payment plans
   - Documentation requirements

4. **Soft Skills** (28 points)
   - Tone and voice modulation
   - Active listening
   - Objection handling
   - Empathy and rapport

5. **Closing** (4 points)
   - Visit invitation
   - Follow-up confirmation
   - Brand mention
   - Professional closing

### Scoring Principles

- **Evidence-Based**: Every score requires timestamped evidence
- **Whole Transcript Analysis**: Evaluates entire conversation context
- **No Hallucination**: Only scores what's explicitly present
- **Project Knowledge Validation**: Strict validation against Ready Reckoner and FAQ
- **Cultural Context**: Supports Tamil-English code-mixing
- **NA Scoring**: Available for genuinely inapplicable parameters

## 🔍 Validation & Testing

### System Validation

Run the comprehensive validation suite:

```bash
python scripts/validate_v2_system.py
# Or: uv run python scripts/validate_v2_system.py
```

This validates:
- File existence and structure
- Module imports
- Rubric loading and alignment
- Scoring functionality
- Evidence format
- Project knowledge validation

### Testing Checklist

- [ ] All required files present
- [ ] Environment variables configured
- [ ] API endpoints accessible
- [ ] Transcription working
- [ ] V1 scoring functional
- [ ] V2 scoring functional
- [ ] Report generation working
- [ ] Database operations working

## 📝 Development Notes

### Database

- SQLite database: `deal_reviews.db`
- Stores: Reviews, scores, comments, deal information

### Temporary Files

- Audio uploads: `.tmp_audio/` (auto-cleaned after processing)
- Do not commit temporary files

### API Keys

- **Never commit** `.env` files or API keys
- Use environment variables or `.env` (gitignored)
- Rotate keys regularly

### Rubric Updates

When updating rubrics:
1. Update YAML file in `api/`
2. Run validation: `python scripts/validate_v2_system.py` (or `uv run python scripts/validate_v2_system.py`)
3. Test with sample transcripts
4. Update documentation if needed

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run validation: `python validate_v2_system.py`
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues or questions:
1. Check the validation output: `python scripts/validate_v2_system.py` (or `uv run python scripts/validate_v2_system.py`)
2. Review API logs for errors
3. Verify environment variables are set correctly
4. Ensure all dependencies are installed

## 🔗 Related Documentation

- **Empire Project**: See `fuel-docs/Empire/` for project-specific documentation
- **GSquare Project**: See `fuel-docs/GSquare/` for GSquare documentation
- **Examples**: See `examples/` directory for usage examples

---

**Built with ❤️ for quality call evaluation**
