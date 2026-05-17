# Enhanced Matching System v2 - Documentation

## Overview

The Enhanced Matching System v2 implements a sophisticated three-tier matching approach:

1. **Hard Filters**: Clear, non-negotiable criteria that completely disqualify a dog
2. **Soft Scoring**: Intelligent scoring of compatible characteristics
3. **LLM Character Analysis**: AI-powered personality and lifestyle matching with reasoning

## Architecture

### Part 1: Hard Filters

Hard filters are disqualifying criteria that completely eliminate a dog from consideration. A dog must pass ALL hard filters to proceed to soft scoring.

#### Hard Filter Criteria:

##### 1. **Other Pets Compatibility** (Critical)
```
IF person has other pets THEN:
  - If has dogs: Dog MUST get along with dogs (or be Unknown)
  - If has cats: Dog MUST get along with cats (or be Unknown)
  
If dog fails this check → Rejected immediately
```

##### 2. **Kids Compatibility** (Age-Aware)
```
IF person has young children (under 15) THEN:
  - Dog MUST get along with kids (or be Unknown)
  
IF person has only older kids (15+) THEN:
  - Kids compatibility is NOT critical
  
If dog fails and person has young kids → Rejected immediately
```

**Note**: Kids age 15+ are considered adults. A person with only 15+ year old kids can adopt dogs that don't get along with young children.

##### 3. **Training Level Requirements**
```
IF dog requires advanced training THEN:
  - Person MUST be willing to do advanced training
  
IF person can only handle basic training and dog is advanced THEN:
  - Dog rejected (safety concern)
```

##### 4. **Home Requirements (Size-Based)**
```
IF dog is large THEN:
  - Person MUST have a house (apartment insufficient)
  - (Large dogs are too big for apartments)
  
IF apartment living and dog is large → Rejected
```

**Examples**:
- ❌ Family with young kids + Dog doesn't get along with kids = Rejected
- ❌ Person has cat + Dog doesn't get along with cats = Rejected  
- ❌ First-time owner + Advanced training dog = Rejected
- ❌ Apartment living + Large dog = Rejected
- ✅ Family with teens (16+) + Dog doesn't like kids = Can proceed (not critical)

### Part 2: Soft Scoring

If a dog passes all hard filters, it receives soft scores across 8 criteria. Each criterion scores 0-100%.

#### Soft Scoring Criteria:

| Criterion | Scoring | Weight | Notes |
|-----------|---------|--------|-------|
| **Gender** | 100% match / 50% any / 0% mismatch | High | Clear preference |
| **Size** | 100% exact / 70% nearby / 30% far / 50% unknown | High | Physical compatibility |
| **Energy Level** | 100% match / 70% close / 40% different / 50% unknown | High | Lifestyle fit |
| **Training Level** | 100% match / 70% close / 40% different / 50% unknown | High | Owner capability |
| **Age Compatibility** | 75% general | Medium | Most ages compatible |
| **Kids Compatibility** | 100% friendly / 0% not / 50% unknown | Medium | Non-critical if no young kids |
| **Pets Compatibility** | 100% compatible / 0% not / 50% unknown | Medium | Non-critical if no pets |
| **Home Requirements** | 100% ideal / 85% good / 75% acceptable / varies | Medium | Size-dependent |

**Soft Score Calculation**:
```
Soft Score = (Sum of all criteria / Number of criteria) × 100
```

**Example**:
- Gender: 100% ✅ (male matches male)
- Size: 70% (medium wanted, medium dog - perfect)
- Energy: 80% (high wanted, high dog)
- Training: 90% (basic wanted, basic dog)
- Age: 75% (flexible)
- Kids: 100% ✅ (dog friendly with kids)
- Pets: 100% ✅ (no other pets)
- Home: 100% ✅ (large dog + house + yard)

**Average Soft Score = (100+70+80+90+75+100+100+100) / 8 = 89.4%**

### Part 3: LLM Character Analysis

Once hard filters pass and soft scores are calculated, the system uses an LLM (Large Language Model) to analyze personality and lifestyle compatibility.

#### LLM Analysis Process:

1. **Collects Information**:
   - Dog: Breed, description, personality traits, fears
   - Person: Why they want to adopt, living situation, lifestyle
   - Contextual data: Family situation, care capacity

2. **Generates Analysis**:
   - Personality fit (0-100%)
   - Key strengths of this match
   - Potential concerns
   - Detailed reasoning
   - Recommendation

3. **Example LLM Output**:
```json
{
  "compatibility_score": 85,
  "key_strengths": [
    "Both are active and enjoy outdoor activities",
    "Dog's friendly nature matches family's open lifestyle",
    "Similar energy levels suggest good daily routine fit"
  ],
  "potential_concerns": [
    "Dog is sensitive to loud noises; family has young kids who can be loud"
  ],
  "reasoning": "This is a very good match. The energetic Golden Retriever aligns well with the family's active lifestyle and their desire for a companion dog. The only minor concern is the dog's noise sensitivity.",
  "recommendation": "Highly recommended - this is a strong match"
}
```

### Part 4: Final Combined Score

The final score combines both soft scoring and LLM analysis:

```
Final Score = (Soft Score × 60%) + (LLM Score × 40%)
```

**Rationale**:
- **60% Soft Scoring**: Hard, objective criteria (size, training, etc.)
- **40% LLM Analysis**: Subjective, personality-based fit

**Final Result Includes**:
- ✅ Final score (0-100%)
- ✅ Passes filters (boolean)
- ✅ Soft score breakdown (for each criterion)
- ✅ Character match analysis (from LLM)
- ✅ Complete reasoning explanation

## Usage

