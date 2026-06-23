# The WADLer

The WADLer is a quick and dirty Python POC script for quickly testing API endpoints pulled from Web Application Description Language (WADL) files. WADL files are XML files that contain API definitions for REST APIs. They outline API paths, needed parameters, HTTP methods, supported data formats, etc.

Checkout the SRA Labs Blogpost [here](https://labs.sra.io/posts/wadler/).

The WADLer allows you to quickly send a single request to each API endpoint from a remote or local WADL file with test data for each defined parameter. This can be helpful for finding endpoints that allow you to interact with them *without authentication* en-masse.

## Installation

Only tested on python `3.12.3`.

Use [poetry](https://python-poetry.org/), [pipx](https://pipx.pypa.io/stable/), or a similar tool to install the WADLer:

```bash
poetry install .

pipx install wadler
```

## Usage

**Always proxy your traffic through burp**, so you can understand the requests made, and have a log of any actions taken. Test the script on a local server before running it on the target to make sure you understand what it's doing, and that your proxy works.

Testing from a local WADL file, sleeping 1.5sec between requests, while proxying traffic through burp, without following redirects:

```bash
wadler --no-verify-ssl --http-proxy http://127.0.0.1:8080 --https-proxy http://127.0.0.1:8080 -v --sleep 1.5 --no-follow-redirects -o output.json application.wadl
```

Testing from a remote WADL file, sleeping 1.5sec between requests, while proxying traffic through burp, without following redirects:

```bash
wadler --no-verify-ssl --http-proxy http://127.0.0.1:8080 --https-proxy http://127.0.0.1:8080 -v --sleep 1.5 --no-follow-redirects -o output.json https://foo.bar/api/application.wadl
```

Full help output:

```bash
usage: WADLer [-h] [-o OUTPUT] [-v] [--endpoint ENDPOINT] [--method METHOD] [--http-proxy HTTP_PROXY] [--https-proxy HTTPS_PROXY] [--username USERNAME]
               [--password PASSWORD] [--token TOKEN] [--no-follow-redirects] [--sleep SLEEP] [--timeout TIMEOUT] [--no-verify-ssl] [--json] [--form]
               [--user-agent USER_AGENT] [--accept ACCEPT] [-H HEADER]
               wadl_source

WADL API self.parser and Tester

positional arguments:
  wadl_source           Path to WADL file or URL

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file for results (JSON)
  -v, --verbose         Verbose output

Filtering Options:
  --endpoint ENDPOINT   Only test endpoints containing this string (comma-separated for multiple)
  --method METHOD       Only test these HTTP methods (comma-separated, e.g. GET,POST)

Proxy Configuration:
  Proxying will be enabled if one or more proxy URLs are supplied.

  --http-proxy HTTP_PROXY
                        HTTP proxy URL (e.g., http://proxy:8080)
  --https-proxy HTTPS_PROXY
                        HTTPS proxy URL (e.g., http://proxy:8080)

Authentication:
  Basic authentication will be selected if a username and password is provided. Bearer token authentication will be selected in a token is provided.

  --username USERNAME   Username for Basic authentication
  --password PASSWORD   Password for Basic authentication
  --token TOKEN         Token for Bearer authentication

Request Configuration:
  --no-follow-redirects
                        Don't follow redirects
  --sleep SLEEP         Time to wait between requests in seconds
  --timeout TIMEOUT     Request timeout in seconds
  --no-verify-ssl, -k   Disable SSL certificate verification
  --json                Send request body as JSON
  --form                Send request body as form data
  --user-agent USER_AGENT
                        User-Agent header
  --accept ACCEPT       Accept header
  -H HEADER, --header HEADER
                        Additional headers (Key: Value)
```

## Dealing with the Output

The WADLer will print a report to the CLI, but also has options for JSON output.

Example JSON output:

```json
[
  {
    "method": "GET",
    "url": "http://localhost:8000/users",
    "status_code": 200,
    "reason": "OK",
    "response_time": 0.006547,
    "response_size": 48,
    "response_body": {
      "message": "Fetched users",
      "filter": "test_role"
    }
  },
  {
    "method": "POST",
    "url": "http://localhost:8000/users",
    "status_code": 200,
    "reason": "OK",
    "response_time": 0.004864,
    "response_size": 54,
    "response_body": {
      "message": "User created",
      "user": {
        "body": "test_body"
      }
    }
  },
  {
    "method": "PUT",
    "url": "http://localhost:8000/users/123",
    "status_code": 200,
    "reason": "OK",
    "response_time": 0.003647,
    "response_size": 66,
    "response_body": {
      "message": "User updated",
      "id": 123,
      "updated": {
        "body": "test_body"
      }
    }
  },
]
```

A quick `jq` command to parse out API endpoints with valid responses:

```bash
# Pull out full info
jq '[.[] | select(.status_code == 200).url]' output.json


# Pull out URLs only
jq '[.[] | select(.status_code == 200).url]' output.json
```
