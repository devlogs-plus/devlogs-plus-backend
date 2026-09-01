from authlib.integrations.flask_client import OAuth

oauth = OAuth()

def init_oauth(app):
    oauth.init_app(app)
    oauth.register(
        name='github',
        client_id=app.config['GITHUB_CLIENT_ID'],
        client_secret=app.config['GITHUB_CLIENT_SECRET'],
        access_token_url='https://github.com/login/oauth/access_token',
        authorize_url='https://github.com/login/oauth/authorize',
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'read:user user:email'}
    )
    oauth.register(
        name='hackclub',
        client_id=app.config['HACKCLUB_CLIENT_ID'],
        client_secret=app.config['HACKCLUB_CLIENT_SECRET'],
        server_metadata_url='https://auth.hackclub.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    oauth.register(
        name='hackatime',
        client_id=app.config['HACKATIME_CLIENT_ID'],
        client_secret=app.config['HACKATIME_CLIENT_SECRET'],
        authorize_url='https://hackatime.hackclub.com/oauth/authorize',
        access_token_url='https://hackatime.hackclub.com/oauth/token',
        api_base_url='https://hackatime.hackclub.com/api',
        client_kwargs={'scope': 'profile read'}
    )