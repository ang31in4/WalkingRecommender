import os
import sys

# Allow running this file directly in PyCharm ("Run") by ensuring the repo root
# is on PYTHONPATH (so `import backend...` works).
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from backend.users.user_profile import UserProfile
from backend.users.manage_user_profiles import (
    make_table,
    insert_user_profile,
    save_user_profile,
)

# Preset Example Users

CASUAL_WALKER = UserProfile(
    user_id="casual_template",

    # step data
    current_steps= 0,
    step_goal= 4000,
    step_length_m= 0.7,

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
    difficulty_weight=1.0,
    safety_weight=1.1,
    step_goal_weight=1.0
)

ACCESS_WALKER = UserProfile(
    user_id="access_template",

    # step data
    current_steps= 0,
    step_goal= 1000,
    step_length_m= 0.5,

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
    difficulty_weight=1.5,
    safety_weight=1.8,
    step_goal_weight=0.8
)

FITNESS_WALKER = UserProfile(
    user_id="fitness_template",

    # step data
    current_steps= 0,
    step_goal= 8000,
    step_length_m= 0.8,

    requires_wheelchair=False,
    avoid_steps=False,

    min_length_m=1500.0,
    max_length_m=None,
    max_difficulty=None,

    bringing_dog=False,

    accessibility_weight=0.2,
    urban_weight=0.5,
    difficulty_weight=1.5,
    safety_weight=0.6,
    step_goal_weight=1.5
)

DOG_WALKER = UserProfile(
    user_id="dog_owner_template",

    # step data
    current_steps= 0,
    step_goal= 6000,
    step_length_m= 0.7,

    requires_wheelchair=False,
    avoid_steps=True,

    min_length_m=500.0,
    max_length_m=3000.0,
    max_difficulty=0.6,

    bringing_dog=True,

    accessibility_weight=0.9,
    urban_weight=0.7,
    difficulty_weight=0.6,
    safety_weight=1.4,
    step_goal_weight=1.0
)

LOOSE_USER = UserProfile(
    user_id="Ada_Lovelace",

    # step data
    current_steps= 0,
    step_goal= 4000,
    step_length_m= 0.7,

    requires_wheelchair=False,
    avoid_steps=False,

    min_length_m=500.0,
    max_length_m=5000.0,
    max_difficulty=None,

    bringing_dog=False,

    accessibility_weight=0.2,
    urban_weight=0.6,
    difficulty_weight=0.6,
    safety_weight=1.0,
    step_goal_weight=1.8
)

NO_PREF = UserProfile(
    user_id="test_no_preference",

    current_steps=0,
    step_goal=None,
    step_length_m=0.6,

    requires_wheelchair=False,
    avoid_steps=False,

    min_length_m=None,
    max_length_m=None,
    max_difficulty=None,

    bringing_dog=False,

    accessibility_weight=1.0,
    urban_weight=1.0,
    difficulty_weight=1.0,
    safety_weight=1.0,
    step_goal_weight=1.0
)

def initialize_test_users():
    make_table()
    insert_user_profile(CASUAL_WALKER)
    insert_user_profile(ACCESS_WALKER)
    insert_user_profile(FITNESS_WALKER)
    insert_user_profile(DOG_WALKER)
    insert_user_profile(NO_PREF)
    insert_user_profile(LOOSE_USER)

if __name__ == "__main__":
    #initialize_test_users()
    save_user_profile(LOOSE_USER)
