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
#explain me the funtion
RAG_USER_PROMPT = PromptTemplate(
    "Explain what {topic} is in {length} concise sentences."
)

# Task 4 & Task 1: Strict Grounding & Context-Injection Prompt Templates
GROUNDING_INSTRUCTIONS = (
    "GROUNDING RULES:\n"
    "1. Answer the user's question ONLY using the factual information provided in the [CONTEXT] section below.\n"
    "2. Do NOT assume, extrapolate, or invent facts outside the provided context.\n"
    "3. Cite your sources using the chunk markers (e.g. [1], [2], or [Source X]) whenever stating a factual claim.\n"
    "4. If the provided context is insufficient or does not contain the answer, you MUST explicitly state: "
    "\"The provided context does not contain sufficient information to answer this question.\" Do not attempt to guess."
)

RAG_GROUNDED_SYSTEM_PROMPT = PromptTemplate(
    "You are an expert AI assistant specialized in {role}.\n\n"
    f"{GROUNDING_INSTRUCTIONS}"
)

RAG_CONTEXT_INJECTION_USER_PROMPT = PromptTemplate(
    "[CONTEXT]\n"
    "{context}\n\n"
    "[QUESTION]\n"
    "{question}\n\n"
    "[ANSWER]"
)

