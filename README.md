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