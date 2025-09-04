# Propylon Document Manager Assessment

The Propylon Document Management Technical Assessment is a simple (and incomplete) web application consisting of a basic API backend and a React based client.  This API/client can be used as a bootstrap to implement the specific features requested in the assessment description. 

## Getting Started
### API Development
The API project is a [Django/DRF](https://www.django-rest-framework.org/) project that utilizes a [Makefile](https://www.gnu.org/software/make/manual/make.html) for a convenient interface to access development utilities. This application uses [SQLite](https://www.sqlite.org/index.html) as the default persistence database you are more than welcome to change this. This project requires Python 3.11 in order to create the virtual environment.  You will need to ensure that this version of Python is installed on your OS before building the virtual environment. Make sure to install `virtualenv` with the command `pip install virtualenv`. Running the below commmands should get the development environment running using the Django development server.
1. `$ make build` to create the virtual environment.
2. `$ make fixture` to create a small number of fixture file versions.
3. `$ make serve` to start the development server on port 8001.
4. `$ make test` to run the limited test suite via PyTest.

### API Request Documentation

**Endpoint:** `/files/upload/`<br>
**Method:** `POST`

**Description**: This endpoint is used to upload a new file to the server.
**Request Format:** `multipart/form-data`

#### Headers
**Authorization**: Token "{your_auth_token}"<br>
**Required:** Yes<br>
**Description:** A valid, unique token to authenticate the user and authorize the request.<br>

#### Request Body (Form Fields)
The body of the request is sent as multipart/form-data. Each field is a separate part of the form.

**file**<br>
**Required:** Yes<br>
**Type:** File<br>
**Description:** The binary data of the file to be uploaded. In the curl command, this is specified with the @ symbol, which instructs curl to read the file content from the local file path.

**file_url**<br>
**Required:** Yes<br>
**Type:** String<br>
**Description:** The desired destination path and name for the file on the server. This field provides the new file's name and its location within the server's file structure.

#### Example curl Command
`curl -X POST -H "Authorization: Token {token}" -F "file=@{path_to_local_file}" -F "file_url={requested_path_and_file_name}" "http://localhost:8001/files/upload/"`

### Client Development 
See the Readme [here](https://github.com/propylon/document-manager-assessment/blob/main/client/doc-manager/README.md)

##
[![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)
