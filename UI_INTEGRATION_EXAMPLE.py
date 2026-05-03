"""
Example: How to integrate the matching system into your UI
This shows the complete flow from form submission to displaying matches
"""

# ============================================================
# PART 1: User submits adoption request form
# ============================================================

def handle_adoption_form_submission(form_data):
    """
    This function would be called when the user submits the adoption form.

    Args:
        form_data: Dictionary from your form with all adoption questions
                   The keys should match what the UI form sends

    Returns:
        request_id: UUID of the created adoption request (or None if failed)
    """
    from furever_match.db_ingestion import ingest_adoption_request

    # The form data from your UI should look like this:
    adoption_request = {
        'why_adopt': form_data.get('why_adopt'),
        'has_kids': form_data.get('has_kids'),  # 'yes'/'no' string → normalized to True/False
        'kids_age': form_data.get('kids_age'),
        'has_other_pets': form_data.get('has_other_pets'),  # 'yes'/'no' → True/False
        'which_pets': form_data.get('which_pets'),
        'has_yard': form_data.get('has_yard'),  # 'yes'/'no' → True/False
        'has_house': form_data.get('has_house'),  # 'yes'/'no' → True/False
        'requested_level_of_train': form_data.get('requested_level_of_train'),
        'requested_gender': form_data.get('requested_gender'),  # 'male'/'female'
        'requested_age': form_data.get('requested_age'),  # e.g., '3-5 years'
        'requested_size': form_data.get('requested_size'),  # 'small'/'medium'/'large'
        'requested_level_energy': form_data.get('requested_level_energy'),  # 'low'/'medium'/'high'
        'dog_living_location': form_data.get('dog_living_location'),
        'primary_care_giver': form_data.get('primary_care_giver'),
    }

    # Save to database and get request ID
    request_id = ingest_adoption_request(adoption_request)

    return request_id


# ============================================================
# PART 2: Display matching dogs to the user
# ============================================================

def get_matching_dogs_for_user(adoption_request_id):
    """
    Display all available dogs ranked by match score.
    This would be called to show the user their recommendations.

    Args:
        adoption_request_id: UUID from Part 1

    Returns:
        List of dogs with match scores, ready to display
    """
    from furever_match.matching_integration import get_matching_dogs

    matches = get_matching_dogs(adoption_request_id)

    # Format for your UI
    results = []
    for match in matches:
        results.append({
            'dog_id': match['dog_id'],
            'name': match['dog_name'],
            'breed': match['breed'],
            'size': match['size'],
            'gender': match['gender'],
            'match_score': match['match_score'],
            'match_score_display': f"{match['match_score']:.1f}%",
            'match_quality': get_quality_label(match['match_score']),
            'match_details': match['match_details'],  # For detailed breakdown
        })

    return results


def get_quality_label(score):
    """Helper to get human-friendly quality label"""
    if score >= 80:
        return "Excellent Match! 🌟"
    elif score >= 60:
        return "Good Match! ✓"
    elif score >= 40:
        return "Fair Match ⊙"
    else:
        return "Poor Match"


# ============================================================
# PART 3: Show detailed match information
# ============================================================

def get_dog_match_details(adoption_request_id, dog_id):
    """
    Show detailed matching information for a specific dog.
    Called when user clicks on a dog to see more details.

    Args:
        adoption_request_id: UUID from Part 1
        dog_id: UUID of the dog to show details for

    Returns:
        Dictionary with detailed match information
    """
    from furever_match.db_ingestion import supabase
    from furever_match.matching import calculate_match_score, get_match_explanation

    # Fetch the dog and adoption request
    dog_response = supabase.table("dogs").select("*").eq("id", dog_id).execute()
    request_response = supabase.table("adoption_requests").select("*").eq("id", adoption_request_id).execute()

    if not dog_response.data or not request_response.data:
        return None

    dog = dog_response.data[0]
    request = request_response.data[0]

    # Calculate match
    match_result = calculate_match_score(dog, request)

    return {
        'dog_id': dog['id'],
        'dog_name': dog['name'],
        'dog_breed': dog['breed'],
        'dog_description': dog.get('description'),
        'match_score': match_result['score'],
        'match_details': match_result['details'],
        'match_explanation': get_match_explanation(match_result),
        'detailed_breakdown': format_detailed_breakdown(match_result['details']),
    }


def format_detailed_breakdown(details):
    """Format the match details for display"""
    breakdown = []

    criteria_names = {
        'gender': '👥 Gender',
        'size': '📏 Size',
        'energy_level': '⚡ Energy Level',
        'training_level': '🎓 Training Level',
        'kids_compatibility': '👶 Kids Compatible',
        'pets_compatibility': '🐾 Pets Compatible',
        'home_requirements': '🏠 Home Requirements',
    }

    for criterion, value in details.items():
        breakdown.append({
            'criterion': criteria_names.get(criterion, criterion),
            'score': f"{value:.1f}%",
            'bar': create_progress_bar(value),
        })

    return breakdown


def create_progress_bar(percentage, width=20):
    """Create a simple text progress bar"""
    filled = int((percentage / 100) * width)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {percentage:.1f}%"


# ============================================================
# PART 4: Filter results
# ============================================================

def get_excellent_matches(adoption_request_id):
    """Get only excellent matches (80%+)"""
    from furever_match.matching_integration import get_matching_dogs

    all_matches = get_matching_dogs(adoption_request_id)
    return [m for m in all_matches if m['match_score'] >= 80]


def get_good_matches(adoption_request_id):
    """Get only good matches (60-79%)"""
    from furever_match.matching_integration import get_matching_dogs

    all_matches = get_matching_dogs(adoption_request_id)
    return [m for m in all_matches if 60 <= m['match_score'] < 80]


# ============================================================
# EXAMPLE FLOW
# ============================================================

if __name__ == '__main__':
    # Step 1: Simulate user submitting form
    form_data = {
        'why_adopt': 'I love dogs and want a companion',
        'has_kids': 'yes',
        'kids_age': '5 and 8',
        'has_other_pets': 'no',
        'which_pets': '',
        'has_yard': 'yes',
        'has_house': 'yes',
        'requested_level_of_train': 'basic',
        'requested_gender': 'female',
        'requested_age': None,
        'requested_size': 'medium',
        'requested_level_energy': 'high',
        'dog_living_location': 'indoor/outdoor',
        'primary_care_giver': 'John Doe',
    }

    print("=" * 60)
    print("STEP 1: User submits adoption form")
    print("=" * 60)
    request_id = handle_adoption_form_submission(form_data)
    print(f"✓ Adoption request created: {request_id}\n")

    # Step 2: Get matching dogs
    print("=" * 60)
    print("STEP 2: Display matching dogs")
    print("=" * 60)
    matches = get_matching_dogs_for_user(request_id)
    for match in matches[:3]:  # Show top 3
        print(f"🐕 {match['name']} ({match['breed']})")
        print(f"   Score: {match['match_score_display']} - {match['match_quality']}")
        print()

    print("\n" + "=" * 60)
    print("STEP 3: User clicks on a dog to see details")
    print("=" * 60)
    if matches:
        dog_details = get_dog_match_details(request_id, matches[0]['dog_id'])
        print(f"🐕 {dog_details['dog_name']}")
        print(f"   Breed: {dog_details['dog_breed']}")
        print(f"   Match Score: {dog_details['match_score']}%\n")
        print("Detailed Breakdown:")
        for detail in dog_details['detailed_breakdown']:
            print(f"  {detail['criterion']}: {detail['bar']}")
