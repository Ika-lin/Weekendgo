This folder contains the demo SQLite snapshots used by Weekendgo.

- `meituan_v2.db`: mock users, POIs, consumption records, deals, and social connections.
- `memories.db`: empty lightweight AI memory table for fresh reviewer sessions.

The backend can recreate missing tables and seed core mock data on startup, but these snapshots are committed so reviewers can see the prepared demo state immediately after cloning.
