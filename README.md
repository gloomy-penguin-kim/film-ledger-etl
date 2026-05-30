`python3 -m venv .venv`

`source .venv/bin/activate`

`pip install -r requirements.txt`

`python3 -m app.etl.ingest`

```
7:00am Render cron starts
   ↓
Python script fetches trending movies
   ↓
Python script upserts media rows into Neon
   ↓
Python script sees poster_url / backdrop_url
   ↓
Python script downloads image temporarily
   ↓
Python script uploads image to R2 / S3 / Cloudinary / etc.
   ↓
Python script updates image_asset row in Neon
   ↓
Temporary local file disappears when cron job ends
```