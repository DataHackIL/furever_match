def match_gender(dog_gender, requested_gender):
    if not requested_gender:
        return 0.5
    if not dog_gender:
        return 0.5
    return 1.0 if dog_gender == requested_gender else 0.0


def match_size(dog_size, requested_size):
    if not requested_size:
        return 0.5
    if not dog_size:
        return 0.5
    if dog_size == requested_size:
        return 1.0
    size_order = ['small', 'medium', 'large']
    if dog_size in size_order and requested_size in size_order:
        dist = abs(size_order.index(dog_size) - size_order.index(requested_size))
        return max(0.0, 1.0 - dist * 0.5)
    return 0.5


def match_energy_level(dog_training, requested_energy):
    # level_of_training is the closest proxy we have for energy
    levels = ['low', 'medium', 'high']
    if not requested_energy or not dog_training:
        return 0.5
    d = dog_training.lower().strip()
    r = requested_energy.lower().strip()
    if d == r:
        return 1.0
    if d in levels and r in levels:
        dist = abs(levels.index(d) - levels.index(r))
        return max(0.0, 1.0 - dist * 0.5)
    return 0.5


def match_training_level(dog_training, requested_training):
    levels = ['low', 'medium', 'high']
    if not requested_training:
        return 0.5
    if not dog_training:
        return 0.5
    d = dog_training.lower().strip()
    r = requested_training.lower().strip()
    if d == r:
        return 1.0
    if d in levels and r in levels:
        dist = abs(levels.index(d) - levels.index(r))
        return max(0.0, 1.0 - dist * 0.5)
    return 0.5


def match_kids_compatibility(dog_gets_along_with_kids, has_kids):
    if has_kids is None:
        return 0.5
    if dog_gets_along_with_kids is None:
        return 0.5
    if has_kids:
        return 1.0 if dog_gets_along_with_kids else 0.0
    return 1.0


def match_pets_compatibility(dog_gets_along_with_dogs, dog_gets_along_with_cats, has_other_pets):
    if has_other_pets is None:
        return 0.5
    if not has_other_pets:
        return 1.0
    if dog_gets_along_with_dogs is None and dog_gets_along_with_cats is None:
        return 0.5
    if dog_gets_along_with_dogs or dog_gets_along_with_cats:
        return 1.0
    return 0.0


def match_home_requirements(dog, has_yard, has_house):
    # Larger dogs need more space; score the fit between dog size and home type
    dog_size = dog.get('size')
    if not dog_size or has_yard is None or has_house is None:
        return 0.5
    if dog_size == 'large':
        if has_yard:
            return 1.0
        if has_house:
            return 0.7
        return 0.2
    if dog_size == 'medium':
        if has_yard:
            return 1.0
        if has_house:
            return 0.85
        return 0.5
    # small dog is fine anywhere
    return 1.0


def calculate_match_score(dog, adoption_request):
    matches = {}

    matches['gender'] = match_gender(
        dog.get('gender'),
        adoption_request.get('requested_gender')
    )
    matches['size'] = match_size(
        dog.get('size'),
        adoption_request.get('requested_size')
    )
    matches['energy_level'] = match_energy_level(
        dog.get('level_of_training'),
        adoption_request.get('requested_level_energy')
    )
    matches['training_level'] = match_training_level(
        dog.get('level_of_training'),
        adoption_request.get('requested_level_of_train')
    )
    matches['kids_compatibility'] = match_kids_compatibility(
        dog.get('get_along_with_kids'),
        adoption_request.get('has_kids')
    )
    matches['pets_compatibility'] = match_pets_compatibility(
        dog.get('get_along_with_dogs'),
        dog.get('get_along_with_cats'),
        adoption_request.get('has_other_pets')
    )
    matches['home_requirements'] = match_home_requirements(
        dog,
        adoption_request.get('has_yard'),
        adoption_request.get('has_house')
    )

    total_score = sum(matches.values())
    overall_score = (total_score / len(matches)) * 100

    return {
        'score': round(overall_score, 2),
        'details': {k: round(v * 100, 2) for k, v in matches.items()}
    }
