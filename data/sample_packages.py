# ─────────────────────────────────────────────
# data/sample_packages.py
# Four pre-loaded demo packages covering all
# four classification scenarios
# ─────────────────────────────────────────────

SAMPLE_PACKAGES = {
    "hard_rule": {
        "id": "DEMO_001",
        "label": "Kashi Vishwanath Jyotirlinga Yatra — 6 nights",
        "scenario": "Hard rule trigger",
        "name": "Kashi Vishwanath Jyotirlinga Yatra — 6 Nights",
        "destination": "Varanasi, Prayagraj, Ayodhya",
        "group_type": "unspecified",
        "price_tier": "Standard",
        "hotel_type": "Dharamshala",
        "description": (
            "Join the sacred Kashi Vishwanath Jyotirlinga Yatra — a 6-night spiritual "
            "journey through the holy cities of Varanasi, Prayagraj and Ayodhya. "
            "Experience guided temple visits, the divine Ganga Aarti at Dashashwamedh Ghat, "
            "and a **holy dip at Triveni Sangam**. Stay in comfortable dharamshalas close "
            "to the temple precincts."
        ),
        "activities": [
            {
                "name": "Kashi Vishwanath Temple Darshan",
                "description": "Guided visit to the sacred Jyotirlinga with priest-led puja rituals.",
                "duration_hours": 4,
            },
            {
                "name": "Ganga Aarti Ceremony",
                "description": "Evening devotional ceremony on the ghats of the Ganges.",
                "duration_hours": 2,
            },
            {
                "name": "Triveni Sangam Dip",
                "description": "Holy bath at the confluence of Ganga, Yamuna and Saraswati in Prayagraj.",
                "duration_hours": 3,
            },
        ],
    },

    "single_theme": {
        "id": "DEMO_002",
        "label": "Himalayan Trek — Manali to Leh, 8 days",
        "scenario": "Single theme auto-assign",
        "name": "Himalayan High — Manali to Leh Trek",
        "destination": "Manali, Leh",
        "group_type": "couple",
        "price_tier": "Budget",
        "hotel_type": "Tent camps and mountain lodges",
        "description": (
            "An 8-day high-altitude trek from Manali to Leh through the Rohtang Pass. "
            "This is an expedition for **serious trekkers** — expect steep ascents, "
            "river crossings and overnight camping at 14,000 feet. "
            "Suitable for physically fit adventurers only. "
            "Guided by certified Himalayan mountaineers."
        ),
        "activities": [
            {
                "name": "Rohtang Pass Trek",
                "description": "Full-day high-altitude trek through snow-covered mountain passes with acclimatisation stops.",
                "duration_hours": 10,
            },
            {
                "name": "River Crossing and Rappelling",
                "description": "Technical river crossing and basic rock rappelling with safety gear.",
                "duration_hours": 5,
            },
            {
                "name": "Mountain Biking — Leh Valley",
                "description": "Guided mountain biking through rugged Leh terrain and monasteries.",
                "duration_hours": 6,
            },
            {
                "name": "Campfire and Stargazing",
                "description": "Evening bonfire at base camp with guided astronomy session.",
                "duration_hours": 2,
            },
        ],
    },

    "conflict": {
        "id": "DEMO_003",
        "label": "Maldives Escape — Luxury + Scuba, 7 nights",
        "scenario": "Multi-theme conflict → human review",
        "name": "Maldives Bliss — 7 Nights",
        "destination": "Maldives",
        "group_type": "couple",
        "price_tier": "Luxury",
        "hotel_type": "Overwater villa resort",
        "description": (
            "An intimate escape designed for couples. Stay in a **private overwater villa** "
            "with a plunge pool and direct ocean access. Enjoy **candlelit dinners** on the "
            "deck each evening, couples massage, and a sunset dolphin cruise. "
            "Also includes a full 4-day PADI scuba diving certification course — "
            "explore coral reefs and underwater ecosystems with expert instructors."
        ),
        "activities": [
            {
                "name": "PADI Scuba Diving Certification",
                "description": "4-day open water certification course. Dives at coral reefs, underwater caves and marine ecosystems.",
                "duration_hours": 16,
            },
            {
                "name": "Couples Spa and Wellness",
                "description": "Full-day wellness experience with hot stone massage, aromatherapy and private jacuzzi for two.",
                "duration_hours": 6,
            },
            {
                "name": "Sunset Dolphin Cruise",
                "description": "Romantic evening cruise for two with champagne and dolphin watching.",
                "duration_hours": 2,
            },
        ],
    },

    "human_review": {
        "id": "DEMO_004",
        "label": "Ooty Weekend Getaway — 3 nights",
        "scenario": "No theme crosses threshold → human review",
        "name": "Ooty Hill Station Retreat — 3 Nights",
        "destination": "Ooty",
        "group_type": "unspecified",
        "price_tier": "Budget",
        "hotel_type": "Standard hill resort",
        "description": (
            "A relaxing 3-night stay at a peaceful hill station property near Ooty. "
            "Includes breakfast, evening bonfire, and access to guided nature walks. "
            "Suitable for small groups, couples or solo travellers who want a quiet retreat. "
            "Close to tea gardens and viewpoints."
        ),
        "activities": [
            {
                "name": "Nature Walk — Tea Gardens",
                "description": "Gentle guided walk through Ooty tea estates with local guide.",
                "duration_hours": 3,
            },
            {
                "name": "Viewpoint Visit",
                "description": "Scenic drive and walk to Doddabetta peak viewpoint.",
                "duration_hours": 2,
            },
            {
                "name": "Evening Bonfire",
                "description": "Group bonfire at the property with light snacks.",
                "duration_hours": 1.5,
            },
        ],
    },
}
