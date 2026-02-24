from .user_profile import UserProfile
from .manage_user_profiles import (make_table, insert_user_profile, load_user_profile)

# Preset Example Users

CASUAL_WALKER = UserProfile(
    user_id="casual_template",

    # hard constraints
    requires_wheelchair=False,
    avoid_steps=False,

    min_length_m=800.0,
    max_length_m=4000.0,
    max_difficulty=0.6,

    bringing_dog=False,

    # preference weights
    accessibility_weight=0.8,
    urban_weight=1.0,
    relaxed_weight=1.3,
    difficulty_weight=1.0,
    safety_weight=1.1,
)

ACCESS_WALKER = UserProfile(
    user_id="access_template",

    # hard constraints
    requires_wheelchair=True,
    avoid_steps=True,

    min_length_m=500.0,
    max_length_m=3000.0,
    max_difficulty=0.4,

    bringing_dog=False,

    # preference weights
    accessibility_weight=2.0,
    urban_weight=1.2,
    relaxed_weight=0.5,
    difficulty_weight=1.5,
    safety_weight=1.8,
)

def initialize_test_users():
    make_table()
    insert_user_profile(CASUAL_WALKER)
    insert_user_profile(ACCESS_WALKER)

if __name__ == "__main__":
    initialize_test_users()
    
    test_user_1 = load_user_profile(CASUAL_WALKER.user_id)
    print(f"{test_user_1.user_id} requires wheelchair: {test_user_1.requires_wheelchair}")
