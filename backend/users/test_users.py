from .user_profile import UserProfile
from .manage_user_profiles import (make_table, insert_user_profile, load_user_profile)

# Preset Example Users

CASUAL_WALKER = UserProfile(
    user_id="test_user_1",
    requires_wheelchair=False,
    accessibility_weight=0.4,
    urban_weight=0.3,
    relaxed_weight=0.5
)

ACCESS_WALKER = UserProfile(
    user_id="test_user_2",
    requires_wheelchair=True,
    accessibility_weight=0.8,
    urban_weight=0.5,
    relaxed_weight=0.5
)

def initialize_test_users():
    make_table()
    insert_user_profile(CASUAL_WALKER)
    insert_user_profile(ACCESS_WALKER)

if __name__ == "__main__":
    initialize_test_users()
    
    test_user_1 = load_user_profile(CASUAL_WALKER.user_id)
    print(f"{test_user_1.user_id} requires wheelchair: {test_user_1.requires_wheelchair}")
