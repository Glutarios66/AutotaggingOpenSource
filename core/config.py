# Note: Create a .env file in the root directory with the following content:
# AI_API_KEY='your_api_key_here'

# core/config.py

# --- Debug Mode Configuration ---
DEBUG_MODE = {
    "enabled": False,
    "log_level_debug": True,
    "override_llm_model": "gemini-2.5-flash-lite",
    "terminate_after_n_cycles": 2,
}

# --- Model Selection ---
AI_MODELS = {

    "gpt": {
        "smart": "gpt-5",           # best reasoning / quality
        "balanced": "gpt-4o",       # strong + fast
        "fast": "gpt-4o-mini",      # cheap + fast
    },

    "claude": {
        "smart": "claude-3.5-sonnet",  # best overall Claude
        "fast": "claude-3-haiku",      # very fast + cheap
    },

    "gemini": {
        "smart": "gemini-2.5-pro",
        "fast": "gemini-2.5-flash",
        "cheap": "gemini-2.5-flash-lite",
    },

    "qwen": {
        "smart": "qwen2.5-72b-instruct",
        "balanced": "qwen2.5-14b-instruct",
        "fast": "qwen2.5-7b-instruct",
    },

    "llama": {
        "smart": "llama-3-70b",
        "fast": "llama-3-8b",
    },

    "mistral": {
        "smart": "mistral-large",
        "fast": "mistral-small",
    }
}

LLM_DEFAULT_MODEL = AI_MODELS['gpt']


PROMPT_TEMPLATE_DIR = 'prompt_templates'
REDIS_DEFAULT_HOST = 'localhost'
REDIS_DEFAULT_PORT = 6379
REDIS_MAX_RETRIES = 5