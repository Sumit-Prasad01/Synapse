import os
import sys
from typing import Optional, Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.src.agents.data_agent import data_agent
from app.src.agents.sql_analyst import sql_analyst
from app.src.agents.etl_analyst import etl_analyst
from app.src.db.database import DataBaseUtil
from app.config.config import settings
from app.utils.logger import logger

app = FastAPI(
    title="Synapse AI Data Platform API",
    description="FastAPI Backend for Synapse: Intelligent SQL & ETL Agent",
    version="1.0.0",
)

# Enable CORS for frontend clients (Streamlit, React, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str = Field(..., description="The user's query or instruction for SQL analysis or ETL task")


class QueryResponse(BaseModel):
    question: str
    route: str
    answer: str
    sql_query: Optional[str] = None
    sql_result: Optional[str] = None
    is_safe: Optional[str] = None
    comments: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    database_connected: bool
    groq_api_key_configured: bool


def _extract_answer_from_messages(messages) -> str:
    """Helper to get the final text response from a list of LangChain messages."""
    if not messages:
        return ""
    last_item = messages[-1]
    if hasattr(last_item, "content"):
        return str(last_item.content)
    if isinstance(last_item, dict):
        if "final_answer" in last_item:
            return str(last_item["final_answer"])
        if "messages" in last_item and last_item["messages"]:
            return _extract_answer_from_messages(last_item["messages"])
    return str(last_item)


@app.get("/", tags=["General"])
def root():
    return {
        "message": "Welcome to Synapse AI Data Platform API",
        "docs_url": "/docs",
        "health_url": "/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
def health_check():
    db_ok = False
    try:
        db_util = DataBaseUtil({
            "host": settings.host,
            "port": settings.port,
            "user": settings.user,
            "password": settings.password,
            "dbname": settings.database_name,
        })
        if db_util.connection:
            db_ok = True
            db_util.connection.close()
    except Exception as e:
        logger.error(f"Health check DB error: {e}")
        db_ok = False

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        database_connected=db_ok,
        groq_api_key_configured=bool(settings.groq_api_key),
    )


@app.get("/api/schema", tags=["Database"])
def get_database_schema():
    """Retrieve database schema details for the public schema."""
    try:
        db_util = DataBaseUtil({
            "host": settings.host,
            "port": settings.port,
            "user": settings.user,
            "password": settings.password,
            "dbname": settings.database_name,
        })
        schema_info = db_util.schema_details("public")
        return {"schema": schema_info}
    except Exception as e:
        logger.error(f"Error retrieving schema: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch schema: {str(e)}")


@app.post("/api/query", response_model=QueryResponse, tags=["Agents"])
def query_agent(request: QueryRequest):
    """
    Unified endpoint: Routes the user question to either the SQL analyst
    or the ETL analyst via the LangGraph Data Agent.
    """
    try:
        logger.info(f"Received query: {request.question}")
        state_input = {
            "messages": [HumanMessage(content=request.question)],
            "route_response": ""
        }
        result = data_agent.invoke(state_input)
        route = result.get("route_response", "unknown")

        messages = result.get("messages", [])
        last_step = messages[-1] if messages else {}

        sql_query = None
        sql_result = None
        is_safe = None
        comments = None
        answer = ""

        if route == "sql" and isinstance(last_step, dict):
            answer = last_step.get("final_answer") or ""
            sql_query = last_step.get("generated_sql_query")
            sql_result = last_step.get("sql_query_execution_result")
            is_safe = last_step.get("is_safe")
            comments = last_step.get("comments")
        elif route == "etl" and isinstance(last_step, dict):
            etl_msgs = last_step.get("messages", [])
            answer = _extract_answer_from_messages(etl_msgs)
        else:
            answer = _extract_answer_from_messages(messages)

        return QueryResponse(
            question=request.question,
            route=route,
            answer=answer,
            sql_query=sql_query,
            sql_result=sql_result,
            is_safe=is_safe,
            comments=comments,
        )

    except Exception as e:
        logger.error(f"Error processing agent query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/sql", tags=["Agents"])
def direct_sql_query(request: QueryRequest):
    """Directly invokes the SQL Analyst graph without passing through the router."""
    try:
        input_schema = {
            "messages": [],
            "user_question": request.question,
            "curated_ques": "",
            "prompt_query_context": "",
            "generated_sql_query": "",
            "is_safe": "No",
            "comments": "",
            "sql_query_execution_result": "",
            "final_answer": "",
        }
        res = sql_analyst.invoke(input_schema)
        return {
            "question": request.question,
            "route": "sql",
            "curated_question": res.get("curated_ques"),
            "generated_sql_query": res.get("generated_sql_query"),
            "is_safe": res.get("is_safe"),
            "comments": res.get("comments"),
            "execution_result": res.get("sql_query_execution_result"),
            "final_answer": res.get("final_answer"),
        }
    except Exception as e:
        logger.error(f"Error in direct SQL query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/etl", tags=["Agents"])
def direct_etl_query(request: QueryRequest):
    """Directly invokes the ETL Analyst graph without passing through the router."""
    try:
        res = etl_analyst.invoke({
            "messages": [HumanMessage(content=request.question)]
        })
        answer = _extract_answer_from_messages(res.get("messages", []))
        return {
            "question": request.question,
            "route": "etl",
            "answer": answer,
        }
    except Exception as e:
        logger.error(f"Error in direct ETL query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, reload=True)
