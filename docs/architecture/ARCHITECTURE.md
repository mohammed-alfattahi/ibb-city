# IBB Guide Architecture Documentation

This project follows a **Service-Selector** pattern (inspired by HackSoftware's Django Styleguide) to ensure separation of concerns, testability, and scalability.

## Core Layers

### 1. Models (`models.py`)
- **Responsibility**: Database schema definition and simple row-level logic (e.g., `__str__`, property computations).
- **Rule**: NO complex business logic, NO cross-model orchestration, NO external API calls.

### 2. Selectors (`selectors.py`)
- **Responsibility**: Fetching data from the database.
- **Rule**: Must return QuerySets, Lists, or Dictionaries. NO creating/updating/deleting data.
- **Why**: Keeps read logic separate from write logic; easy to memoize or optimize.

### 3. Services (`services.py`)
- **Responsibility**: Business logic, orchestration, and writing to the DB.
- **Rule**: Functions that take arguments and perform an action (e.g., `create_establishment`, `approve_ad`).
- **Structure**:
    - Validate inputs (if not done by serializers/forms).
    - Perform atomic transactions.
    - Trigger side effects (emails, notifications).
    - Return the result (Object or DTO).

### 4. Views (`views.py` or API ViewSets)
- **Responsibility**: HTTP interface.
- **Rule**: minimalist logic.
    - Parse request data.
    - Call Selectors (for GET).
    - Call Services (for POST/PUT).
    - Return Response/HTML.

### 5. API/Serializers
- **Responsibility**: Data validation and shaping for JSON responses.
- **Rule**: Keep `create()` and `update()` methods thin; ideally call a Service.

## Domain Boundaries

Code is organized by Django Apps (Domains). Cross-domain dependency is allowed but should be minimized.
- `places`: Core establishments and navigation.
- `partners`: Partner specific logic.
- `management`: Admin/Wizard logic.
- `interactions`: Reviews, comments, likes.
- `users`: Authentication and profiles.

## Refactoring Guide

When refactoring a "Fat View":
1.  Identify the "Write" logic -> Extract to `services.py`.
2.  Identify complex "Read" queries -> Extract to `selectors.py`.
3.  Replace View logic with calls to these functions.
