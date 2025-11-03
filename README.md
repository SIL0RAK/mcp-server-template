# MCP Server Template

A minimal template for running an **MCP (Model Context Protocol) server** with support for authentication, PostgreSQL integration, and containerization.

---

## 🚀 Features

* 🔑 **Basic Authentication** (via API token)
* 🗄 **PostgreSQL database** integration
* 🌐 **HTTP server** for MCP transport
* 📦 **Containerization** with Docker & Docker Compose
* 🗄 [**Migrations** for database schema management](./migrations/README.md)


## 🐳 Getting Started with Containers

### Option 1: Run server only

```bash
docker build -t mcp-server .
docker run -p 8000:8000 mcp-server
```

### Option 2: Run server + database (recommended for testing)

```bash
docker compose up
```


## ⚙️ Environment Variables

The server is configured using environment variables.

| Variable       | Required | Description                                                                            |
| -------------- | -------- | -------------------------------------------------------------------------------------- |
| `API_TOKEN`    | ❌        | API token for basic authentication. If provided, clients must include it in requests.  |
| `DATABASE_URL` | ✅        | PostgreSQL connection string. Format: `postgresql://user:password@localhost:5432/mydb` |

👉 When working locally, create a `.env` file in the project root (use `.env.example` as a template).

---

## 🔌 Connecting to MCP Client

* Local: `http://localhost:8000`
* Remote: `http://<your-server-domain>`

### Authentication

If `API_TOKEN` is set, include it in your request headers:

```
Authorization: Bearer ${API_TOKEN}
```

### Required Headers

```
Content-Type: application/json
Accept: application/json, text/event-stream
```

---

## 📡 Transport Support

* ✅ Currently supports: **`streamable-http`**
* 🚧 Can be extended to support other MCP transports

---

## 🖼 Architecture Diagram

```mermaid
flowchart TD
    A[MCP Client] <-- streamable-http --> B[MCP Server]
    B <-- queries --> C[(PostgreSQL Database)]
    A -.  Call with instructions and headers .-> B:::auth
```

* **MCP Client** communicates with the server using HTTP (`streamable-http`).
* **MCP Server** handles authentication and queries.
* **PostgreSQL Database** stores and retrieves persistent data.
* Optional **API Token** can be used for secured communication.


## 🔄 Sequence Diagram (Request Flow)

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Server as MCP Server
    participant DB as PostgreSQL Database

    Client->>Server: HTTP Request (with headers & optional Bearer Token)
    Server->>Server: Validate API Token (if required)
    alt Token invalid
        Server-->>Client: 401 Unauthorized
    else Token valid / not required
        Server->>DB: Execute query
        DB-->>Server: Query result
        Server-->>Client: Response (JSON / Event Stream)
    end
```
