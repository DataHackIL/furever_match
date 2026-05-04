from furever_match.models import DogProfile, UserPreferences

def calculate_match_score(dog: DogProfile, user: UserPreferences, weights: dict = None) -> float:
    """
    Calculates a match score between a dog and a user's preferences.
    Score is returned as a float between 0.0 and 1.0.
    """
    if weights is None:
        weights = {"energy_level": 0.5, "size": 0.5}

    # Dealbreaker logic
    if user.has_cat and not dog.cat_friendly:
        return 0.0

    # Calculate distance for energy level (scale 1-5, max distance is 4)
    energy_distance = abs(user.ideal_energy_level - dog.energy_level)
    # Convert distance to a score where 0 distance = 1.0, 4 distance = 0.0
    energy_score = 1.0 - (energy_distance / 4.0)

    # Calculate distance for size (scale 1-5, max distance is 4)
    size_distance = abs(user.ideal_size - dog.size)
    size_score = 1.0 - (size_distance / 4.0)

    # Weighted average
    total_score = (energy_score * weights.get("energy_level", 0.5)) + (size_score * weights.get("size", 0.5))
    
    # Normalize by the sum of weights in case they don't add up to 1.0
    weight_sum = sum(weights.values())
    if weight_sum > 0:
        return total_score / weight_sum
    return 0.0
