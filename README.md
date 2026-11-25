# Answer Sheet Evaluator
Compares a student's answer with a model answer using an LLM and suggests marks, missing points and feedback.

## Setup
    pip install -r requirements.txt
    export GROQ_API_KEY=...        # or GEMINI_API_KEY / OPENAI_API_KEY (Windows: set GROQ_API_KEY=...)
    streamlit run app.py

Pick the provider in the sidebar. For a local model: install Ollama, run `ollama pull llama3.1`, choose "Ollama (local)".

## Files
- app.py: Streamlit UI
- evaluator.py: LLM call, JSON parsing, mark calculation
- prompts.py: system prompt with scoring rubric
- test_evaluator.py: offline tests for scoring/parsing
- sample_input.md: example to try
