

CLUB_BLACKLIGHT = {
    "name": "Club Blacklight",
    "path": "club_blacklight",
    "iban": "NL12IBAN123456",
    "commission": 50,
    "location": {
        "name": "Blacklight House",
        "street": "Nieuwezijds Voorburgwal",
        "street_number": "147",
        "postal_code": "1012",
        "postal_code_letters": "RJ",
        "city": "Amsterdam",
        "maps_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d5793.346928128371!2d4.88922109012838!3d52."
                    "374004136611084!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47c609c6c0880e15%3A0x39914e99"
                    "b51dcf8a!2sKoninklijk%20Paleis%20Amsterdam!5e0!3m2!1snl!2snl!4v1595000028414!5m2!1snl!2snl",
    },
    "invoice": {
        "legal_name": "Club Blacklight BV",
        "street": "Nieuwezijds Voorburgwal",
        "street_number": "147",
        "postal_code": "1012",
        "postal_code_letters": "RJ",
        "city": "Amsterdam",
        "country": "Nederland",
        "kvk": "KVK24680",
        "vat": "BTW12312312312",
    },
    "logos": [2, 7],
}
DOWN_UNDER = {
    "name": "Down Under",
    "path": "down_under",
    "iban": "NL34IBAN345678",
    "commission": 60,
    "location": {
        "name": "Australia Alley",
        "street": "Jodenbreestraat",
        "street_number": "4",
        "postal_code": "1011",
        "postal_code_letters": "NK",
        "city": "Amsterdam",
        "maps_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2896.7988862853736!2d4.895345317603952!3d5"
                    "2.372091819437216!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x77611f40a53cc979!2s"
                    "Museum%20Het%20Rembrandthuis!5e0!3m2!1snl!2snl!4v1595000573316!5m2!1snl!2snl",
    },
    "invoice": {
        "legal_name": "Down Under BV",
        "street": "Jodenbreestraat",
        "street_number": "4",
        "postal_code": "1011",
        "postal_code_letters": "NK",
        "city": "Amsterdam",
        "country": "Nederland",
        "kvk": "KVK13579",
        "vat": "BTW34534534534",
    },
    "logos": [3, 4],
}
NEON_DISTRICT = {
    "name": "Neon District",
    "path": "neon_district",
    "iban": "NL56IBAN567890",
    "commission": 58,
    "location": {
        "name": "Neon Club",
        "street": "Kalverstraat",
        "street_number": "92",
        "postal_code": "1012",
        "postal_code_letters": "PH",
        "city": "Amsterdam",
        "maps_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d4871.9144587453475!2d4.889415495016657!3d5"
                    "2.37119554012523!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x7741a77a95c86bf2!2s"
                    "Amsterdam%20Museum!5e0!3m2!1snl!2snl!4v1595000681707!5m2!1snl!2snl",
    },
    "invoice": {
        "legal_name": "Neon District BV",
        "street": "Kalverstraat",
        "street_number": "92",
        "postal_code": "1012",
        "postal_code_letters": "PH",
        "city": "Amsterdam",
        "country": "Nederland",
        "kvk": "KVK12345",
        "vat": "BTW67867867867",
    },
    "logos": [2, 4],
}
ROCK_PARK = {
    "name": "Rock Park",
    "path": "rock_park",
    "iban": "NL78IBAN789012",
    "commission": 55,
    "location": {
        "name": "Club Rock",
        "street": "Herengracht",
        "street_number": "386",
        "postal_code": "1016",
        "postal_code_letters": "CJ",
        "city": "Amsterdam",
        "maps_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d4872.12398920667!2d4.888170950033742!3d52.3"
                    "6929587747344!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x47c609c26cdd9f3f%3A0xddd4a1b87"
                    "af1336f!2sGrachtenmuseum%20Amsterdam!5e0!3m2!1snl!2snl!4v1595000933546!5m2!1snl!2snl",
    },
    "invoice": {
        "legal_name": "Rock Park BV",
        "street": "Herengracht",
        "street_number": "386",
        "postal_code": "1016",
        "postal_code_letters": "CJ",
        "city": "Amsterdam",
        "country": "Nederland",
        "kvk": "KVK67890",
        "vat": "BTW78978978978",
    },
    "logos": [4, 6],
}


CLUBS = [CLUB_BLACKLIGHT, DOWN_UNDER, NEON_DISTRICT, ROCK_PARK]

CURRENT_PARTY_DAYS = [0, 1, 4, 5]
PAST_PARTY_DAYS = [1, 2, 5, 7, 8, 14, 15, 18, 21, 25, 27, 28]


PROMOTER_ALICE = {
    "first_name": "Alice",
    "last_name": "Test",
    "business_entity": False,
    "iban": "NL54IBAN876543",
    "commission": 12,
    "invoice": {
        "legal_name": "Alice Test",
        "street": "Pierre de Coubertinplein",
        "street_number": "4",
        "postal_code": "1362",
        "postal_code_letters": "LB",
        "city": "Almere",
        "country": "Nederland",
        "kvk": "KVK98765",
        "vat": "BTW87687687687",
    },
    "code": "123456",
}
PROMOTER_BOB = {
    "first_name": "Bob",
    "last_name": "Test",
    "business_entity": True,
    "iban": "NL32IBAN874931",
    "commission": 20,
    "invoice": {
        "legal_name": "BoB Test",
        "street": "Pierre de Coubertinplein",
        "street_number": "4",
        "postal_code": "1362",
        "postal_code_letters": "LB",
        "city": "Almere",
        "country": "Nederland",
        "kvk": "KVK76543",
        "vat": "BTW54645645632",
    },
    "code": "571242",
}
PROMOTER_CHARLIE = {
    "first_name": "Charlie",
    "last_name": "Test",
    "business_entity": False,
    "iban": "NL98IBAN120987",
    "commission": 15,
    "invoice": {
        "legal_name": "Charlie Test",
        "street": "Pierre de Coubertinplein",
        "street_number": "4",
        "postal_code": "1362",
        "postal_code_letters": "LB",
        "city": "Almere",
        "country": "Nederland",
        "kvk": "KVK65432",
        "vat": "BTW23456734578",
    },
    "code": "385478",
}


PROMOTERS = [PROMOTER_ALICE, PROMOTER_BOB, PROMOTER_CHARLIE]
PROMOTER_CODES = [c["code"] for c in PROMOTERS]


BUYER_DAVE = {
    "first_name": "Dave",
    "last_name": "Test",
    "email": "dave@purchase.com",
}
BUYER_ERIN = {
    "first_name": "Erin",
    "last_name": "Test",
    "email": "erin@purchase.com",
}
BUYER_GRACE = {
    "first_name": "Grace",
    "last_name": "Test",
    "email": "grace@purchase.com",
}


BUYERS = [BUYER_DAVE, BUYER_ERIN, BUYER_GRACE]
