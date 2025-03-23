from fastapi import FastAPI,HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware


from database import startup
from api import router
from exception_handlers import validation_exception_handler,http_exception_handler


app = FastAPI(
    title="DeepMark",
    description="social media platform that ensures originality by preventing duplicate content uploads",
    version="0.1",
    
    
)

#Intializing Database
@app.on_event("startup")
async def on_startup():
    await startup()
    print("Database Succesfully Connected")

#Adding CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

#Adding Exception Handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

#Adding Main Router
app.include_router(router)

