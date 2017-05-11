from .oauth_classes import *


class Auth:
    def __init__(self, config):
        # load config for social networks
        # config includes app-ids and secrets, scopes
        """
        Format of config :
        {
            <custom-name> : {
                class : <provider adapter class object>, :: if using auth_with_token, is only required attribute
                app_id : <app id from provider>, :: not actually needed for this....
                app_secret : <secret from provider>,  :: used for server-server verification of auth codes
                scope: [email, profile]  :: some providers require auth scopes
        }
        
        Only the class is needed for auth_with_token
        
        :param config: dict containing configuration for different providers 
        """
        self.config = config

    # def auth_with_code(self, provider_name, auth_code):
    #     """
    #     Uses auth code from oauth provider to exchange with provider for token, then uses token to
    #     grab user info according to scope
    #
    #     :param provider_name: custom name for provider defined in config
    #     :param auth_code: code provided by oauth provider
    #     :return: returns User object including access_token, refresh_token, user info
    #     """
    #     provider_config = self.config.get(provider_name)
    #
    #     user=None
    #     if not provider_config:
    #         return "No such provider defined in config."
    #     else :
    #         provider_adapter = provider_config.get("class")
    #         if not provider_adapter:
    #             "No provider adapter defined in config."
    #         else:
    #             user = provider_adapter.auth_with_code(code=auth_code,
    #                                             app_id=provider_config.get("app_id"),
    #                                             app_secret=provider_config.get("app_secret"),
    #                                             scope=provider_config.get("scope"))
    #     return user if user else None


    def auth_with_token(self, provider_name, request):
        """
                Uses auth token from oauth provider, verifies, then uses token to grab user info according to scope

                :param provider_name: custom name for provider defined in config  
                :param token: code provided by oauth provider
                :return: returns User object including access_token, user info
                """
        provider_config = self.config.get(provider_name)

        user = None
        if not provider_config:
            # TODO change return values
            return "No such provider defined in config."
        else:
            provider_adapter = provider_config.get("class")
            if not provider_adapter:
                return "No provider adapter defined in config."
            else:
                if issubclass(provider_adapter, OAuth1):
                    user = provider_adapter.auth_with_token(request)
                elif issubclass(provider_adapter, OAuth2):
                    user = provider_adapter.auth_with_token(request.form.get("token"))

        return user if user else None


