
import textwrap
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, SystemMessage
from typing import List, Any, Dict
from pydantic import BaseModel, Field
import asyncio


load_dotenv(override=True)

class State(TypedDict):
    messages : Annotated[List[str],add_messages];


class EvaluationOutput(BaseModel):
    search_places : List[str] = Field(description="Websites list from which the target roles were searched");
    relevance : str = Field(description="Relevance of the resume when compared with the current job requirements of the target roles");
    relevance_rating : int = Field(description="Rating out of 10 for the relevance of the resume with the current job requirements of the target roles");
    skill_gap : str = Field(description="SKills that are not present in the resume but are required in most of the jobs in the target roles");
    ats_friendliness : str = Field(description="How ATS friendly is the resume and what modifications can be done to enhance it")
    length : str = Field(description="How appropriate is the length of the resume for the total experience of the candidate. Suggest a change in length if required")
    hiring_manager_affinity : str = Field(description="How likely it is to get noticed or selected by a hiring manager for the target roles with the current resume")
    unnecesary : str = Field(description="Is there any absolutely unnecessary content in the resume for the target roles. If yes, suggest to remove it")
    summary : str = Field(description="Resume analysis summary in simple human like language")


class GraphRequest(BaseModel):
    history : List[Dict[str,str]];
    session_id : str


def ensure_system_message(messages, system_message):
    for m in messages:
        if isinstance(m,SystemMessage):
            m.content = system_message
            return messages
        
    return [SystemMessage(content=system_message)] + list(messages)


def evaluation_to_messages(evaluation_output : EvaluationOutput) -> str:
    msg =  f"""
        🗓️ Search sites
        {evaluation_output.search_places}
        📌 Relevance
        {evaluation_output.relevance}
        ⭐ Relevance Rating (out of 10)
        {evaluation_output.relevance_rating}/10
        🧩 Skill Gaps
        {evaluation_output.skill_gap}
        🤖 ATS Friendliness
        {evaluation_output.ats_friendliness}
        📄 Resume Length
        {evaluation_output.length}
        👔 Hiring Manager Affinity
        {evaluation_output.hiring_manager_affinity}
        🗑️ Unnecessary Content
        {evaluation_output.unnecesary}
        🗓️ Summary
        {evaluation_output.summary}
    """.strip()

    return textwrap.dedent(msg).strip()




def router_to_tools(state: State):
    lst_msg = state["messages"][-1]

    if hasattr(lst_msg, "tool_calls") and lst_msg.tool_calls:
        return "tools"
    else:
        return "EvaluatorAgent"



async def build_graph(tools,llm):

    async def InformationAgent(state : State) -> Dict[str, Any]:
        llm_tools= llm.bind_tools(tools);

        system_message = f"""

        You are an information gatherer for resume evaluator.
        You are given a resume and a list of target roles. 
        You shall use the provided tools to search the job descriptions of all the target roles in all the job board websites such as linkedin , indeed, etc.
        Collate all the requirements for the target roles and respond with that information.

        """

        messages = ensure_system_message(state["messages"], system_message)

        response = await llm_tools.ainvoke(messages)

        return {"messages" : [response]}


    async def EvaluatorAgent(state : State) -> Dict[str, Any]:
        llm_with_so = llm.with_structured_output(EvaluationOutput)

        system_message = f"""

        You are a resume evaluator.
        You are given a resume and a list of target roles and the requirements for such target roles from across multiple job board websites. 
        You shall use the provided information to compare the resume with the information from job board sites and evaluate the resume.

        """

        messages = ensure_system_message(state["messages"],system_message)

        response = await llm_with_so.ainvoke(messages)

        response = evaluation_to_messages(response)

        return {"messages" : [AIMessage(content=response)]}

    graph_builder = StateGraph(State)
    graph_builder.add_node("InformationAgent" , InformationAgent)
    graph_builder.add_node("EvaluatorAgent",EvaluatorAgent)
    graph_builder.add_node("tools", ToolNode(tools=tools))
    graph_builder.add_edge(START,"InformationAgent")
    graph_builder.add_edge("EvaluatorAgent",END)
    graph_builder.add_conditional_edges(
        "InformationAgent",router_to_tools,{"tools" : "tools", "EvaluatorAgent" : "EvaluatorAgent"}
    )
    graph_builder.add_edge("tools","InformationAgent")
    graph = graph_builder.compile(checkpointer=MemorySaver())
    #png = graph.get_graph().draw_mermaid_png()
    #with open("graph.png", "wb") as f:
        #f.write(png)
    
    return graph


async def run_superstep(message, history, graph, session_id):
    config = {"configurable" : {"thread_id" : session_id}}

    state = {

        "messages" : message,
        
    }

    result = await graph.ainvoke(state, config = config)

    

    reply = {"role" : "assistant", "content" : result["messages"][-1].content}

    partial_reply = ""

    for word in reply["content"].split(" "):
        partial_reply += f"{word} "
        await asyncio.sleep(0.05)
        yield partial_reply
    
    yield partial_reply



