class ErrorCodes:  # Descriptions - https://developers.viber.com/docs/api/rest-bot-api/#broadcast
    OK = 0  # Success
    INVALID_URL = 1  # The webhook URL is not valid
    INVALID_AUTH_TOKEN = 2  # The authentication token is not valid
    BAD_DATA = 3  # There is an error in the request itself (missing comma, brackets, etc.)
    MISSING_DATA = 4  # Some mandatory data is missing
    RECEIVER_NOT_REGISTERED = 5  # The receiver is not registered to Viber
    RECEIVER_NOT_SUBSCRIBED = 6  # The receiver is not subscribed to the account
    PUBLIC_ACCOUNT_BLOCKED = 7  # The account is blocked
    PUBLIC_ACCOUNT_NOT_FOUND = 8  # The account associated with the token is not a account.
    PUBLIC_ACCOUNT_SUSPENDED = 9  # The account is suspended
    WEBHOOK_NOT_SET = 10  # No webhook was set for the account
    RECEIVER_NO_SUITABLE_DEVICE = 11  # The receiver is using a device or a Viber version that don’t support accounts
    TOO_MANY_REQUESTS = 12  # Rate control breach
    API_VERSION_NOT_SUPPORTED = 13  # Maximum supported account version by all user’s devices is less than the
    # minApiVersion in the message
    INCOMPATIBLE_WITH_VERSION = 14  # minApiVersion is not compatible to the message fields
    PUBLIC_ACCOUNT_NOT_AUTHORIZED = 15  # The account is not authorized
    INCHAT_REPLY_MESSAGE_NOT_ALLOWED = 16  # Inline message not allowed
    PUBLIC_ACCOUNT_IS_NOT_IN_LINE = 17  # The account is not inline
    NO_PUBLIC_CHAT = 18  # Failed to post to public account. The bot is missing a Public Chat interface
    CANNOT_SEND_BROADCAST = 19  # Cannot send broadcast message
    BROADCAST_NOT_ALLOWED = 20  # Attempt to send broadcast message from the bot
    UNSUPPORTED_COUNTRY = 21  # The message sent is not supported in the destination country
    PAYMENT_UNSUPPORTED = 22  # The bot does not support payment messages
    FREE_MESSAGES_EXCEEDED = 23  # The non-billable bot has reached the monthly threshold of free out of session
    # messages
    NO_BALANCE = 24  # No balance for a billable bot (when the “free out of session messages” threshold has been
    # reached)
