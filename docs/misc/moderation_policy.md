# Moderation & Anti-Abuse Policy

## 1. Overview
This policy outlines the rules and mechanisms used by the "Ibb Tourist Guide" platform to maintain a safe, respectful, and high-quality environment for all users. We employ a hybrid moderation system combining automated analysis and manual review.

## 2. Content Standards
All user-generated content (reviews, comments, replies, business names, biographies) must adhere to the following standards.

### Prohibited Content
- **Hate Speech**: Attacks on race, religion, gender, or other protected characteristics.
- **Harassment**: Bullying, threats, or targeted abuse.
- **Profanity**: Vulgar or obscene language (English & Arabic).
- **Spam**: Repetitive content, unauthorized advertising, or gibberish.
- **Illegal Content**: Promotion of illegal acts or goods.

## 3. Automated Moderation
Our system analyzes content in real-time before it is published.

### Analysis Logic
- **Allow**: Content containing no banned terms is published immediately.
- **Warn (Severity: Low)**: Content with mild infractions triggers a warning. users may edit and resubmit, or proceed at their own risk. The event is logged.
- **Block (Severity: High/Medium)**: Content with severe infractions is **blocked** immediately. The user cannot publish it and must remove the offending terms.

### Keyword Database
- We maintain a database of banned words and phrases in both **Arabic** and **English**.
- Words are categorized by severity: `High` (Block), `Medium` (Block), `Low` (Warn).
- Text is normalized (removing diacritics, unifying characters) before analysis to prevent evasion.

## 4. Rate Limiting
To prevent spam and abuse, we enforce the following limits on user actions:

| Action | Limit | Scope |
| :--- | :--- | :--- |
| **Reviews** | 5 per hour | Per User |
| **Comments/Replies** | 10 per hour | Per User |
| **Reports** | 3 per hour | Per User |
| **Upgrade Requests** | 1 per day | Per User |
| **API Calls** | 1000 per day | Authenticated User |
| **API Calls** | 100 per day | Anonymous |

exceeding these limits will result in a temporary block on that specific action.

## 5. Manual Review & Administration
- **Moderation Log**: All warnings and blocks are logged in the `ModerationEvent` system for review by administrators.
- **Admin Actions**: Administrators can:
    - Review flagged content and recognized terms.
    - **Block Users**: Indefinitely suspend users who repeatedly violate policies.
    - **Manage Banned Words**: Add or remove terms from the database dynamically.
    - **Hide Content**: Remove content that may have bypassed automation (post-moderation).

## 6. Reporting Mechanism
Users can report inappropriate places or content via the "Report" feature.
- All reports are reviewed by the office staff.
- Reports are rate-limited to prevent abuse of the reporting system itself.

## 7. Appeals
Users who believe they were unfairly blocked or moderated may contact support for a manual review of their case.
