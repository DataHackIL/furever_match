from furever_match.db_ingestion import ingest_adoption_request

# Test request: family with kids, no other pets, wants a medium trained dog
request_id = ingest_adoption_request({
    "why_adopt": "אנחנו משפחה עם ילדים שתמיד חלמה על כלב. רוצים כלב שיהיה חבר טוב לילדים",
    "has_kids": "yes",
    "kids_age": "6, 9",
    "has_other_pets": "no",
    "has_yard": "yes",
    "has_house": "yes",
    "requested_size": "medium",
    "requested_level_of_train": "medium",
    "requested_level_energy": "medium",
    "dog_living_location": "בבית עם גישה לחצר",
    "primary_care_giver": "אמא",
})

print(f"Inserted adoption request: {request_id}")
