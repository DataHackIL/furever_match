"""
Test and example usage of the Enhanced Matching System v2

This demonstrates:
1. Hard filters in action
2. Soft scoring breakdown
3. LLM character analysis
4. Final combined score
"""

from furever_match.matching_v2 import calculate_match_score_v2
from furever_match.matching_integration_v2 import get_matching_dogs_v2


# ============================================================
# Test Case 1: Good Match - Family with kids wants friendly dog
# ============================================================

def test_case_1_good_match():
    """
    Family with young kids looking for friendly, medium-sized dog
    meets: Friendly dog that loves kids
    """
    dog = {
        'id': 'dog1',
        'name': 'Max',
        'breed': 'Golden Retriever',
        'age': '3 years',
        'size': 'large',
        'gender': 'male',
        'description': 'Friendly family dog, loves to play',
        'level_of_training': 'basic',
        'get_along_with_kids': True,
        'get_along_with_dogs': True,
        'get_along_with_cats': False,
        'happy_to': 'play with kids, fetch',
        'scared_of': 'thunder',
    }

    adoption_request = {
        'id': 'req1',
        'why_adopt': 'We are a family looking for a companion for our kids',
        'has_kids': True,
        'kids_age': '5,8',
        'has_other_pets': False,
        'which_pets': None,
        'has_house': True,
        'has_yard': True,
        'has_kids': True,
        'requested_gender': 'male',
        'requested_size': 'large',
        'requested_level_energy': 'high',
        'requested_level_of_train': 'basic',
        'requested_age': None,
        'dog_living_location': 'house with yard',
        'primary_care_giver': 'both parents',
    }

    print("\n" + "="*70)
    print("TEST CASE 1: Good Match - Family with Kids")
    print("="*70)

    result = calculate_match_score_v2(dog, adoption_request, use_llm=False)

    print(f"\nDog: {dog['name']} ({dog['breed']})")
    print(f"Request: {adoption_request['why_adopt']}")
    print(f"\nPasses Hard Filters: {result['passes_filters']}")
    print(f"Filter Rejection: {result['filter_rejection_reason']}")
    print(f"\nSoft Score: {result['soft_score']}%")
    print("Soft Scores Breakdown:")
    for key, score in result['soft_scores_breakdown'].items():
        print(f"  - {key}: {score}%")
    print(f"\nFinal Score: {result['final_score']}%")
    print(f"Final Reasoning: {result['final_reasoning']}")

    return result


# ============================================================
# Test Case 2: Hard Filter Failure - Dog doesn't get along with kids
# ============================================================

def test_case_2_hard_filter_failure():
    """
    Family with kids wants a dog, but this dog doesn't get along with kids
    Should be filtered out immediately
    """
    dog = {
        'id': 'dog2',
        'name': 'Spike',
        'breed': 'Husky',
        'age': '5 years',
        'size': 'medium',
        'gender': 'male',
        'description': 'Energetic dog, not suitable for families with kids',
        'level_of_training': 'advanced',
        'get_along_with_kids': False,
        'get_along_with_dogs': True,
        'get_along_with_cats': False,
        'happy_to': 'run, hike',
        'scared_of': None,
    }

    adoption_request = {
        'id': 'req2',
        'why_adopt': 'Family looking for a dog for our kids',
        'has_kids': True,
        'kids_age': '4,7',
        'has_other_pets': False,
        'which_pets': None,
        'has_house': True,
        'has_yard': True,
        'requested_gender': None,
        'requested_size': 'medium',
        'requested_level_energy': 'high',
        'requested_level_of_train': 'basic',
        'requested_age': None,
        'dog_living_location': 'house with yard',
        'primary_care_giver': 'both parents',
    }

    print("\n" + "="*70)
    print("TEST CASE 2: Hard Filter Failure - Kids Incompatibility")
    print("="*70)

    result = calculate_match_score_v2(dog, adoption_request, use_llm=False)

    print(f"\nDog: {dog['name']} ({dog['breed']})")
    print(f"Request: {adoption_request['why_adopt']}")
    print(f"\nPasses Hard Filters: {result['passes_filters']}")
    print(f"Filter Rejection: {result['filter_rejection_reason']}")
    print(f"\nFinal Score: {result['final_score']}%")
    print(f"Expected: 0% due to hard filter failure")

    return result


