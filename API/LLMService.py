from langchain_openai import OpenAI, ChatOpenAI
from langchain_anthropic import ChatAnthropic

class LLMService:
    def __init__(self):
        self.llm_lookup = {
            ("OpenAI", "gpt-4o-2024-08-06"): ChatOpenAI(model_name="gpt-4"),
            ("Claude", "claude-3-opus-20240229"): ChatAnthropic(model="claude-3-opus-20240229")  # Example, replace with actual model
        }

    def get_llm(self, model_name: str, version: str):
        return self.llm_lookup.get((model_name, version), None)