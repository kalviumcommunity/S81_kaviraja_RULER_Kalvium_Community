class PromptTemplate:
    """
    A simple wrapper around a string template to allow named placeholder formatting.
    """
    def __init__(self, template: str, default_kwargs: dict = None):
        self.template = template
        self.default_kwargs = default_kwargs or {}

    def render(self, **kwargs) -> str:
        """
        Inject dynamic values into the template with flexible placeholder aliasing.
        """
        merged = {**self.default_kwargs, **kwargs}
        if "context_str" in merged and "context" not in merged:
            merged["context"] = merged["context_str"]
        elif "context" in merged and "context_str" not in merged:
            merged["context_str"] = merged["context"]

        if "query" in merged and "question" not in merged:
            merged["question"] = merged["query"]
        elif "question" in merged and "query" not in merged:
            merged["query"] = merged["question"]

        try:
            return self.template.format(**merged)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")

# Predefined templates
RAG_SYSTEM_PROMPT = PromptTemplate(
    "You are a helpful {role} specialized AI assistant.",
    default_kwargs={"role": "RAG"}
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
    f"{GROUNDING_INSTRUCTIONS}",
    default_kwargs={"role": "Banking Regulation & Financial Compliance"}
)

RAG_CONTEXT_INJECTION_USER_PROMPT = PromptTemplate(
    "[CONTEXT]\n"
    "{context}\n\n"
    "[QUESTION]\n"
    "{question}\n\n"
    "[ANSWER]"
)

# Aliases for grounded generator
RAG_GROUNDED_USER_PROMPT = PromptTemplate(
    "[CONTEXT]\n"
    "{context_str}\n\n"
    "[QUESTION]\n"
    "{query}\n\n"
    "[ANSWER]"
)

RAG_UNGROUNDED_USER_PROMPT = PromptTemplate(
    "[QUESTION]\n"
    "{query}\n\n"
    "[ANSWER]"
)



