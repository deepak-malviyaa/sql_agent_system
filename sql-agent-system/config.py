import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

# Force reload of .env
load_dotenv(override=True)

class LLMFactory:
    @staticmethod
    def get_llm(model_type="reasoning"):
        # --- 1. DISABLE LANGFUSE (Temporarily) ---
        # Your network is blocking the connection, causing timeouts.
        callbacks = [] 
        # try:
        #     from langfuse.langchain import CallbackHandler
        #     langfuse_handler = CallbackHandler()
        #     callbacks.append(langfuse_handler)
        # except ImportError:
        #     pass

        # --- 2. GET PROVIDER ---
        # Default to gemini/groq if env vars are missing
        provider = os.getenv("MODEL_REASONING") if model_type == "reasoning" else os.getenv("MODEL_FAST")
        if not provider:
            provider = "gemini" if model_type == "reasoning" else "groq"

        # --- 3. RETURN MODELS ---
        if provider == "gemini":
            return ChatGoogleGenerativeAI(
                model="gemini-3-pro-preview", 
                temperature=0,
                callbacks=callbacks
            )
        elif provider == "groq":
            return ChatGroq(
                model_name="llama-3.1-8b-instant", 
                temperature=0,
                callbacks=callbacks
            )
        else:
            print(f"⚠️ Warning: Provider '{provider}' not recognized. Using Gemini.")
            return ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)