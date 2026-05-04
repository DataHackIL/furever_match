"""
Insert sample adoption requests into Supabase
"""
from furever_match.db_ingestion import ingest_adoption_request

# Sample adoption requests data
requests_data = [
    {
        'why_adopt': 'מחפשת כלב רגוע לדירה שייתן חברה בבית. חשוב שיהיה מסתדר עם אנשים וקל יחסית לטיפול.',
        'has_kids': False,
        'kids_age': None,
        'has_other_pets': False,
        'which_pets': None,
        'has_yard': False,
        'has_house': False,
        'requested_level_of_train': 'בינוני',
        'requested_gender': 'לא משנה',
        'requested_size': 'קטן-בינוני',
        'requested_age': 'בוגר',
        'requested_level_energy': 'בינונית',
        'dog_living_location': 'דירה',
        'primary_care_giver': 'אני'
    },
    {
        'why_adopt': 'אנחנו משפחה עם ילדים שמחפשת כלב חברותי ומאוזן שיתאים לבית ולחצר.',
        'has_kids': True,
        'kids_age': '5,8',
        'has_other_pets': False,
        'which_pets': None,
        'has_yard': True,
        'has_house': True,
        'requested_level_of_train': 'בסיסי',
        'requested_gender': 'לא משנה',
        'requested_size': 'בינוני',
        'requested_age': 'צעיר',
        'requested_level_energy': 'גבוהה',
        'dog_living_location': 'בית עם חצר',
        'primary_care_giver': 'שני ההורים'
    },
    {
        'why_adopt': 'זו פעם ראשונה שאני מאמצת כלב ורוצה כלב קטן ושקט יחסית. מוכנה להשקיע באילוף.',
        'has_kids': False,
        'kids_age': None,
        'has_other_pets': False,
        'which_pets': None,
        'has_yard': False,
        'has_house': False,
        'requested_level_of_train': 'בסיסי',
        'requested_gender': 'נקבה',
        'requested_size': 'קטן',
        'requested_age': 'צעיר',
        'requested_level_energy': 'נמוכה',
        'dog_living_location': 'דירה',
        'primary_care_giver': 'אני'
    },
    {
        'why_adopt': 'אנחנו מחפשים כלב שמירה עדין אך עירני, שיתאים לבית פרטי. חשוב שיהיה ממושמע.',
        'has_kids': True,
        'kids_age': '12,15,17',
        'has_other_pets': True,
        'which_pets': 'חתול',
        'has_yard': True,
        'has_house': True,
        'requested_level_of_train': 'מתקדם',
        'requested_gender': 'זכר',
        'requested_size': 'גדול',
        'requested_age': 'בוגר',
        'requested_level_energy': 'בינונית',
        'dog_living_location': 'בית עם חצר',
        'primary_care_giver': 'אני'
    },
    {
        'why_adopt': 'אני אוהב ספורט וטיולים ומחפש כלב שיהיה שותף לפעילות יומיומית.',
        'has_kids': False,
        'kids_age': None,
        'has_other_pets': False,
        'which_pets': None,
        'has_yard': False,
        'has_house': False,
        'requested_level_of_train': 'בינוני',
        'requested_gender': 'לא משנה',
        'requested_size': 'בינוני',
        'requested_age': 'צעיר',
        'requested_level_energy': 'גבוהה',
        'dog_living_location': 'דירה',
        'primary_care_giver': 'אני'
    },
    {
        'why_adopt': 'מחפשים כלב עדין ורגוע שמתאים לילד קטן בבית. חשוב שלא יהיה תוקפני.',
        'has_kids': True,
        'kids_age': '2',
        'has_other_pets': False,
        'which_pets': None,
        'has_yard': False,
        'has_house': False,
        'requested_level_of_train': 'בינוני',
        'requested_gender': 'לא משנה',
        'requested_size': 'קטן-בינוני',
        'requested_age': 'בוגר',
        'requested_level_energy': 'נמוכה',
        'dog_living_location': 'דירה',
        'primary_care_giver': 'אמא'
    },
    {
        'why_adopt': 'מחפשת כלב קטן שיהיה לי חברה בבית. אני בבית רוב היום ויכולה לטפל בו.',
        'has_kids': False,
        'kids_age': None,
        'has_other_pets': False,
        'which_pets': None,
        'has_yard': True,
        'has_house': True,
        'requested_level_of_train': 'בסיסי',
        'requested_gender': 'לא משנה',
        'requested_size': 'קטן',
        'requested_age': 'מבוגר',
        'requested_level_energy': 'נמוכה',
        'dog_living_location': 'בית עם חצר',
        'primary_care_giver': 'אני'
    },
    {
        'why_adopt': 'יש לנו כלב נוסף בבית ואנחנו רוצים לאמץ עוד כלב שיסתדר עם כלבים אחרים.',
        'has_kids': False,
        'kids_age': None,
        'has_other_pets': True,
        'which_pets': 'כלב',
        'has_yard': True,
        'has_house': True,
        'requested_level_of_train': 'בינוני',
        'requested_gender': 'לא משנה',
        'requested_size': 'בינוני',
        'requested_age': 'בוגר',
        'requested_level_energy': 'בינונית',
        'dog_living_location': 'בית עם חצר',
        'primary_care_giver': 'אני והבת זוג'
    },
    {
        'why_adopt': 'אני גרה עם שותפים ומחפשת כלב קטן וחברותי שלא ינבח הרבה ויתאים לדירה.',
        'has_kids': False,
        'kids_age': None,
        'has_other_pets': False,
        'which_pets': None,
        'has_yard': False,
        'has_house': False,
        'requested_level_of_train': 'בסיסי',
        'requested_gender': 'לא משנה',
        'requested_size': 'קטן',
        'requested_age': 'צעיר',
        'requested_level_energy': 'בינונית',
        'dog_living_location': 'דירה',
        'primary_care_giver': 'אני'
    },
    {
        'why_adopt': 'אנחנו מחפשים כלב משפחתי שמסתדר עם ילדים ועם חתולים. חשוב שיהיה רגוע בבית.',
        'has_kids': True,
        'kids_age': '6,9',
        'has_other_pets': True,
        'which_pets': 'חתול',
        'has_yard': True,
        'has_house': True,
        'requested_level_of_train': 'בינוני',
        'requested_gender': 'לא משנה',
        'requested_size': 'בינוני',
        'requested_age': 'בוגר',
        'requested_level_energy': 'בינונית',
        'dog_living_location': 'בית עם חצר',
        'primary_care_giver': 'שני ההורים'
    }
]

# Insert each adoption request
inserted_count = 0
for req in requests_data:
    try:
        request_id = ingest_adoption_request(req)
        if request_id:
            inserted_count += 1
            print(f'✓ Inserted adoption request {inserted_count}: {req["primary_care_giver"]} (ID: {request_id})')
        else:
            print(f'✗ Failed to insert: {req["primary_care_giver"]}')
    except Exception as e:
        print(f'✗ Error inserting {req["primary_care_giver"]}: {str(e)}')

print(f'\n✅ Successfully inserted {inserted_count} adoption requests!')
