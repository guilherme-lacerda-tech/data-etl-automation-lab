# ADR 0002: PostgreSQL and SQLAlchemy for ETL persistence

## Status

Accepted for v0.2.0.

## Context

The ETL lab now validates, deduplicates and loads synthetic event records. A relational database makes the loaded state queryable and demonstrates a realistic batch-processing boundary.

## Decision

Use SQLAlchemy for the persistence layer and PostgreSQL as the Docker-based runtime database. SQLite remains available for fast tests and a simple local demo.

## Consequences

- The pipeline can be tested without a running database server.
- Docker Compose demonstrates the intended PostgreSQL environment.
- The README explains why PostgreSQL is used here instead of being added only as a badge.
