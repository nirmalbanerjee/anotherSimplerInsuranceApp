# ✅ Fixed: Policy Creation & Frontend Data Display

## The Problem
The `generate-metrics-data.sh` script was running without errors, but the data wasn't showing up in the frontend.

## Root Cause
The backend's `create_policy()` function had a bug:
- It was trying to access `user_obj.id` 
- But `UserORM` uses `username` as the primary key, not `id`
- It was also trying to set `user_id=user_obj.id` on PolicyORM
- But `PolicyORM` doesn't have a `user_id` field

**Error:** `AttributeError: 'UserORM' object has no attribute 'id'`

## The Fix

### Before (Broken Code):
```python
@app.post("/policies", response_model=InsurancePolicy)
def create_policy(policy: InsurancePolicyCreate, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get the user's database ID
    user_obj = db.query(UserORM).filter(UserORM.username == user["username"]).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    
    row = PolicyORM(
        name=policy.name, 
        details=policy.details, 
        owner=user["username"],
        user_id=user_obj.id  # ❌ user_obj has no 'id' attribute!
    )
    # ...
```

### After (Fixed Code):
```python
@app.post("/policies", response_model=InsurancePolicy)
def create_policy(policy: InsurancePolicyCreate, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    row = PolicyORM(
        name=policy.name, 
        details=policy.details, 
        owner=user["username"]  # ✅ Just use username directly
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return InsurancePolicy(id=row.id, name=row.name, details=row.details or "", owner=row.owner)
```

## What Changed
1. ✅ Removed unnecessary user lookup
2. ✅ Removed non-existent `user_id` field assignment
3. ✅ Simplified to just use `owner=user["username"]`
4. ✅ Rebuilt backend container with fixed code

## Verification

### Test Policy Creation:
```bash
# Login as user1
TOKEN=$(curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=user1&password=pass123' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create a policy
curl -X POST http://localhost:8000/policies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"My Policy","details":"Test policy"}'

# Should return:
# {"id":1,"name":"My Policy","details":"Test policy","owner":"user1"}
```

### Test Fetching Policies:
```bash
# Get all policies for user1
curl -X GET http://localhost:8000/policies \
  -H "Authorization: Bearer $TOKEN"

# Should return array of policies
```

## Testing the Frontend

1. **Open the app**: http://localhost:3023
2. **Register a new user** or **login** with existing credentials:
   - Username: `user1`
   - Password: `pass123`
3. **Navigate to Policies section**
4. **You should see**:
   - Test Policy
   - Policy 1
   - Policy 2
   - Policy 3
5. **Try creating a new policy** - it should work now!

## Current Data in System

After running `./generate-metrics-data.sh`, you have:
- ✅ **6 users**: user1-5 (password: pass123) + admin1 (password: admin123)
- ✅ **4 policies** for user1:
  - Test Policy (manual test)
  - Policy 1 (from script)
  - Policy 2 (from script)
  - Policy 3 (from script)
- ✅ **3 failed login attempts** (for metrics)
- ✅ **Metrics data** for Prometheus/Grafana

## Generate More Data

Run the script multiple times to create more test data:
```bash
./generate-metrics-data.sh
```

Each run will:
- Create 5 more users (duplicates will fail silently, which is fine)
- Add 3 more policies for user1
- Generate 3 more failed login events
- Create HTTP request metrics

## Database Schema

For reference, here's the actual schema being used:

### UserORM:
```python
class UserORM(Base):
    __tablename__ = "users"
    username = Column(String(100), primary_key=True, index=True)  # ← PK is username, not id
    password = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False)
```

### PolicyORM:
```python
class PolicyORM(Base):
    __tablename__ = "policies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)
    owner = Column(String(100), nullable=False)  # ← References username, not user.id
```

## Troubleshooting

### Policies still not showing in frontend?
1. **Clear browser cache**: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. **Check you're logged in**: The frontend needs a valid JWT token
3. **Verify API works**: Use curl commands above to test
4. **Check browser console**: Look for any JavaScript errors

### Can't create policies?
1. **Check you're authenticated**: Must have valid login token
2. **Verify backend is running**: `docker compose ps`
3. **Check logs**: `docker compose logs backend --tail 20`

### Users from script not appearing?
- Users ARE created, they just silently fail if they already exist
- Try logging in with `user2`, `user3`, etc. (password: pass123)

## Files Modified
- ✅ `backend/main.py` - Fixed create_policy() function

## No Changes Needed
- ✅ `db/models.py` - Schema is correct as-is
- ✅ `frontend/` - No frontend changes needed
- ✅ `generate-metrics-data.sh` - Script is correct

---

**Status**: ✅ **FIXED** - Policies can now be created and will appear in the frontend!
