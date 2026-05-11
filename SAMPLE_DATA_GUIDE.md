# How to Insert Sample Adoption Requests

## Quick Start

I've created a Python script that will insert all 10 adoption requests into your Supabase database.

### Option 1: Run from Python IDE
Open `insert_sample_requests.py` in PyCharm and run it directly.

### Option 2: Run from Terminal
```bash
python insert_sample_requests.py
```

### Option 3: Run Manually
You can also insert the requests one at a time using the matching system:

```python
from furever_match.db_ingestion import ingest_adoption_request

# Insert a single request
request_id = ingest_adoption_request({
    'why_adopt': 'מחפשת כלב רגוע לדירה שייתן חברה בבית. חשוב שיהיה מסתדר עם אנשים וקל יחסית לטיפול.',
    'has_kids': False,
    'kids_age': None,
    'has_other_pets': False,
    'which_pets': None,
    'has_yard': False,
    'has_house': False,
    'requested_level_of_train': 'בינוני',
    'requested_gender': 'לא משנה',
    'requested_size': 'קטן-בינוני',
    'requested_age': 'בוגר',
    'requested_level_energy': 'בינונית',
    'dog_living_location': 'דירה',
    'primary_care_giver': 'אני'
})

print(f"Inserted request with ID: {request_id}")
```

## What Gets Inserted

The script inserts 10 adoption requests with different scenarios:

1. **Single person in apartment** - Looking for calm, easy to care for dog
2. **Family with kids** - Looking for friendly, balanced dog for house with yard
3. **First-time adopter** - Looking for small, quiet young dog
4. **Experienced owner with house** - Looking for alert guard dog, good with cats
5. **Active person** - Looking for dog to companion sports activities
6. **Small child family** - Looking for gentle, non-aggressive dog
7. **Homebound person** - Looking for small companion dog with yard
8. **Multi-dog household** - Looking for dog compatible with other dogs
9. **Apartment with roommates** - Looking for small, not-barky dog
10. **Family with cats** - Looking for family dog compatible with cats and kids

## Verify Insertion

After running the script, verify in Supabase:

1. Go to Supabase Dashboard
2. Select your project
3. Go to "adoption_requests" table
4. You should see 10 new rows inserted

## Now Test the Matching!

Once the adoption requests are inserted, test the matching system:

```python
from furever_match.matching_integration import get_matching_dogs

# Get matches for the first adoption request
# (You'll need to replace this with an actual request_id from your database)
matches = get_matching_dogs('request_id_here')

for match in matches[:5]:
    print(f"🐕 {match['dog_name']}: {match['match_score']}%")
```

## Script Details

**File:** `insert_sample_requests.py`

**What it does:**
1. Imports the `ingest_adoption_request` function
2. Defines 10 sample adoption requests in Hebrew
3. Loops through each request and inserts it
4. Reports success/failure for each insertion
5. Prints total number of insertions

**Output example:**
```
✓ Inserted adoption request 1: אני (ID: abc123...)
✓ Inserted adoption request 2: שני ההורים (ID: def456...)
✓ Inserted adoption request 3: אני (ID: ghi789...)
...
✅ Successfully inserted 10 adoption requests!
```

## Data Normalization

The script uses your existing normalization functions:
- Text cleaning
- Boolean normalization (yes/no → true/false)
- Energy level normalization (low/medium/high)
- Gender normalization (male/female)
- Size normalization (small/medium/large)

## If Something Goes Wrong

Check:
1. Your `.env` file has `SUPABASE_URL` and `SUPABASE_KEY`
2. Your Supabase project is active
3. The `adoption_requests` table exists with all required columns
4. Network connection to Supabase is working

## Integration with Your App

After inserting these sample requests, you can:

1. **Get all dogs matching a person:**
   ```python
   from furever_match.matching_integration import get_matching_dogs
   matches = get_matching_dogs(request_id)
   ```

2. **Get top 5 matches:**
   ```python
   top_matches = get_matching_dogs(request_id)[:5]
   ```

3. **See detailed matching info:**
   ```python
   for match in matches:
       print(f"{match['dog_name']}: {match['match_score']}%")
       print(f"Details: {match['match_details']}")
   ```

---

The adoption requests are now ready to use with your matching system! 🐕
