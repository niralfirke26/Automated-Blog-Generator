import os
import traceback
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Initialize Groq client with error handling
try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    groq_client = Groq(api_key=groq_api_key)
except Exception as e:
    print("❌ Failed to initialize Groq client:", str(e))
    print("ℹ️ Make sure your .env file contains GROQ_API_KEY")
    print("ℹ️ Current working directory:", os.getcwd())
    raise RuntimeError("Critical: Could not initialize Groq client") from e

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "generated_blog": ""})

@app.post("/", response_class=HTMLResponse)
async def generate_blog(request: Request, prompt: str = Form(...)):
    system_prompt = (
        "You are a professional blog writer. Write a detailed, well-structured blog post "
        "based on the user's prompt. Use formal language, paragraphs, headings, and avoid "
        "any dialogue or script format. The blog should be informative and engaging."
    )
    user_prompt = prompt

    try:
        print("📡 Calling Groq API with prompt:", user_prompt[:50] + "...")  # Log first 50 chars
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=800,
            temperature=0.7,
            top_p=1,
        )
        generated_blog = response.choices[0].message.content.strip()
        print("✅ Successfully generated blog post")
    except Exception as e:
        error_msg = f"Error generating blog post: {str(e)}"
        print("❌", error_msg)
        traceback.print_exc()
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": error_msg
        }, status_code=500)

    return templates.TemplateResponse("index.html", {"request": request, "generated_blog": generated_blog})
