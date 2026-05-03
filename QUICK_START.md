# Quick Start Guide - Dog Adoption Matching

## TL;DR - Get Started in 30 seconds

```python
from furever_match.matching import calculate_match_score
from furever_match.matching_integration import get_matching_dogs

# Method 1: Match one dog with one person
result = calculate_match_score(dog_dict, adoption_request_dict)
print(f"Match Score: {result['score']}%")  # Output: 85.5%

# Method 2: Find all dogs for a person (ranked by score)
matches = get_matching_dogs(adoption_request_id)
for match in matches:
    print(f"{match['dog_name']}: {match['match_score']}%")

# Method 3: Get top 5 matches
top_5 = get_matching_dogs(adoption_request_id)[:5]
```

## What Data Do I Need?

### Dog Data (from your database)
```python
dog = {
    'gender': 'male',           # 'male' or 'female'
    'size': 'medium',           # 'small', 'medium', or 'large'
    'level_of_training': 'intermediate',  # 'basic', 'intermediate', or 'advanced'
    'get_along_with_kids': True,    # True, False, or None
    'get_along_with_dogs': True,    # True, False, or None
    'get_along_with_cats': False,   # True, False, or None
}
```

### Adoption Request Data (from UI form)
```python
request = {
    'requested_gender': 'male',         # 'male', 'female', or None
    'requested_size': 'medium',         # 'small', 'medium', 'large', or None
    'requested_level_energy': 'high',   # 'low', 'medium', 'high', or None
    'requested_level_of_train': 'intermediate',  # text or None
    'requested_age': '3-5 years',       # text or None (for future use)
    'has_kids': True,                   # True, False, or None
    'has_other_pets': False,            # True, False, or None
    'has_yard': True,                   # True, False, or None
    'has_house': True,                  # True, False, or None
}
```

## Score Ranges

| Score | Meaning |
|-------|---------|
| 80-100 | Excellent! ✓ |
| 60-79 | Good! ✓ |
| 40-59 | Fair - think carefully ⊙ |
| 0-39 | Poor match ✗ |

## Examples

### Example 1: Perfect Match
```python
dog = {
    'gender': 'female',
    'size': 'small',
    'level_of_training': 'basic',
    'get_along_with_kids': True,
    'get_along_with_dogs': False,
    'get_along_with_cats': True,
}

request = {
    'requested_gender': 'female',
    'requested_size': 'small',
    'requested_level_energy': 'low',
    'requested_level_of_train': 'basic',
    'has_kids': True,
    'has_other_pets': False,
    'has_yard': False,
    'has_house': True,
}

result = calculate_match_score(dog, request)
# Result: 92.86% (Excellent match!)
```

### Example 2: Poor Match
```python
dog = {
    'gender': 'male',
    'size': 'large',
    'level_of_training': 'advanced',
    'get_along_with_kids': False,
    'get_along_with_dogs': False,
    'get_along_with_cats': False,
}

request = {
    'requested_gender': 'female',
    'requested_size': 'small',
    'requested_level_energy': 'low',
    'requested_level_of_train': 'basic',
    'has_kids': True,
    'has_other_pets': True,
    'has_yard': False,
    'has_house': False,
}

result = calculate_match_score(dog, request)
# Result: 0% (Poor match)
```

## How the 7 Criteria Are Scored

1. **Gender** (100% or 0% or 50%)
   - 100% if it matches
   - 0% if it doesn't match
   - 50% if no preference

2. **Size** (100% or 0% or 50%)
   - Same as gender matching

3. **Energy Level** (100% or 0% or 50%)
   - Same as gender matching

4. **Training Level** (100% or 0% or 50%)
   - Same as gender matching

5. **Kids Compatibility** (100% or 0% or 50%)
   - If person HAS kids: dog must be kids-friendly (100%) or not (0%)
   - If person has NO kids: always 100% (kids compatibility doesn't matter)

6. **Pets Compatibility** (100% or 0% or 50%)
   - If person HAS other pets: dog must get along with them (100%) or not (0%)
   - If person has NO other pets: always 100% (pet compatibility doesn't matter)

7. **Home Requirements** (100% or 75% or 0%)
   - House + Yard = 100% (ideal)
   - House only = 75% (acceptable)
   - No house = 0% (not suitable)

## Integration with Your App

### Step 1: User Submits Adoption Form
```python
from furever_match.db_ingestion import ingest_adoption_request

adoption_form_data = {
    'why_adopt': user_input['why_adopt'],
    'has_kids': user_input['has_kids'],
    'kids_age': user_input['kids_age'],
    # ... all other fields
}

request_id = ingest_adoption_request(adoption_form_data)
```

### Step 2: Show Matching Dogs
```python
from furever_match.matching_integration import get_matching_dogs

matches = get_matching_dogs(request_id)

for match in matches:
    print(f"🐕 {match['dog_name']}")
    print(f"   Match Score: {match['match_score']}%")
    print(f"   Details: {match['match_details']}")
```

## Files You Have

- `furever_match/matching.py` - Core matching algorithm
- `furever_match/matching_integration.py` - Database integration
- `furever_match/db_ingestion.py` - Updated with adoption request ingestion
- `tests/test_matching.py` - Test suite
- `examples_matching.py` - Usage examples
- `MATCHING_GUIDE.md` - Full documentation

## Need Help?

See `MATCHING_GUIDE.md` for detailed documentation.
