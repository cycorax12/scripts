# Monthly Operational Snapshot ETL
**Spring Boot → Oracle → Elasticsearch → Kibana**

## Objective

Build a monthly ETL process that extracts all currently open operational entities from Oracle, enriches them with common Event information, and indexes them into Elasticsearch for Kibana reporting.

The solution should be:
- Optimized for performance
- Easy to maintain
- Modular
- Easily extensible for new entity types

---

## Overall Flow

```text
Monthly Scheduler
        │
        ▼
1. Extract Open Events
        │
        ▼
Build EventContext Map
(announcementId -> event details)
        │
        ├──────────────┬──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
 Event Diary      Cash Tasks    Approval Tasks    PayRecs
                                                    │
                                                    ▼
                                                 Postings
        │
        ▼
Enrich every document using EventContext
        │
        ▼
Bulk Index into Elasticsearch
```

## Processing Order

1. Extract Open Events
2. Build EventContext Map
3. Extract Event Diary
4. Extract Cash Tasks
5. Extract Approval Tasks
6. Extract PayRecs
7. Extract Postings
8. Bulk Index into Elasticsearch

## Event Context

Create an in-memory lookup:

```java
Map<Long, EventContext> eventContextMap;
```

Key:
- announcementId

Value:
- eventCode
- eventDescription
- payDate
- region
- eventOwner

All remaining entity extractors must enrich their documents using this map instead of repeatedly joining Event tables.

## Entity Extractors

Each extractor should retrieve only:
- Entity Primary Key
- announcementId
- Entity-specific fields
- Status

Avoid joining Event tables in every SQL query.

## Elasticsearch Index

Use a single Elasticsearch index:

```text
operational-open-snapshots
```

Do NOT create monthly indices.

## Elasticsearch Document

```json
{
  "snapshotDate": "2026-07-31",
  "snapshotMonth": 7,
  "snapshotYear": 2026,
  "snapshotMonthKey": "2026-07",

  "entityType": "PAYREC",
  "entityId": "12345",

  "announcementId": "9001",

  "eventCode": "DVD001",
  "eventDescription": "Dividend",
  "eventOwner": "Corporate Actions",
  "region": "EMEA",
  "payDate": "2026-05-10",

  "status": "OPEN",

  "attributes": {
    "amount": 1000,
    "currency": "USD"
  }
}
```

## Required Common Fields

- snapshotDate
- snapshotMonth
- snapshotYear
- snapshotMonthKey
- entityType
- entityId
- announcementId
- eventCode
- eventDescription
- eventOwner
- region
- payDate
- status

## Elasticsearch Document ID

```text
snapshotYear_snapshotMonth_entityType_entityId
```

Example:

```text
2026_07_EVENT_100
2026_07_PAYREC_555
2026_07_TASK_777
```

## Performance Requirements

### Oracle
- Query Open Events only once.
- Avoid repeated joins.
- Stream results where possible.
- Fetch only required columns.

### Application
- Build EventContext once.
- Use HashMap lookups.
- Modular extractor per entity.
- Minimize object creation.

### Elasticsearch
- Use Bulk API.
- Configurable batch size (500–1000).
- Retry failed bulk operations.
- Log failures.

## Suggested Package Structure

```text
scheduler/
extractor/
service/
model/
repository/
config/
```

## Kibana Reporting Goals

- Open Events
- Open PayRecs
- Open Tasks
- Open Postings
- Open Diary Entries
- Region analysis
- Event Owner analysis
- Event Code analysis
- Entity Type analysis
- Monthly trends
- Year-over-Year trends
- Aging analysis using Pay Date

## Out of Scope

- firstSeenMonth
- isNew
- Incremental updates
- Delete operations

Monthly snapshots are append-only.

## Design Principles

- Single Elasticsearch index
- Monthly append-only snapshots
- Event extracted once and reused
- Minimal SQL joins
- Modular extractors
- Bulk indexing
- Self-contained Elasticsearch documents
