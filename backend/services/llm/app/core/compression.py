import re
import logging

logger = logging.getLogger(__name__)

def compress_prompt(prompt: str) -> str:
    """
    Optimizes the prompt content for efficient token usage:
    - Compresses repeated whitespaces and newlines.
    - Limits excessively large HTML snippets nested inside Axe violation logs.
    """
    # 1. Compress repeated whitespace / indentation spacing
    compressed = re.sub(r'[ \t]+', ' ', prompt)
    compressed = re.sub(r'\n+', '\n', compressed)
    
    # 2. Match and truncate large HTML block substrings
    # E.g., if a node includes a massive raw HTML body of 20KB+
    def truncate_large_html(match: re.Match) -> str:
        tag_name = match.group(1)
        tag_content = match.group(2)
        if len(tag_content) > 1000:
            logger.info(f"Compressor: Truncating large HTML snippet ({len(tag_content)} chars)")
            return f"<{tag_name} ... [HTML truncated for token efficiency: {len(tag_content)} chars] ... </{tag_name}>"
        return match.group(0)

    # Regex to capture HTML tags and their inner content
    # matches: <(div|svg|iframe|span|form|table) ...> ... </\1>
    tag_regex = r'<([a-zA-Z0-9]+)\b[^>]*>(.*?)</\1>'
    
    try:
        # Run standard tag replacement for tags spanning multiple lines
        compressed = re.sub(tag_regex, lambda m: truncate_large_html(m), compressed, flags=re.DOTALL)
    except Exception as e:
        logger.warning(f"Error compressing prompt HTML tags: {str(e)}")
        
    return compressed
