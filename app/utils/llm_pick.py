from langchain_groq import ChatGroq
from app.config.config import settings
from app.utils.logger import logger

def pick_llm(level : str):
    """
    Picks the appropriate LLM based on the level of the question.

    Args:
        level (str): The level of the question, can be "low", "medium", or "high".

    Returns:
        ChatOpenAI: The LLM instance to be used.
    """
    api_key = settings.groq_api_key

    if not api_key:
        logger.error(f"GROQ API KEY is missing!")
        raise ValueError(
            "GROQ_API_KEY is missing. Check your project's .env file."
        )

    if level.lower() == "low":
        llm = ChatGroq(
            model_name =  "openai/gpt-oss-20b",
            temperature = 0,
            api_key=api_key,
            reasoning_effort="low"
        )

    elif level.lower() == "medium":
        llm = ChatGroq(
            model_name =  "llama-3.3-70b-versatile",
            temperature = 0,
            api_key=api_key,
            reasoning_effort="low"
        )

    elif level.lower() == "high":
        llm = ChatGroq(
            model_name =  "openai/gpt-oss-120b",
            temperature = 0,
            api_key=api_key,
            reasoning_effort="low"
        )

    else:
        logger.error(f"Unsupported level: {level}")
        raise ValueError(f"Unsupported level: {level}")

    return llm



if __name__ == "__main__":
    llm_obj = pick_llm("low")  
    logger.info(llm_obj.invoke("What is the capital of France?"))