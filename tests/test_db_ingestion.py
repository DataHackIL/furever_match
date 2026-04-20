from furever_match.db_ingestion import ingest_dog

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

#ingest_dog(sample)