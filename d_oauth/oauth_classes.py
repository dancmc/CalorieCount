from logging import Logger

log = Logger("d_oauth : OAuth2")

class OAuth1:
    def __init__(self):
        pass

    @staticmethod
    def auth_with_token(request):
        log.error("OAuth2 adapter subclass has no auth_with_token method implementation")


class OAuth2:
    def __init__(self, provider_name, token):
        pass

    @staticmethod
    def auth_with_token(token):
        log.error("OAuth2 adapter subclass has no auth_with_token method implementation")