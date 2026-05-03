"""
Matching algorithm that compares dog profiles with adoption requests
and returns a match score as a percentage.
"""

# -----------------------------
# MATCHING LOGIC
# -----------------------------

def match_gender(dog_gender, requested_gender):
    """
    Match dog gender with requested gender.
    Returns 1.0 if match, 0.0 if no match, 0.5 if no preference.
    """
    if not requested_gender:
        return 0.5  # No preference
    if not dog_gender:
        return 0.0  # Unknown dog gender
    return 1.0 if dog_gender == requested_gender else 0.0


def match_size(dog_size, requested_size):
    """
    Match dog size with requested size.
    Returns 1.0 if match, 0.0 if no match, 0.5 if no preference.
    """
    if not requested_size:
        return 0.5  # No preference
    if not dog_size:
        return 0.0  # Unknown dog size
    return 1.0 if dog_size == requested_size else 0.0


def match_energy_level(dog_energy, requested_energy):
    """
    Match dog energy level with requested energy level.
    Returns 1.0 if match, 0.0 if no match, 0.5 if no preference.

    Note: dog_energy is derived from level_of_training.
    High training = high energy potential, low training = low energy.
    """
    if not requested_energy:
        return 0.5  # No preference
    if not dog_energy:
        return 0.5  # Unknown dog energy
    return 1.0 if dog_energy == requested_energy else 0.0


def match_training_level(dog_training, requested_training):
    """
    Match dog training level with requested training level.
    Returns 1.0 if match, 0.0 if no match, 0.5 if no preference.
    """
    if not requested_training:
        return 0.5  # No preference
    if not dog_training:
        return 0.5  # Unknown dog training
    # Exact match preferred
    return 1.0 if dog_training.lower() == requested_training.lower() else 0.0


def match_kids_compatibility(dog_gets_along_with_kids, has_kids):
    """
    Match dog's compatibility with kids.
    Returns 1.0 if compatible, 0.0 if incompatible, 0.5 if unknown.
    """
    if has_kids is None:
        return 0.5  # No info about kids
    if dog_gets_along_with_kids is None:
        return 0.5  # Unknown dog compatibility with kids

    # If person has kids, dog must get along with kids
    if has_kids:
        return 1.0 if dog_gets_along_with_kids else 0.0
    else:
        # If no kids, dog compatibility with kids is less critical
        return 1.0


def match_pets_compatibility(dog_gets_along_with_dogs, dog_gets_along_with_cats, has_other_pets):
    """
    Match dog's compatibility with other pets.
    Returns 1.0 if compatible, 0.0 if incompatible, 0.5 if unknown.
    """
    if has_other_pets is None:
        return 0.5  # No info about other pets

    if not has_other_pets:
        # No other pets, so compatibility doesn't matter much
        return 1.0

    # Person has other pets
    # Dog must get along with dogs or cats (we'll assume if either is true, it's somewhat compatible)
    if dog_gets_along_with_dogs is None and dog_gets_along_with_cats is None:
        return 0.5  # Unknown compatibility

    if dog_gets_along_with_dogs or dog_gets_along_with_cats:
        return 1.0
    else:
        return 0.0


def match_home_requirements(has_yard, has_house):
    """
    Match dog's home requirements with person's home setup.
    Returns 1.0 if suitable, 0.5 if acceptable, 0.0 if unsuitable.
    """
    if has_yard is None or has_house is None:
        return 0.5  # Missing info

    # Ideal: has house and yard
    if has_house and has_yard:
        return 1.0
    # Acceptable: has house
    elif has_house:
        return 0.75
    # Not ideal
    else:
        return 0.0


def calculate_match_score(dog, adoption_request):
    """
    Calculate overall match score between a dog and an adoption request.

    Args:
        dog: Dictionary with dog information from database
        adoption_request: Dictionary with adoption request information from database

    Returns:
        Dictionary with:
        - score: Overall match percentage (0-100)
        - details: Dictionary with individual match scores for each criteria
    """

    # Initialize match scores
    matches = {}

    # 1. Gender match
    matches['gender'] = match_gender(
        dog.get('gender'),
        adoption_request.get('requested_gender')
    )

    # 2. Size match
    matches['size'] = match_size(
        dog.get('size'),
        adoption_request.get('requested_size')
    )

    # 3. Energy level match
    matches['energy_level'] = match_energy_level(
        dog.get('level_of_training'),  # Using training as proxy for energy
        adoption_request.get('requested_level_energy')
    )

    # 4. Training level match
    matches['training_level'] = match_training_level(
        dog.get('level_of_training'),
        adoption_request.get('requested_level_of_train')
    )

    # 5. Kids compatibility
    matches['kids_compatibility'] = match_kids_compatibility(
        dog.get('get_along_with_kids'),
        adoption_request.get('has_kids')
    )

    # 6. Pets compatibility
    matches['pets_compatibility'] = match_pets_compatibility(
        dog.get('get_along_with_dogs'),
        dog.get('get_along_with_cats'),
        adoption_request.get('has_other_pets')
    )

    # 7. Home requirements
    matches['home_requirements'] = match_home_requirements(
        adoption_request.get('has_yard'),
        adoption_request.get('has_house')
    )

    # Calculate average score
    total_score = sum(matches.values())
    num_criteria = len(matches)
    overall_score = (total_score / num_criteria) * 100

    return {
        'score': round(overall_score, 2),
        'details': {k: round(v * 100, 2) for k, v in matches.items()}
    }


def get_match_explanation(match_result):
    """
    Get a human-readable explanation of the match result.

    Args:
        match_result: Dictionary returned from calculate_match_score

    Returns:
        String with explanation of the match
    """
    score = match_result['score']
    details = match_result['details']

    explanation = f"Overall Match: {score}%\n\n"
    explanation += "Detailed Breakdown:\n"

    for criterion, value in details.items():
        criterion_display = criterion.replace('_', ' ').title()
        explanation += f"  • {criterion_display}: {value}%\n"

    if score >= 80:
        explanation += "\n✓ Excellent match!"
    elif score >= 60:
        explanation += "\n✓ Good match!"
    elif score >= 40:
        explanation += "\n⊙ Fair match - consider carefully"
    else:
        explanation += "\n✗ Poor match - may not be suitable"

    return explanation
