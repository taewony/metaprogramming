---
sources: ["summaries/00-introduction.md"]
brief: "A table is a structured way to organize data in a database using rows and columns."
---

A **table** is a fundamental component of a relational database, used to store and organize data in a structured format. In the context of the [[summaries/00-introduction]] document, a table consists of **rows** (also called records) and **columns** (also called fields). Each **row** represents a unique record, while each **column** defines a specific attribute or property of the data.

### Key Details from the Document
- **Rows**: Each row in a table represents a single entity or record. For example, in a 'customers' table, each row might represent a different customer.
- **Columns**: Columns define the attributes of the data, such as 'name', 'email', or 'grade' in a customer table.
- **Data Types**: Columns have specific data types, such as `INTEGER` for numeric values and `TEXT` for strings. For instance, the 'id' column in a table might be of type `INTEGER`, while the 'name' column might be of type `TEXT`.
- **Relationships**: Tables can be related through **primary keys (PK)** and **foreign keys (FK)**. For example, a 'orders' table might have a foreign key that references the 'id' column of the 'customers' table, establishing a relationship between the two tables.

### Related Concepts
- [[concepts/table]]
- [[concepts/primary_key]]
- [[concepts/foreign_key]]
- [[concepts/sql]]
- [[summaries/00-introduction]]

This concept is central to understanding how data is structured and managed in relational databases, as described in the [[summaries/00-introduction]] document.