# MCP server template

## Features

* Basic Authentication
* Connection to PostgreSQL database
* HTTP server
* Containerization

## Start container

Start docker container

```bash
docker build -t mcp-server .
docker run -p 8000:8000 mcp-server
```
OR

Start docker container and database (suggested flow for testing)

```
docker compose up
```

## Environment variables

* `API_TOKEN` - [Optional] API token for basic authentication

* `DATABASE_URL` - postgresql://user:password@localhost:5432/mydb

** If you are working locally you will need to create .env file in root directory (use .env.example as a template)