# ============================================================
# Test Case 3: Hard Filter Failure - Cat incompatibility
# ============================================================

def test_case_3_cat_incompatibility():
    """
    Person has a cat, but dog doesn't get along with cats
    Should be filtered out
    """
    dog = {
        'id': 'dog3',
        'name': 'Buddy',
        'breed': 'Terrier',
        'age': '2 years',
        'size': 'small',
        'gender': 'female',
        'description': 'High prey drive dog',
        'level_of_training': 'basic',
        'get_along_with_kids': True,
        'get_along_with_dogs': True,
        'get_along_with_cats': False,
        'happy_to': 'chase toys',
        'scared_of': None,
    }

    adoption_request = {
        'id': 'req3',
        'why_adopt': 'I have a cat and want to find a compatible dog',
        'has_kids': False,
        'kids_age': None,
        'has_other_pets': True,
        'which_pets': 'cat',
        'has_house': False,
        'has_yard': False,
        'requested_gender': 'female',
        'requested_size': 'small',
        'requested_level_energy': 'medium',
        'requested_level_of_train': 'basic',
        'requested_age': None,
        'dog_living_location': 'apartment',
        'primary_care_giver': 'me',
    }

    print("\n" + "="*70)
    print("TEST CASE 3: Hard Filter Failure - Cat Incompatibility")
    print("="*70)

    result = calculate_match_score_v2(dog, adoption_request, use_llm=False)

    print(f"\nDog: {dog['name']} ({dog['breed']})")
    print(f"Request: {adoption_request['why_adopt']}")
    print(f"\nPasses Hard Filters: {result['passes_filters']}")
    print(f"Filter Rejection: {result['filter_rejection_reason']}")
    print(f"\nFinal Score: {result['final_score']}%")

    return result


# ============================================================
# Test Case 4: Older kids (15+) - Not critical
# ============================================================

def test_case_4_older_kids():
    """
    Person has kids but they're all 15+ (considered adults)
    Dog that doesn't get along with kids can still be matched
    """
    dog = {
        'id': 'dog4',
        'name': 'Scout',
        'breed': 'German Shepherd',
        'age': '4 years',
        'size': 'large',
        'gender': 'male',
        'description': 'Guard dog, not suitable for young children',
        'level_of_training': 'advanced',
        'get_along_with_kids': False,
        'get_along_with_dogs': False,
        'get_along_with_cats': False,
        'happy_to': 'protect, patrol',
        'scared_of': None,
    }

    adoption_request = {
        'id': 'req4',
        'why_adopt': 'We have teenage kids and want a guard dog',
        'has_kids': True,
        'kids_age': '16,18',
        'has_other_pets': False,
        'which_pets': None,
        'has_house': True,
        'has_yard': True,
        'requested_gender': 'male',
        'requested_size': 'large',
        'requested_level_energy': 'high',
        'requested_level_of_train': 'advanced',
        'requested_age': None,
        'dog_living_location': 'house with yard',
        'primary_care_giver': 'family',
    }

    print("\n" + "="*70)
    print("TEST CASE 4: Older Kids (15+) - Not Critical")
    print("="*70)

    result = calculate_match_score_v2(dog, adoption_request, use_llm=False)

    print(f"\nDog: {dog['name']} ({dog['breed']})")
    print(f"Request: {adoption_request['why_adopt']}")
    print(f"\nPasses Hard Filters: {result['passes_filters']}")
    print(f"Filter Rejection: {result['filter_rejection_reason']}")
    print(f"\nSoft Score: {result['soft_score']}%")
    print("Soft Scores Breakdown:")
    for key, score in result['soft_scores_breakdown'].items():
        print(f"  - {key}: {score}%")
    print(f"\nFinal Score: {result['final_score']}%")

    return result


# ============================================================
# Test Case 5: Large dog in apartment (hard filter)
# ============================================================

