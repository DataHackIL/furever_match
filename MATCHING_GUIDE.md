# Dog Adoption Matching System

## Overview
The matching system compares a dog's profile with an adoption request to calculate a compatibility score between 0-100%.

## How It Works

### Matching Criteria (7 total)
Each criterion is scored from 0-1 (0%, 50%, or 100%), then the average is converted to a percentage.

1. **Gender Match** (100 or 0 or 50%)
   - 100% if dog gender matches requested gender
   - 0% if dog gender doesn't match
   - 50% if no gender preference

2. **Size Match** (100 or 0 or 50%)
   - 100% if dog size matches requested size (small, medium, large)
   - 0% if sizes don't match
   - 50% if no size preference

3. **Energy Level Match** (100 or 0 or 50%)
   - 100% if dog's energy level matches requested energy level
   - 0% if they don't match
   - 50% if no energy preference

4. **Training Level Match** (100 or 0 or 50%)
   - 100% if dog's training level matches requested training level
   - 0% if they don't match
   - 50% if no training preference

5. **Kids Compatibility** (100 or 0 or 50%)
   - If person has kids: Dog must get along with kids (100% if yes, 0% if no)
   - If person doesn't have kids: Always 100% (compatibility less critical)
   - 50% if unknown

6. **Pets Compatibility** (100 or 0 or 50%)
   - If person has other pets: Dog must get along with dogs or cats
   - If person doesn't have pets: Always 100%
   - 50% if unknown

7. **Home Requirements** (100% or 75% or 0%)
   - 100% if person has house AND yard
   - 75% if person has house (but no yard)
   - 0% if person has neither house nor yard

### Score Interpretation

- **80-100%**: Excellent match! ✓
- **60-79%**: Good match ✓
- **40-59%**: Fair match - consider carefully ⊙
- **0-39%**: Poor match - may not be suitable ✗

## Usage

### Basic Example

```python
from furever_match.matching import calculate_match_score, get_match_explanation

# Dog data from database
dog = {
    'gender': 'female',
    'size': 'medium',
    'level_of_training': 'intermediate',
    'get_along_with_kids': True,
    'get_along_with_dogs': True,
    'get_along_with_cats': True,
}

# Adoption request data from database
request = {
    'requested_gender': 'female',
    'requested_size': 'medium',
    'requested_level_energy': 'medium',
    'requested_level_of_train': 'intermediate',
    'has_kids': True,
    'has_other_pets': False,
    'has_yard': True,
    'has_house': True,
}

# Calculate match
result = calculate_match_score(dog, request)

# Print score
print(f"Match Score: {result['score']}%")

# Get detailed explanation
explanation = get_match_explanation(result)
print(explanation)
```

### Output Example

```
Overall Match: 95.24%

Detailed Breakdown:
  • Gender: 100.0%
  • Size: 100.0%
  • Energy Level: 100.0%
  • Training Level: 100.0%
  • Kids Compatibility: 100.0%
  • Pets Compatibility: 100.0%
  • Home Requirements: 100.0%

✓ Excellent match!
```

## Functions

### `calculate_match_score(dog, adoption_request)`
Main function to calculate overall match score.

**Parameters:**
- `dog` (dict): Dog profile with keys like 'gender', 'size', 'level_of_training', etc.
- `adoption_request` (dict): Adoption request with keys like 'requested_gender', 'requested_size', etc.

**Returns:**
```python
{
    'score': 95.24,  # Overall percentage
    'details': {
        'gender': 100.0,
        'size': 100.0,
        'energy_level': 100.0,
        'training_level': 100.0,
        'kids_compatibility': 100.0,
        'pets_compatibility': 100.0,
        'home_requirements': 100.0,
    }
}
```

### `get_match_explanation(match_result)`
Generates human-readable explanation of the match.

**Parameters:**
- `match_result` (dict): Result from `calculate_match_score()`

**Returns:**
- String with formatted explanation and interpretation

## Integration with Database

The matching function can be integrated into your main.py to:

1. Fetch a list of dogs from the database
2. Fetch an adoption request
3. Calculate match scores for each dog
4. Return ranked results to the user

Example integration:
```python
from furever_match.db_ingestion import supabase
from furever_match.matching import calculate_match_score

# Get all available dogs
dogs_response = supabase.table("dogs").select("*").eq("status", "available").execute()
dogs = dogs_response.data

# Get adoption request
request_response = supabase.table("adoption_requests").select("*").eq("id", request_id).execute()
adoption_request = request_response.data[0]

# Calculate matches
matches = []
for dog in dogs:
    match_result = calculate_match_score(dog, adoption_request)
    matches.append({
        'dog_id': dog['id'],
        'dog_name': dog['name'],
        'match_score': match_result['score'],
        'details': match_result['details']
    })

# Sort by score (highest first)
matches.sort(key=lambda x: x['match_score'], reverse=True)

# Return top matches
return matches
```

## Data Requirements

For the matching algorithm to work best, make sure both dog profiles and adoption requests are populated with:

**Dog Profile Fields:**
- `gender` (male/female)
- `size` (small/medium/large)
- `level_of_training` (basic/intermediate/advanced)
- `get_along_with_kids` (true/false/null)
- `get_along_with_dogs` (true/false/null)
- `get_along_with_cats` (true/false/null)

**Adoption Request Fields:**
- `requested_gender` (male/female/null)
- `requested_size` (small/medium/large/null)
- `requested_level_energy` (low/medium/high/null)
- `requested_level_of_train` (text/null)
- `has_kids` (true/false/null)
- `has_other_pets` (true/false/null)
- `has_yard` (true/false/null)
- `has_house` (true/false/null)

## Future Enhancements

Possible improvements to the matching algorithm:

1. **Weighted Criteria**: Some criteria could be weighted more heavily than others
2. **Fuzzy Matching**: Handle variations in text input (e.g., "really energetic" → "high")
3. **User Preferences**: Allow users to set importance levels for different criteria
4. **Machine Learning**: Learn from successful matches to improve recommendations
5. **Exclusion Rules**: Hard rules that automatically disqualify matches
6. **Age Matching**: Add dog age and requested age range as a criterion
