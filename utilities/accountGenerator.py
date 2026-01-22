import core.state as state
import utilities.constants as constant

from utilities.loggerSetup import setup_logger
from utilities.usernameGenerator import (
    generate_counter_username,
    generate_word_username
)
from utilities.emailGenerator import (
    generate_email
)
from utilities.accountRegistration import (
    signup_user
)

# Initialize Logger
logger = setup_logger()

def generate():
    username, password, email = generateMandatoryField()
    firstname = state.get_account_firstname()
    lastname = state.get_account_lastname()

    success, msg = signup_user(
        firstname, lastname, email, username, password, False
    )

    return success, username, password


def generateMandatoryField():
    prefix = state.get_username_prefix()
    postfix = state.get_username_postfix()
    domain = constant.DEFAULT_ACCOUNT_EMAIL_DOMAIN if not state.get_account_email_domain() else state.get_account_email_domain()
    use_prefix_count = state.get_username_prefix_count_enabled()
    use_postfix_count = state.get_username_postfix_count_enabled()
    prefix_count_start_at = state.get_username_prefix_count_start_at()
    postfix_count_start_at = state.get_username_postfix_count_start_at()
    password = constant.DEFAULT_ACCOUNT_PASSWORD if not state.get_account_password() else state.get_account_password()

    if use_prefix_count or use_postfix_count:
        username, prefix_counter, postfix_counter = generate_counter_username(
            prefix=prefix,
            postfix=postfix,
            use_prefix_count=use_prefix_count,
            use_postfix_count=use_postfix_count,
            prefix_start=prefix_count_start_at,
            postfix_start=postfix_count_start_at,
        )

        if use_prefix_count:
            state.set_username_prefix_count_start_at(prefix_counter - 1)

        if use_postfix_count:
            state.set_username_postfix_count_start_at(postfix_counter - 1)

    else:
        # 🟢 Normal word-pool generator (existing behavior)
        username = generate_word_username(prefix, postfix)

    email = generate_email(prefix, postfix, domain)

    return username, password, email