def test_case_5_large_dog_apartment():
    """
    Large dog but person lives in apartment (no house)
    Should fail hard filter
    """
    dog = {
        'id': 'dog5',
        'name': 'Rex',
        'breed': 'Great Dane',
        'age': '3 years',
        'size': 'large',
        'gender': 'male',
        'description': 'Gentle giant',
        'level_of_training': 'basic',
        'get_along_with_kids': True,
        'get_along_with_dogs': True,
        'get_along_with_cats': True,
        'happy_to': 'cuddle',
        'scared_of': None,
    }

    adoption_request = {
        'id': 'req5',
        'why_adopt': 'Looking for a companion for my apartment',
        'has_kids': False,
        'kids_age': None,
        'has_other_pets': False,
        'which_pets': None,
        'has_house': False,
        'has_yard': False,
        'requested_gender': None,
        'requested_size': 'large',
        'requested_level_energy': 'low',
        'requested_level_of_train': 'basic',
        'requested_age': None,
        'dog_living_location': 'apartment',
        'primary_care_giver': 'me',
    }

    print("\n" + "="*70)
    print("TEST CASE 5: Large Dog in Apartment (Hard Filter)")
    print("="*70)

    result = calculate_match_score_v2(dog, adoption_request, use_llm=False)

    print(f"\nDog: {dog['name']} ({dog['breed']})")
    print(f"Request: {adoption_request['why_adopt']}")
    print(f"\nPasses Hard Filters: {result['passes_filters']}")
    print(f"Filter Rejection: {result['filter_rejection_reason']}")
    print(f"\nFinal Score: {result['final_score']}%")
    print(f"Expected: 0% due to hard filter failure (large dog needs house)")

    return result


# ============================================================
# Test Case 6: Training level mismatch
# ============================================================

def test_case_6_training_mismatch():
    """
    Advanced dog but person has only basic training skills
    Should fail hard filter
    """
    dog = {
        'id': 'dog6',
        'name': 'Zen',
        'breed': 'Border Collie',
        'age': '2 years',
        'size': 'medium',
        'gender': 'female',
        'description': 'Highly trained working dog',
        'level_of_training': 'advanced',
        'get_along_with_kids': True,
        'get_along_with_dogs': True,
        'get_along_with_cats': True,
        'happy_to': 'work, herd',
        'scared_of': None,
    }

    adoption_request = {
        'id': 'req6',
        'why_adopt': 'First time dog owner, want a companion',
        'has_kids': False,
        'kids_age': None,
        'has_other_pets': False,
        'which_pets': None,
        'has_house': True,
        'has_yard': True,
        'requested_gender': None,
        'requested_size': 'medium',
        'requested_level_energy': 'medium',
        'requested_level_of_train': 'basic',
        'requested_age': None,
        'dog_living_location': 'house with yard',
        'primary_care_giver': 'me',
    }

    print("\n" + "="*70)
    print("TEST CASE 6: Training Level Mismatch (Hard Filter)")
    print("="*70)

    result = calculate_match_score_v2(dog, adoption_request, use_llm=False)

    print(f"\nDog: {dog['name']} ({dog['breed']})")
    print(f"Request: {adoption_request['why_adopt']}")
    print(f"\nPasses Hard Filters: {result['passes_filters']}")
    print(f"Filter Rejection: {result['filter_rejection_reason']}")
    print(f"\nFinal Score: {result['final_score']}%")
    print(f"Expected: 0% due to hard filter failure (advanced dog needs experience)")

    return result


def run_all_tests():
    """Run all test cases"""
    print("\n" + "="*70)
    print("ENHANCED MATCHING SYSTEM v2 - TEST SUITE")
    print("="*70)
    print("\nThis suite demonstrates:")
    print("1. Hard filters (clear disqualifying criteria)")
    print("2. Soft scoring (matching percentages)")
    print("3. Final combined scores")
    print("4. Detailed reasoning\n")

    results = []

    try:
        results.append(test_case_1_good_match())
        results.append(test_case_2_hard_filter_failure())
        results.append(test_case_3_cat_incompatibility())
        results.append(test_case_4_older_kids())
        results.append(test_case_5_large_dog_apartment())
        results.append(test_case_6_training_mismatch())

        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"\nTotal test cases: {len(results)}")
        print(f"Passed filters: {sum(1 for r in results if r['passes_filters'])}")
        print(f"Failed filters: {sum(1 for r in results if not r['passes_filters'])}")
        print(f"Average final score: {sum(r['final_score'] for r in results) / len(results):.2f}%")

    except Exception as e:
        print(f"\nError running tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
