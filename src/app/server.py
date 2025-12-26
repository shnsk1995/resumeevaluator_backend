from fastapi import FastAPI
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI();

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

@app.post("/chat")
async def chat():

    

    return{
        "message" : "It's working my friend!"
    }

if __name__ == "main":
    import uvicorn;

    uvicorn.run(app, host="0.0.0.0", port=8000);