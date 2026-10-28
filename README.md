# Devlogs+ Backend

This repo holds all the code for the backend of Devlogs+. 

## Made With

This was made with Python using Flask. 
It also uses Flask-Bcrypt for cryptography, flask-cors for CORS, Flask-Login for session management, Flask-SQLAlchemy for SQL, and Authlib for OAuth

## Developing

When developing it is recommended to use docker as it simulates what happens on the VPS.
There is a docker compose file in this repo that holds this code and a database.

### File Organization
The files in the root are app.py, config.py, models.py, oauth.py, render_functions.py, and utils.py
app.py runs the main app
config.py holds the class for the config
models.py has the db models
oauth.py sets up the oauth apps
render_functions.py holds functions for resend (yeah i know the name is different)
utils.py has helper functions

the blueprints folder holds the files with the routes, auth.py, devlogs.py, and projects.py
auth.py has routes relating to auth
devlogs.py has all the devlog routes
projects.py is all the project routes

### Setting up the .env file

The env file holds several variables that need to be kept secret relating to the project. Do not push it to a public repo.
Here is an explanation of what you should put for the env variables

| Var                     | Explaination                                |
|-------------------------|---------------------------------------------|
| CDN_KEY                 | This is the API key for the CDN API         |
| GITHUB_CLENT_ID         | This the client id for the GitHub OAuth app |
| GITHUB_CLIENT_SECRET    | Client secret for GitHub OAuth app          |
| HACKCLUB_CLIENT_ID      | Client ID for Hack Club OAuth app           |
| HACKCLUB_CLIENT_SECRET  | Client secret for Hack Club OAuth app       |
| FRONTEND_URL            | URL for the frontend                        |
| SECRET_KEY              | Secret key for the app                      |
| RESEND_API_KEY          | API key for Resend (Mail service)           |
| HACKATIME_CLIENT_ID     | Client ID for Hackatime                     |
| HACKATIME_CLIENT_SECRET | Client secret for Hackatime                 |
| WAKATIME_CLIENT_ID      | Client ID for WakaTime                      |
| WAKATIME_CLIENT_SECRET  | Client Secret for WakaTime                  | 

The .env.example file holds a copy-pastable version you can put in your .env file

### Using the Docker Compose file

Create a .env file in the root with the settings from .env.example, then start the docker-compose file:
```shell
docker compose -f docker-compose.yaml up --build
```

The API will be available at http://localhost:8000. 
Compose saves the database data in the pgdata volume.
"devlogs-local" is the default password for the database; set one by setting the POSTGRES_PASSWORD in .env