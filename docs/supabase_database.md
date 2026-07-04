# Supabase Database Setup

Run this before production testing:

1. Open Supabase project.
2. Go to `SQL Editor`.
3. Paste and run the SQL from:

```text
supabase/schema.sql
```

This creates:

- `public.user_profiles`
- `public.recommendation_history`

Both tables use Row Level Security. Users can only read/write their own rows through their Supabase session.

The backend saves data after each successful recommendation:

- latest profile is upserted into `user_profiles`
- recommendation run is inserted into `recommendation_history`

Do not disable RLS for these tables.
