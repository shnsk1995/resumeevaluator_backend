import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Dict, Optional
from pydantic import BaseModel, Field
import uuid
import asyncio


load_dotenv(override=True)

class State(TypedDict):
    messages : Annotated[List[Any],add_messages];
    target : List[str];


class EvaluationOutput(BaseModel):
    relevance : str = Field(description="Relevance of the resume when compared with the current job requirements of the target roles");
    relevance_rating : int = Field(description="Rating out of 10 for the relevance of the resume with the current job requirements of the target roles");
    skill_gap : str = Field(description="SKills that are not present in the resume but are required in most of the jobs in the target roles");
    ats_friendliness : str = Field(description="How ATS friendly is the resume and what modifications can be done to enhance it")
    length : str = Field(description="How appropriate is the length of the resume for the total experience of the candidate. Suggest a change in length if required")
    hiring_manager_affinity : str = Field(description="How likely it is to get noticed or selected by a hiring manager for the target roles with the current resume")
    unnecesary : str = Field(description="Is there any absolutely unnecessary content in the resume for the target roles. If yes, suggest to remove it")


class GraphRequest(BaseModel):
    resume : str;
    target_roles : str;
    session_id : Optional[str] = None


def EvaluatorAgent(state : State) -> Dict[str, Any]:
    tools= "";
    llm = ChatOpenAI(model="gpt-4o-mini");
    llm_tools= llm.bind_tools(tools);
    llm_with_so = llm_tools.with_structured_output(EvaluationOutput);

    system_message = f"""

    You are a resume evaluator.
    You are given a resume and a list of target roles. 
    You shall use the appropriate tools to search the job descriptions of all the target roles in all the job board websites such as linkedin , indeed, etc.
    Collate all the requirements for the target roles and compare them with the resume to evaluate the resume for different metrics as described in {EvaluationOutput}.
    You will only respond in the requested structured output format and avoid any hallucinations.

"""

    response = llm_with_so.invoke(state["messages"])
