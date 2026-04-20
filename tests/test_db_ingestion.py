from furever_match.db_ingestion import transform_dog

sample = {
    "name": "buddy",
    "breed": "Labrador mix",
    "age": "about 2 years",
    "size": "large",
    "gender": "male",
    "description": "very friendly dog!!",
    "location": "Tel Aviv area",
    "get_along_with_cats": "yes",
    "get_along_with_dogs": "no",
    "get_along_with_kids": "yes",
    "scared_of": "loud noises",
    "happy_to": "walks",
    "level_of_training": "basic",
    "images": ["https://example.com/a.jpg"],
    "source": "site_a",
    "external_id": "12345"
}


def test_transform_dog():
    """Test that a dog record is properly transformed"""
    result = transform_dog(sample)

    assert result["name"] == "buddy"
    assert result["breed"] == "Labrador mix"
    assert result["age"] == "2 years"
    assert result["size"] == "large"
    assert result["gender"] == "male"
    assert result["description"] == "very friendly dog!!"
    assert result["location"] == "Tel Aviv"
    assert result["get_along_with_cats"] is True
    assert result["get_along_with_dogs"] is False
    assert result["get_along_with_kids"] is True
    assert result["scared_of"] == "loud noises"
    assert result["happy_to"] == "walks"
    assert result["level_of_training"] == "basic"
    assert result["source"] == "site_a"
    assert result["external_id"] == "12345"
    assert result["status"] == "available"
