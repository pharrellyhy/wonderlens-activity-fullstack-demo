# Switch Director & Script Agents to OpenAI GPT-5.2

## Changes

### 1. Config (`config.py` + `config.yaml` + `.env.example`)
- Add `openai_api_key` and `openai_base_url` settings (from .env)
- Add `openai_model` setting (from config.yaml, default "gpt-5.2")
- Increase timeouts since OpenAI may have different latency profile

### 2. Dependencies (`pyproject.toml`)
- Ensure `openai` is in dependencies

### 3. Director Agent (`agents/director.py`)
- Replace Gemini client with OpenAI AsyncOpenAI client
- Use structured outputs (response_format with json_schema) for CompositionPlan
- Keep same timeout/fallback logic

### 4. Script Agent (`agents/script_agent.py`)
- Replace Gemini client with OpenAI AsyncOpenAI client
- Use structured outputs for VoiceScript
- Keep same timeout/fallback logic

## Not Changed
- Vision (stays Gemini — image analysis)
- TTS (stays Gemini TTS — audio synthesis)
- Visual Agent (rule-based, no LLM)
- Recipe Assembler (no LLM)
