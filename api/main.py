from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client

SUPABASE_URL = "https://ivncxzpwluxyaujhpnxo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml2bmN4enB3bHV4eWF1amhwbnhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQxNDA1MzUsImV4cCI6MjA2OTcxNjUzNX0.pK3gYHumts_qEmd9QrQi6JbGpzk1P_oM-Odn2l0bECI"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()

class RegisterRequest(BaseModel):
    user_id: str
    username: str = ""
    referred_by: str = ""

@app.post("/register")
async def register_user(data: RegisterRequest):
    print(f"Register request: user_id={data.user_id}, username={data.username}, referred_by={data.referred_by}")
    try:
        # Check if user exists
        user = supabase.table("users").select("*").eq("id", data.user_id).execute()
        if user.data:
            return {"message": "Already registered."}

        print("🚀 Inserting user...")
        result = supabase.table("users").insert({
            "id": data.user_id,
            "username": data.username,
            "points": 0,
            "referral_count": 0,
            "referred_by": data.referred_by or None
        }).execute()

        print("✅ Insert result:", result)

        # Optional: referral system
        if data.referred_by:
            ref_user = supabase.table("users").select("*").eq("id", data.referred_by).execute()
            if ref_user.data:
                supabase.table("users").update({
                    "points": ref_user.data[0]["points"] + 10,
                    "referral_count": ref_user.data[0]["referral_count"] + 1
                }).eq("id", data.referred_by).execute()

                supabase.table("referrals").insert({
                    "user_id": data.user_id,
                    "referred_by": data.referred_by
                }).execute()

        return {"message": "Registered successfully"}

    except Exception as e:
        print("🔥 Error during register_user:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_points/{user_id}")
def get_points(user_id: str):
    user = supabase.table("users").select("points").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")
    return {"points": user.data[0]["points"]}

@app.get("/leaderboard")
def leaderboard():
    top_users = supabase.table("users").select("id, username, points").order("points", desc=True).limit(10).execute()
    return {"leaderboard": top_users.data}

class AddPointRequest(BaseModel):
    user_id: str
    amount: int

@app.post("/add_points")
def add_points(data: AddPointRequest):
    user = supabase.table("users").select("points").eq("id", data.user_id).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_points = user.data[0]["points"] + data.amount
    supabase.table("users").update({"points": new_points}).eq("id", data.user_id).execute()
    return {"message": "Points added", "total": new_points}
