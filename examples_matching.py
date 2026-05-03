"""
Example usage of the matching algorithm
"""
from furever_match.matching import calculate_match_score, get_match_explanation


def example_perfect_match():
    """Example of a perfect match"""
    dog = {
        'name': 'Max',
        'gender': 'male',
        'size': 'medium',
        'level_of_training': 'intermediate',
        'get_along_with_kids': True,
        'get_along_with_dogs': True,
        'get_along_with_cats': True,
    }

    request = {
        'primary_care_giver': 'John Doe',
        'requested_gender': 'male',
        'requested_size': 'medium',
        'requested_level_energy': 'medium',
        'requested_level_of_train': 'intermediate',
        'has_kids': True,
        'has_other_pets': False,
        'has_yard': True,
        'has_house': True,
    }

    result = calculate_match_score(dog, request)
    print("=" * 60)
    print("EXAMPLE 1: Perfect Match")
    print("=" * 60)
    print(f"Dog: {dog['name']}")
    print(f"Person: {request['primary_care_giver']}")
    print()
    print(get_match_explanation(result))
    print()


def example_poor_match():
    """Example of a poor match"""
    dog = {
        'name': 'Rocky',
        'gender': 'male',
        'size': 'large',
        'level_of_training': 'advanced',
        'get_along_with_kids': False,
        'get_along_with_dogs': False,
        'get_along_with_cats': False,
    }

    request = {
        'primary_care_giver': 'Jane Smith',
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
    print("=" * 60)
    print("EXAMPLE 2: Poor Match")
    print("=" * 60)
    print(f"Dog: {dog['name']}")
    print(f"Person: {request['primary_care_giver']}")
    print()
    print(get_match_explanation(result))
    print()


def example_fair_match():
    """Example of a fair match"""
    dog = {
        'name': 'Bella',
        'gender': 'female',
        'size': 'small',
        'level_of_training': 'basic',
        'get_along_with_kids': True,
        'get_along_with_dogs': None,  # Unknown
        'get_along_with_cats': True,
    }

    request = {
        'primary_care_giver': 'Sarah Johnson',
        'requested_gender': 'female',
        'requested_size': 'small',
        'requested_level_energy': 'low',
        'requested_level_of_train': 'basic',
        'has_kids': False,
        'has_other_pets': True,  # Cats
        'has_yard': False,
        'has_house': True,
    }

    result = calculate_match_score(dog, request)
    print("=" * 60)
    print("EXAMPLE 3: Fair Match")
    print("=" * 60)
    print(f"Dog: {dog['name']}")
    print(f"Person: {request['primary_care_giver']}")
    print()
    print(get_match_explanation(result))
    print()


if __name__ == '__main__':
    example_perfect_match()
    example_poor_match()
    example_fair_match()
