import os
import logging
from typing import Dict

logger = logging.getLogger("ai_service.prompt_loader")

_PROMPT_CACHE: Dict[str, str] = {}

def get_prompts_dir() -> str:
    # 1. Check relative to app root (/app/prompts or ./prompts)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    prompts_dir = os.path.join(base_dir, "prompts")
    if os.path.isdir(prompts_dir):
        return prompts_dir
    
    # 2. Check /app/prompts inside Docker
    docker_dir = "/app/prompts"
    if os.path.isdir(docker_dir):
        return docker_dir

    return prompts_dir

def load_prompt(prompt_name: str) -> str:
    """
    Loads markdown prompt from prompts/<prompt_name>.md with memory caching.
    """
    filename = prompt_name if prompt_name.endswith(".md") else f"{prompt_name}.md"
    
    if filename in _PROMPT_CACHE:
        return _PROMPT_CACHE[filename]

    prompts_dir = get_prompts_dir()
    filepath = os.path.join(prompts_dir, filename)

    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                _PROMPT_CACHE[filename] = content
                return content
        else:
            logger.warning(f"Prompt file '{filepath}' not found. Falling back to default.")
    except Exception as e:
        logger.error(f"Error loading prompt '{filename}': {e}")

    return ""
