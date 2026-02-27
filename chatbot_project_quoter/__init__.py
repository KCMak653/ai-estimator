from .chatbot_project_quoter import ChatbotProjectQuoter, format_quote_as_string, format_quote_as_html

# Backward compatibility
format_quote = format_quote_as_string

__all__ = ["ChatbotProjectQuoter", "format_quote_as_string", "format_quote_as_html", "format_quote"]
