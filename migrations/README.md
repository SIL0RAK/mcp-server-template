
## Migrations

Migrations are used to manage and version changes to the database schema.

### 📁 Location

All migration files are stored in the `migrations/` directory at the root of the project.

### 📄 Migration Files

* Each migration is a **single `.sql` file** containing the SQL statements needed to update the schema.
* The **filename** serves as the **unique migration key**, so each migration must have a unique name.

**Example:**

```
migrations/
├── 001_create_data_table.sql
├── 002_insert_some_data.sql
└── 003_create_orders_table.sql
```

### ⚙️ Application of Migrations

* Migrations are **automatically applied** when the server starts.
* The system checks which migrations have already been applied and runs any new ones in order based on their filenames.

### 🧩 Creating a New Migration

To create a new migration:

1. Create a new `.sql` file in the `migrations/` directory.
2. Name it with the next sequential number and a short description, for example:

   ```
   004_add_payment_methods.sql
   ```
3. Add your SQL statements inside the file.

**Example contents:**

```sql
ALTER TABLE data 
ADD COLUMN payment_method VARCHAR(50) DEFAULT 'credit_card' NOT NULL;
```

### ✅ Best Practices

* Use clear, descriptive filenames.
* Keep each migration **idempotent** (safe to run multiple times if necessary).
* Avoid modifying or deleting old migrations—create a new one instead.
* Test migrations locally before deploying to production.