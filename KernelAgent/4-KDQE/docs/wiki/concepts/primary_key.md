---
sources: ["summaries/00-introduction.md"]
brief: "A primary key uniquely identifies each row in a table and enforces data integrity."
---

## Primary Key

A **primary key** is a column or set of columns in a table that uniquely identifies each row within that table. It serves as a unique identifier for records and ensures that no duplicate values exist in the primary key column.

### Key Characteristics
- **Uniqueness**: Each value in the primary key column must be unique.
- **Non-null**: The primary key column cannot contain NULL values.
- **Indexing**: Most databases automatically create an index on the primary key column to improve query performance.

### Role in Database Design
Primary keys are essential for maintaining referential integrity between tables. They are used by foreign keys in related tables to establish relationships.

### Example
In the context of the [[summaries/00-introduction]] document, the `id` column in the `customers` table is a primary key. It ensures that each customer has a unique identifier and prevents duplicate entries.

### Related Concepts
- [[concepts/primary_key]]
- [[concepts/foreign_key]]
- [[concepts/table]]
- [[concepts/sql]]
- [[concepts/database]]
- [[summaries/00-introduction]]

This concept is fundamental to understanding how relational databases organize and relate data between tables.