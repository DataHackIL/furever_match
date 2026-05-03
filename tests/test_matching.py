"""
Tests for the matching algorithm
"""
import pytest
from furever_match.matching import (
    calculate_match_score,
    get_match_explanation,
    match_gender,
    match_size,
    match_energy_level,
    match_kids_compatibility,
    match_pets_compatibility,
    match_home_requirements
)


class TestMatchingFunctions:
    """Test individual matching functions"""

    def test_match_gender_exact_match(self):
        assert match_gender("male", "male") == 1.0
        assert match_gender("female", "female") == 1.0

    def test_match_gender_no_match(self):
        assert match_gender("male", "female") == 0.0
        assert match_gender("female", "male") == 0.0

    def test_match_gender_no_preference(self):
        assert match_gender("male", None) == 0.5
        assert match_gender("female", None) == 0.5

    def test_match_gender_unknown_dog(self):
        assert match_gender(None, "male") == 0.0

    def test_match_size_exact_match(self):
        assert match_size("small", "small") == 1.0
        assert match_size("medium", "medium") == 1.0
        assert match_size("large", "large") == 1.0

    def test_match_size_no_match(self):
        assert match_size("small", "large") == 0.0

    def test_match_size_no_preference(self):
        assert match_size("medium", None) == 0.5

    def test_match_kids_compatibility_has_kids_dog_friendly(self):
        assert match_kids_compatibility(True, True) == 1.0

    def test_match_kids_compatibility_has_kids_dog_not_friendly(self):
        assert match_kids_compatibility(False, True) == 0.0

    def test_match_kids_compatibility_no_kids(self):
        assert match_kids_compatibility(False, False) == 1.0
        assert match_kids_compatibility(True, False) == 1.0

    def test_match_kids_compatibility_unknown(self):
        assert match_kids_compatibility(None, True) == 0.5
        assert match_kids_compatibility(True, None) == 0.5

    def test_match_home_requirements_ideal(self):
        assert match_home_requirements(True, True) == 1.0

    def test_match_home_requirements_only_house(self):
        assert match_home_requirements(False, True) == 0.75

    def test_match_home_requirements_no_house(self):
        assert match_home_requirements(False, False) == 0.0


class TestCalculateMatchScore:
    """Test overall match score calculation"""

    def test_perfect_match(self):
        """Test a perfect match scenario"""
        dog = {
            'gender': 'male',
            'size': 'medium',
            'level_of_training': 'intermediate',
            'get_along_with_kids': True,
            'get_along_with_dogs': True,
            'get_along_with_cats': True,
        }

        request = {
            'requested_gender': 'male',
            'requested_size': 'medium',
            'requested_level_energy': 'medium',
            'requested_level_of_train': 'intermediate',
            'has_kids': True,
            'has_other_pets': True,
            'has_yard': True,
            'has_house': True,
        }

        result = calculate_match_score(dog, request)
        assert result['score'] > 85  # Should be a very high match
        assert 'details' in result
        assert len(result['details']) == 7

    def test_poor_match(self):
        """Test a poor match scenario"""
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
        assert result['score'] < 50  # Should be a low match

    def test_match_with_missing_data(self):
        """Test matching with incomplete data"""
        dog = {
            'gender': 'male',
            'size': None,  # Missing size
            'level_of_training': 'basic',
            'get_along_with_kids': None,  # Unknown
            'get_along_with_dogs': True,
            'get_along_with_cats': None,  # Unknown
        }

        request = {
            'requested_gender': 'male',
            'requested_size': None,  # No preference
            'requested_level_energy': 'low',
            'requested_level_of_train': 'basic',
            'has_kids': True,
            'has_other_pets': False,
            'has_yard': True,
            'has_house': True,
        }

        result = calculate_match_score(dog, request)
        # Should still produce a score despite missing data
        assert 0 <= result['score'] <= 100
        assert 'details' in result


class TestMatchExplanation:
    """Test match explanation generation"""

    def test_excellent_match_explanation(self):
        """Test explanation for excellent match"""
        match_result = {
            'score': 90,
            'details': {
                'gender': 100,
                'size': 100,
                'energy_level': 100,
                'training_level': 100,
                'kids_compatibility': 100,
                'pets_compatibility': 100,
                'home_requirements': 100,
            }
        }

        explanation = get_match_explanation(match_result)
        assert "90" in explanation
        assert "Excellent match" in explanation

    def test_poor_match_explanation(self):
        """Test explanation for poor match"""
        match_result = {
            'score': 20,
            'details': {
                'gender': 0,
                'size': 0,
                'energy_level': 0,
                'training_level': 0,
                'kids_compatibility': 0,
                'pets_compatibility': 0,
                'home_requirements': 0,
            }
        }

        explanation = get_match_explanation(match_result)
        assert "20" in explanation
        assert "Poor match" in explanation