### Basic Usage (Without LLM - Fast)

```python
from furever_match.matching_v2 import calculate_match_score_v2

result = calculate_match_score_v2(dog, adoption_request, use_llm=False)

print(f"Passes filters: {result['passes_filters']}")
print(f"Soft score: {result['soft_score']}%")
print(f"Final score: {result['final_score']}%")
```

### Advanced Usage (With LLM - Detailed Analysis)

```python
from furever_match.matching_v2 import calculate_match_score_v2

result = calculate_match_score_v2(
    dog,
    adoption_request,
    use_llm=True,
    llm_provider="gemini"  # or "ollama"
)

print(f"Final score: {result['final_score']}%")
print(f"Reasoning: {result['final_reasoning']}")
print(f"LLM analysis: {result['character_match']['reasoning']}")
```

### Integration Example (Database Integration)

```python
from furever_match.matching_integration_v2 import get_matching_dogs_v2

# Get all matching dogs for a person (fast, without LLM)
matches = get_matching_dogs_v2(
    request_id="adoption_request_uuid",
    use_llm=False  # Fast results
)

for match in matches:
    if match['passes_filters']:
        print(f"{match['dog_name']}: {match['match_score']}%")
        print(f"  Soft score: {match['soft_score']}%")
        print(f"  Character match: {match['character_match']['reasoning']}")
```

## Result Structure

### Full Match Result Object:

```python
{
    # Hard filter results
    'passes_filters': bool,
    'filter_rejection_reason': str or None,
    
    # Soft scoring
    'soft_score': float,  # 0-100
    'soft_scores_breakdown': {
        'gender': float,
        'size': float,
        'energy_level': float,
        'training_level': float,
        'age_compatibility': float,
        'kids_compatibility': float,
        'pets_compatibility': float,
        'home_requirements': float,
    },
    
    # LLM character analysis
    'character_match': {
        'compatibility_score': float,  # 0-100
        'key_strengths': [str, ...],
        'potential_concerns': [str, ...],
        'reasoning': str,
        'recommendation': str,
    },
    
    # Final results
    'final_score': float,  # 0-100
    'final_reasoning': str,
}
```

## Interpretation Guide

### Score Ranges:

| Score | Meaning | Recommendation |
|-------|---------|-----------------|
| **90-100%** | Excellent match | Highly recommended |
| **75-89%** | Very good match | Recommended |
| **60-74%** | Good match | Consider |
| **40-59%** | Moderate match | Requires discussion |
| **0-39%** | Poor match | Not recommended |
| **0% (fails filters)** | Disqualified | Incompatible |

### When Score is 0%:

If final score is 0%, the dog has **failed hard filters**. Check `filter_rejection_reason`:
- "Dog doesn't get along with other dogs" → Won't work with other pets
- "Dog doesn't get along with young children" → Won't work with families
- "Large dog needs a house" → Unsuitable for apartment
- "Dog requires advanced training skills" → Too demanding for owner

## LLM Providers

### Gemini (Recommended)
```python
result = calculate_match_score_v2(
    dog,
    adoption_request,
    use_llm=True,
    llm_provider="gemini"
)
```
- Set `GEMINI_API_KEY` environment variable
- Fast, accurate, well-reasoned results

### Ollama (Local)
```python
result = calculate_match_score_v2(
    dog,
    adoption_request,
    use_llm=True,
    llm_provider="ollama"
)
```
- Runs locally (no API key needed)
- Slower but privacy-preserving
- Requires Ollama running on http://localhost:11434

## Performance Considerations

### Without LLM (Fast):
- ~10-50ms per dog
- Suitable for real-time filtering
- Use for initial screening

### With LLM (Thorough):
- ~1-5 seconds per dog (varies by provider)
- Better for detailed analysis
- Use when showing top matches to user

### Recommendation:
1. Use `use_llm=False` for initial filtering (get top 10)
2. Use `use_llm=True` for detailed analysis of top matches

## Testing

Run comprehensive test suite:

```bash
py -3.9 -m pytest tests/test_matching_v2.py -v
```

Or run example tests directly:

```bash
py -3.9 tests/test_matching_v2.py
```

### Test Cases Include:
1. ✅ Good match - family with kids wants friendly dog
2. ❌ Hard filter failure - dog doesn't get along with kids
3. ❌ Hard filter failure - cat incompatibility
4. ✅ Older kids - not critical filter
5. ❌ Hard filter failure - large dog in apartment
6. ❌ Hard filter failure - training level mismatch

## Migration from v1

### Old Code (v1):
```python
from furever_match.matching import calculate_match_score
result = calculate_match_score(dog, adoption_request)
score = result['score']
```

### New Code (v2):
```python
from furever_match.matching_v2 import calculate_match_score_v2
result = calculate_match_score_v2(dog, adoption_request)
score = result['final_score']
```

### Backward Compatibility:
```python
# New matching_integration automatically uses v2
from furever_match.matching_integration_v2 import get_matching_dogs

matches = get_matching_dogs(request_id)  # Now uses v2!
```

## Future Enhancements

1. **Weighted Criteria**: Let users set importance of criteria
2. **Hard Rules**: Custom disqualifying rules per adoption request
3. **Age Range Matching**: Smart age preference handling
4. **Neighborhood Matching**: Geographic compatibility
5. **Schedule Matching**: Time availability for exercise/training
6. **Cost Consideration**: Budget-aware matching

## Questions & Support

- For quick scoring: Use `calculate_match_score_v2(..., use_llm=False)`
- For detailed analysis: Use `calculate_match_score_v2(..., use_llm=True)`
- Check test cases in `tests/test_matching_v2.py` for examples
