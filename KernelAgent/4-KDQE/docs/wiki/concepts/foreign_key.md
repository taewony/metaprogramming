---
sources: ["summaries/00-introduction.md"]
brief: "A foreign key is a field in one table that links to the primary key of another table."
---

A **foreign key** is a field (or collection of fields) in one table that links to the **primary key** of another table. This relationship establishes a connection between the data in two tables, ensuring referential integrity.

### Key Details from the Source Document
- A foreign key is used to maintain a link between tables, such as how a `customer_id` in an `orders` table references the `id` in a `customers` table.
- It helps enforce **data consistency** by ensuring that values in the foreign key column exist in the referenced primary key column.
- Foreign keys are essential for creating **relationships** like 1:N (one-to-many) between tables.

### Related Concepts
- [[concepts/primary_key]]: The primary key is the unique identifier for a table, which a foreign key references.
- [[concepts/sql]]: SQL is used to manage and query relational databases, including defining and using foreign keys.
- [[summaries/00-introduction]]: This summary provides an overview of database concepts, including foreign keys and their role in relational databases.