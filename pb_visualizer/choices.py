def find_choice_value(choices, key):
    for k, v in choices:
        if k == key:
            return v
    return None


def is_choice(choices, choice):
    for c in choices:
        if c[0] == choice:
            return True
    return False


GENDER_MALE = "Male"
GENDER_FEMALE = "Female"
GENDER_OTHER = "Other"
GENDER_UNKNOWN = "Unknown"

GENDER = ((GENDER_MALE, "male"), (GENDER_FEMALE, "female"), (GENDER_OTHER, "other"))


INNER_TYPE = [("int", "integer"), ("float", "float"), ("list[float]", "list of floats")]
