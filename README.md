# MyLA Survey Data Application

Charlie Logan (ctlogan@umich.edu)

Application allows user to download anonymized survey data from multiple semesters.

## Development

### Pre-requisities

The sections below provide instructions for configuring, installing, and using the application. Depending on the environment you plan to run the application in, you may also need to install some or all of the following:

- [Python 3.8](https://docs.python.org/3.8/)
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Django](https://www.djangoproject.com/)

While performing any of the actions described below, use a terminal, text editor, or file utility as necessary. Sample terminal commands are provided for some steps.

### Configuration

Before running the application, you will need to prepare the configuration file: `.env` file containing key-value pairs that will be added to the environment.

- `.env`

The `.env` file serves as the primary configuration file, loading credentials for kaltura admins. A template called `.env_sample` has been provided in the root directory. The comments before the variables in the template should describe the purpose of each; some recommended values have been provided. Copy `.env_sample` file and rename it to `.env`, and update values for parameters within.

#### With Docker

Build and run the application on localhost

1.  Build an docker image

    ```sh
    docker-compose build
    ```

2.  Run django app locally

    ```sh
    docker-compose up
    ```

3.  Add root account user into database
    ```
    docker exec -it myla_survey python manage.py createsuperuser --username ROOT_USER_NAME --email EMAIL_ADDRESS
    ```
4.  Launch app from http://localhost:8000
