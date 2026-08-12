import os
import tempfile

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from graph.pipeline import trip_graph
from api.schemas import TripRequest, UserSignup, UserLogin, TokenResponse
from api.database import (
    init_db, create_user, get_user_by_email,
    save_trip, get_user_trips, get_trip_by_id,
)
from api.auth import hash_password, verify_password, create_access_token, get_current_user
from tools.pdf_export import build_trip_pdf

load_dotenv()

app = FastAPI(title="Trip Planner Agent API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "model": "llama-3.3-70b-versatile"}


# ---------- Auth ----------

@app.post("/auth/signup", response_model=TokenResponse)
async def signup(body: UserSignup):
    if get_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = create_user(body.email, hash_password(body.password))
    return {"access_token": create_access_token(user_id)}


@app.post("/auth/login", response_model=TokenResponse)
async def login(body: UserLogin):
    user = get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(user["id"])}


@app.get("/auth/me")
async def me(current_user: dict = Depends(get_current_user)):
    return {"id": current_user["id"], "email": current_user["email"]}


# ---------- Trip planning ----------

def _run_pipeline(req: TripRequest) -> dict:
    try:
        result = trip_graph.invoke({"preferences": req.model_dump()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "destination": req.destination,
        "destination_info": result.get("destination_info", {}),
        "weather_summary": result.get("weather_forecast", []),
        "attractions": result.get("attractions", []),
        "itinerary": result.get("final_itinerary", []),
        "budget_breakdown": result.get("budget_breakdown", {}),
        "budget_status": result.get("budget_status", ""),
        "suggestions": result.get("suggestions", []),
        "hotel_suggestions": result.get("hotel_suggestions", []),
        "flight_suggestions": result.get("flight_suggestions", []),
    }


@app.post("/plan")
async def plan_trip(req: TripRequest):
    """Plan a trip without saving it (no login required)."""
    return _run_pipeline(req)


@app.post("/plan/save")
async def plan_and_save_trip(req: TripRequest, current_user: dict = Depends(get_current_user)):
    """Plan a trip and save it to the logged-in user's history."""
    plan = _run_pipeline(req)
    trip_id = save_trip(current_user["id"], req.destination, plan)
    return {**plan, "trip_id": trip_id}


@app.get("/trips")
async def list_trips(current_user: dict = Depends(get_current_user)):
    return get_user_trips(current_user["id"])


@app.get("/trips/{trip_id}")
async def get_trip(trip_id: int, current_user: dict = Depends(get_current_user)):
    trip = get_trip_by_id(trip_id, current_user["id"])
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


# ---------- PDF export ----------

@app.post("/plan/pdf")
async def export_pdf(req: TripRequest):
    """Plan a trip and return it as a downloadable PDF (no login required)."""
    plan = _run_pipeline(req)

    tmp_path = os.path.join(tempfile.gettempdir(), f"trip_{req.destination}.pdf")
    build_trip_pdf(
        destination=plan["destination"],
        itinerary=plan["itinerary"],
        budget_breakdown=plan["budget_breakdown"],
        suggestions=plan["suggestions"],
        hotels=plan["hotel_suggestions"],
        flights=plan["flight_suggestions"],
        out_path=tmp_path,
    )
    return FileResponse(tmp_path, media_type="application/pdf", filename=f"{req.destination}_trip_plan.pdf")


# Run locally:   uvicorn api.main:app --reload --port 8000
# Docs:          http://localhost:8000/docs
