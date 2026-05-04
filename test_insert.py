import sys
print("Script started", file=sys.stderr)

try:
    from furever_match.db_ingestion import ingest_adoption_request
    print("Import successful", file=sys.stderr)

    test_request = {
        'why_adopt': 'Test adoption request',
        'has_kids': False,
        'kids_age': None,
        'has_other_pets': False,
        'which_pets': None,
        'has_yard': False,
        'has_house': False,
        'requested_level_of_train': 'בסיסי',
        'requested_gender': 'לא משנה',
        'requested_size': 'בינוני',
        'requested_age': 'בוגר',
        'requested_level_energy': 'בינונית',
        'dog_living_location': 'דירה',
        'primary_care_giver': 'Test'
    }

    print("About to insert", file=sys.stderr)
    result = ingest_adoption_request(test_request)
    print(f"Inserted with ID: {result}", file=sys.stderr)

except Exception as e:
    import traceback
    print(f"ERROR: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

print("Script finished", file=sys.stderr)
