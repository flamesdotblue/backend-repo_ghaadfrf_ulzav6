import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal
import random

app = FastAPI(title="DreamInk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)
    mood: Literal["Romantic", "Melancholic", "Hopeful", "Dreamlike", "Haunting"]
    format: Literal["Poem", "Short Story", "Haiku", "Microfiction"]


class GenerateResponse(BaseModel):
    content: str
    mood: str
    format: str


def craft_lines(prompt: str, mood: str, format: str) -> list[str]:
    # Word palettes to color the output by mood
    palettes = {
        "Romantic": ["rose", "heartbeat", "velvet", "starlit", "whisper", "tender"],
        "Melancholic": ["rain", "echo", "ashen", "window", "ache", "distant"],
        "Hopeful": ["dawn", "warmth", "seed", "lift", "promise", "bright"],
        "Dreamlike": ["silk", "float", "mist", "lantern", "lucid", "drift"],
        "Haunting": ["hollow", "candle", "shadow", "marrow", "threshold", "murmur"],
    }

    tone_lines = {
        "Poem": 8,
        "Short Story": 14,
        "Haiku": 3,
        "Microfiction": 5,
    }

    structures = {
        "Poem": [
            "{prompt} {w1} in the {w2} of night",
            "I fold a {w3} letter to the sky",
            "between breaths, {w4} syllables glow",
            "your name is a small {w5} constellating",
            "the world tilts toward a quiet {w6}",
            "and somewhere, the future loosens its hands",
            "we step into a doorway made of hush",
            "and call it home for one more luminous minute",
        ],
        "Short Story": [
            "The evening learned our names before we spoke.",
            "{prompt} was only a rumor the moon kept repeating.",
            "In the kitchen, a {w1} clock dripped time into a chipped mug.",
            "We traded secrets like small {w2} coins, warm from the palm.",
            "Outside, the alley held its breath, all {w3} and listening.",
            "You said tomorrow, and the word wavered, a {w4} lantern.",
            "I wanted to believe in the simple machinery of hope.",
            "We walked past windows where strangers practiced happiness.",
            "The city unfurled, a long {w5} ribbon of headlights.",
            "At the river, someone had left a message in the reeds.",
            "It said: keep going. It said: the door is almost open.",
            "We did not turn back. The night followed, gentle and {w6}.",
            "Somewhere a small animal remembered our footsteps.",
            "And the future, patient, set another place at the table.",
        ],
        "Haiku": [
            "{prompt} in mist",
            "a {w1} window breathing",
            "dawn learns our {w2}",
        ],
        "Microfiction": [
            "We met where {prompt} became a password.",
            "You laughed, and the {w1} street forgot its loneliness.",
            "We promised only this: to listen for {w2} doors opening.",
            "Night wrote our names on its {w3} palm and did not close its hand.",
            "In the morning, one small {w4} miracle was still there, waiting.",
        ],
    }

    words = palettes.get(mood, palettes["Dreamlike"])[:]
    random.shuffle(words)

    # Build lines based on format structure
    tmpl = structures[format]
    lines = []
    for i, t in enumerate(tmpl):
        w1 = words[i % len(words)]
        w2 = words[(i + 1) % len(words)]
        w3 = words[(i + 2) % len(words)]
        w4 = words[(i + 3) % len(words)]
        w5 = words[(i + 4) % len(words)]
        w6 = words[(i + 5) % len(words)]
        lines.append(t.format(prompt=prompt.strip(), w1=w1, w2=w2, w3=w3, w4=w4, w5=w5, w6=w6))

    # Trim if necessary
    target = tone_lines[format]
    return lines[:target]


@app.post("/generate", response_model=GenerateResponse)
def generate_text(req: GenerateRequest):
    lines = craft_lines(req.prompt, req.mood, req.format)
    content = "\n".join(lines)
    return GenerateResponse(content=content, mood=req.mood, format=req.format)


@app.get("/")
def read_root():
    return {"message": "DreamInk API is alive"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
