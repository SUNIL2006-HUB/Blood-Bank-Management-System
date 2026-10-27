from datetime import time

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
MIN_DONOR_AGE = 18
MAX_DONOR_AGE = 65
MAX_DONATION_ML = 500

# Blood bank operating hours (24-hour clock). Update to match the SRS.
OPERATING_OPEN = time(9, 0)    # 9:00 AM
OPERATING_CLOSE = time(18, 0)  # 6:00 PM