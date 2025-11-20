import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from database import create_document, get_documents, db
from schemas import Place

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Germany Tourist Places API"}

@app.get("/schema")
def get_schema():
    return {
        "place": {
            "fields": {
                "name": "string",
                "city": "string?",
                "state": "string?",
                "description": "string?",
                "category": "string?",
                "tags": "string[]?",
                "latitude": "float?",
                "longitude": "float?",
                "website": "string?"
            }
        }
    }

class PlaceCreate(Place):
    pass

@app.post("/places")
def create_place(place: PlaceCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    inserted_id = create_document("place", place)
    return {"id": inserted_id}

@app.post("/places/seed")
def seed_places():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # If already seeded, do nothing
    existing = db["place"].count_documents({})
    if existing > 0:
        return {"seeded": False, "message": "Places already exist", "count": existing}

    sample: List[dict] = [
        {
            "name": "Brandenburg Gate",
            "city": "Berlin",
            "state": "Berlin",
            "category": "landmark",
            "description": "18th-century neoclassical monument and iconic symbol of Berlin.",
            "tags": ["history", "architecture", "city"],
            "latitude": 52.516275, "longitude": 13.377704,
            "website": "https://www.visitberlin.de/en/brandenburg-gate"
        },
        {
            "name": "Neuschwanstein Castle",
            "city": "Schwangau",
            "state": "Bavaria",
            "category": "castle",
            "description": "Fairy-tale 19th-century Romanesque Revival castle commissioned by King Ludwig II.",
            "tags": ["castle", "mountains", "romantic road"],
            "latitude": 47.5576, "longitude": 10.7498,
            "website": "https://www.neuschwanstein.de/englisch/tourist/index.htm"
        },
        {
            "name": "Cologne Cathedral",
            "city": "Cologne",
            "state": "North Rhine-Westphalia",
            "category": "cathedral",
            "description": "UNESCO-listed Gothic cathedral with twin spires and a rich history.",
            "tags": ["unesco", "gothic", "church"],
            "latitude": 50.9413, "longitude": 6.9583,
            "website": "https://www.koelner-dom.de/"
        },
        {
            "name": "Miniatur Wunderland",
            "city": "Hamburg",
            "state": "Hamburg",
            "category": "museum",
            "description": "World's largest model railway exhibition with intricate miniature worlds.",
            "tags": ["museum", "family", "model"],
            "latitude": 53.5437, "longitude": 9.9884,
            "website": "https://www.miniatur-wunderland.com/"
        },
        {
            "name": "Black Forest",
            "city": "",
            "state": "Baden-Württemberg",
            "category": "nature",
            "description": "Mountainous region known for dense forests, cuckoo clocks, and scenic trails.",
            "tags": ["hiking", "nature", "scenic"],
            "latitude": 48.1430, "longitude": 8.2096,
            "website": "https://www.schwarzwald-tourismus.info/"
        },
        {
            "name": "Heidelberg Castle",
            "city": "Heidelberg",
            "state": "Baden-Württemberg",
            "category": "castle",
            "description": "Picturesque Renaissance castle ruins overlooking the old town.",
            "tags": ["castle", "ruins", "river"],
            "latitude": 49.4106, "longitude": 8.7153,
            "website": "https://www.schloss-heidelberg.de/"
        },
        {
            "name": "Zugspitze",
            "city": "Garmisch-Partenkirchen",
            "state": "Bavaria",
            "category": "mountain",
            "description": "Germany's highest peak with panoramic views and year-round activities.",
            "tags": ["alps", "skiing", "views"],
            "latitude": 47.4210, "longitude": 10.9840,
            "website": "https://zugspitze.de/"
        },
        {
            "name": "Museum Island",
            "city": "Berlin",
            "state": "Berlin",
            "category": "museum",
            "description": "UNESCO ensemble of five world-renowned museums on the Spree.",
            "tags": ["unesco", "art", "history"],
            "latitude": 52.5211, "longitude": 13.3969,
            "website": "https://www.smb.museum/en/museums-institutions/museum-island-berlin/home/"
        },
        {
            "name": "Sanssouci Palace",
            "city": "Potsdam",
            "state": "Brandenburg",
            "category": "palace",
            "description": "Rococo summer palace of Frederick the Great with terraced gardens.",
            "tags": ["palace", "gardens", "rococo"],
            "latitude": 52.4036, "longitude": 13.0397,
            "website": "https://www.spsg.de/"
        },
        {
            "name": "Saxon Switzerland National Park",
            "city": "",
            "state": "Saxony",
            "category": "nature",
            "description": "Dramatic sandstone formations and hiking trails along the Elbe.",
            "tags": ["national park", "hiking", "sandstone"],
            "latitude": 50.9289, "longitude": 14.2366,
            "website": "https://www.saechsische-schweiz.de/en/"
        }
    ]

    ids = []
    for doc in sample:
        ids.append(create_document("place", doc))
    return {"seeded": True, "count": len(ids), "ids": ids}

@app.get("/places")
def list_places(
    q: Optional[str] = Query(default=None, description="Search query across name, city, state, category, tags"),
    category: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500)
):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filter_dict = {}
    if q:
        filter_dict["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"city": {"$regex": q, "$options": "i"}},
            {"state": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}},
            {"tags": {"$elemMatch": {"$regex": q, "$options": "i"}}},
        ]
    if category:
        filter_dict["category"] = {"$regex": f"^{category}$", "$options": "i"}
    if state:
        filter_dict["state"] = {"$regex": f"^{state}$", "$options": "i"}
    if city:
        filter_dict["city"] = {"$regex": f"^{city}$", "$options": "i"}

    docs = get_documents("place", filter_dict, limit)

    cleaned = []
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
        cleaned.append(d)
    return {"items": cleaned, "count": len(cleaned)}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
