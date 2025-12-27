from email import message
from fastapi import FastAPI,Request
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.runnables import history
from langgraph import graph
from app.resumeevaluator import GraphRequest, build_graph, run_superstep
from contextlib import asynccontextmanager
from langsmith import traceable

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.graph = build_graph()
    yield

app = FastAPI(lifespan=lifespan);

origins = os.getenv("CORS_ORIGINS","http://localhost:3000").split(",")
app.add_middleware(
 CORSMiddleware,
 allow_origins=origins,
 allow_credentials = False,
 allow_methods=["GET","POST","OPTIONS"],
 allow_headers=["*"],

)



@app.get("/")
async def root():
    return{
        "message" : "It's working my friend!"
    }

@traceable
@app.post("/chat")
async def chat(graph_request : GraphRequest, request : Request):

    graph = request.app.state.graph
    message = graph_request.history[-1]["content"]
    last_reply =None
    async for reply in run_superstep(message=message, history= graph_request.history, graph=graph,session_id=graph_request.session_id):
        last_reply = reply


    return last_reply.strip()

if __name__ == "main":
    import uvicorn;

    uvicorn.run(app, host="0.0.0.0", port=8000);