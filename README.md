# TutorBot Prompt System

A modular, decomposed prompt engineering system for educational AI assistants that help students with reading comprehension and science concepts.

## Project Overview

The TutorBot Prompt System uses decomposed prompt structures and best practices in prompt engineering to create specialized educational AI assistants. The system currently supports:

- **Reading Comprehension**: Text analysis, question generation, and comprehension assessment
- **Science Education**: Concept explanation, doubt classification, and understanding checks

## Key Features

- **Prompt Decomposition**: Breaking down complex educational tasks into manageable components
- **Context-Aware Prompting**: Adapting explanations to grade level and student needs
- **Structured Feedback Loop**: Continuously improving responses based on student interactions
- **Escalation Handling**: Knowing when to involve human teachers for complex cases

## Project Structure

```
TutorBotPromptSystem/
├── prompts/               # Prompt templates organized by subject
├── models/                # Model loading and configuration
├── utils/                 # Shared utilities and helpers
├── ui/                    # Streamlit UI (planned for future)
├── main.py                # Main application entry point
└── requirements.txt       # Project dependencies
```

## Setup Instructions

1. Clone and Fork the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate # On Mac 
   # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the main application:
   ```
   python main.py
   ```

## Usage Examples

(Examples will be added as the project develops)

## License

[MIT License](LICENSE) 