import os
import logging
from pathlib import Path
from jinja2 import Template

logger = logging.getLogger(__name__)

# Root prompts directory inside the LLM service
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def load_prompt_template(name: str, version: str = "v1") -> str:
    """
    Loads a versioned prompt template from the app/prompts/ directory.
    E.g. load_prompt_template("auditor", "v1") reads app/prompts/auditor_v1.xml.
    """
    filename = f"{name}_{version}.xml"
    file_path = PROMPTS_DIR / filename
    
    if not file_path.exists():
        # Fallback to general file name if versioned suffix not found
        fallback_filename = f"{name}.xml"
        fallback_path = PROMPTS_DIR / fallback_filename
        if fallback_path.exists():
            return fallback_path.read_text(encoding="utf-8")
            
        logger.error(f"Prompt template {filename} or fallback does not exist at {PROMPTS_DIR}")
        raise FileNotFoundError(f"Template not found: {filename}")
        
    return file_path.read_text(encoding="utf-8")

def render_prompt(name: str, variables: dict, version: str = "v1") -> str:
    """
    Loads a prompt template and renders it using Jinja2 with variable placeholders.
    """
    template_str = load_prompt_template(name, version)
    template = Template(template_str)
    return template.render(**variables)
