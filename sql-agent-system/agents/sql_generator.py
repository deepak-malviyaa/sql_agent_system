import re
from langchain_core.prompts import ChatPromptTemplate
from config import LLMFactory
from tools.schema_rag import get_relevant_schema
from tools.query_history import get_query_history

def clean_sql_output(text: str) -> str:
    """
    Forcefully extracts SQL from mixed text.
    """
    # 1. If inside markdown code blocks, extract that
    if "```" in text:
        pattern = r"```sql(.*?)```"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try generic code block if sql tag missing
        pattern = r"```(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

    # 2. If no markdown, but text contains multiple queries or conversational filler,
    # we take everything before the first semicolon.
    if ";" in text:
        text = text.split(";")[0] + ";"
        
    # 3. Remove conversational prefixes if they still exist
    text = re.sub(r"^(Here is the SQL|Sure|The query is):", "", text, flags=re.IGNORECASE)
    
    return text.strip()

def sql_generator_agent(state):
    print("⚡ [SQL Agent] Generating code...")
    llm = LLMFactory.get_llm("fast") # Groq
    
    # Retrieve Schema
    schema = get_relevant_schema(state["question"])
    
    # Check if we have retry guidance from the retry agent
    retry_guidance = state.get("retry_guidance", "")
    
    # 🧠 LEARNING FEATURE: Get similar successful queries from history
    query_history = get_query_history()
    learning_examples = query_history.get_learning_examples(state["question"], limit=3)
    
    if learning_examples:
        print("   📚 [Learning] Found similar past queries to learn from")
    
    # Enhanced prompt with learning examples
    prompt_template = """
    You are a specialized SQL compiler for PostgreSQL. 
    Your ONLY task is to convert the Intent into a SQL query based on the Schema.
    
    SCHEMA:
    {schema}
    
    INTENT:
    {intent}
    
    PREVIOUS ERROR (If any):
    {error}
    
    {retry_guidance_section}
    
    {learning_examples_section}
    
    STRICT RULES:
    1. Output ONLY the raw SQL code. 
    2. Do NOT use Markdown formatting (no ```sql ... ```).
    3. Do NOT add explanations, apologies, or introductions.
    4. Do NOT offer alternative queries.
    5. Use the exact table and column names from the SCHEMA. Do not hallucinate 'sale_amount' if the column is 'amount'.
    6. If RETRY GUIDANCE is provided above, follow it EXACTLY to fix the previous error.
    
    SQL CODE:
    """
    
    # Add retry guidance section if available
    retry_guidance_section = ""
    if retry_guidance:
        retry_guidance_section = f"""
    ⚠️ RETRY GUIDANCE FROM AGENT:
    {retry_guidance}
    
    YOU MUST follow this guidance to correct the previous error.
    """
    
    # Add learning examples section
    learning_examples_section = ""
    if learning_examples:
        learning_examples_section = f"""
    📚 LEARNING FROM PAST SUCCESSFUL QUERIES:
    Here are similar questions that were successfully answered:
    {learning_examples}
    
    Use these as reference for style and structure, but adapt to current question.
    """
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    chain = prompt | llm
    res = chain.invoke({
        "intent": state["user_intent"],
        "schema": schema,
        "error": state.get("error", ""),
        "retry_guidance_section": retry_guidance_section,
        "learning_examples_section": learning_examples_section
    })
    
    # Apply the cleaner function
    final_sql = clean_sql_output(res.content)
    
    return {"generated_sql": final_sql, "schema_context": schema}