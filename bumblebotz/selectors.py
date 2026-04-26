"""
Bumble web app URLs and XPath/CSS selectors.
To be updated by inspecting bumble.com in the browser (login, discover, like/pass, profile, messages).
"""
# Base URLs
BASE_URL = "https://bumble.com"
LOGIN_URL = "https://bumble.com/get-started"
# App / discover (exact path may vary; inspect after login)
APP_DISCOVER_URL = "https://bumble.com/app"
MESSAGES_URL = "https://bumble.com/app/matches"

# Modal / overlay (inspect Bumble DOM for modal container)
# modal_container = "//div[contains(@class, 'modal') or contains(@class, 'overlay')]"  # placeholder

# Login (placeholder – inspect "Sign in", "Continue with Facebook", etc.)
# LOGIN_BUTTON = "//a[contains(text(), 'Sign in')]"
# FACEBOOK_BUTTON = "//button[contains(., 'Facebook')]"
# EMAIL_INPUT = "//input[@type='email']"
# PASSWORD_INPUT = "//input[@type='password']"

# Discover: like (checkmark) / pass (X) – placeholders
# LIKE_BUTTON = "//button[@aria-label='Like'] or //button[contains(@class, 'like')]"
# PASS_BUTTON = "//button[@aria-label='Pass'] or //button[contains(@class, 'pass')]"
# CARD_CONTAINER = "//div[contains(@class, 'profile-card') or contains(@class, 'encounter')]"

# Profile (name, age, bio, photos) – placeholders
# PROFILE_NAME_AGE = "//h1 or //div[contains(@class, 'name')]"
# PROFILE_BIO = "//div[contains(@class, 'bio')] or //p"
# PROFILE_IMAGES = "//img[contains(@src, 'bumble') or contains(@src, 'images')]"

# Popups (e.g. "Upgrade", "Turn on notifications") – placeholders
# POPUP_CLOSE = "//button[contains(@aria-label, 'Close')] or //*[contains(text(), 'Not now')]"
