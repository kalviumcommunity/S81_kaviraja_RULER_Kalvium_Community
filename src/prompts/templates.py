class PromptTemplate:
    """
    A simple wrapper around a string template to allow named placeholder formatting.
    """
    def __init__(self, template: str):
        self.template = template

    def render(self, **kwargs) -> str:
        """
        Inject dynamic values into the template.
        """
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")

# Predefined templates
RAG_SYSTEM_PROMPT = PromptTemplate(
    "You are a helpful {role} specialized AI assistant."
)

RAG_USER_PROMPT = PromptTemplate(
    "Explain what {topic} is in {length} concise sentences."
)
