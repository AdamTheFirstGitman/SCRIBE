# Supabase Setup Guide for Plume & Mimir

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up/Login with GitHub
3. Click "New project"
4. Choose organization
5. Fill project details:
   - **Name**: `plume-mimir`
   - **Database Password**: Generate strong password (save it!)
   - **Region**: Choose closest to you
   - **Plan**: Start with Pro ($25/month) for better performance

## Step 2: Configure Database

### Apply Schema
1. Go to SQL Editor in your Supabase dashboard
2. Copy the contents of `database/schema.sql`
3. Paste and execute the SQL
4. Verify all tables were created successfully

### Enable Extensions
The schema includes these extensions (they should be auto-enabled):
- `uuid-ossp` - UUID generation
- `vector` - pgvector for embeddings
- `btree_gin` - Performance indexes

## Step 3: Get API Keys

1. Go to Settings → API
2. Copy these values:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_KEY` (keep secret!)

## Step 4: Configure Environment

1. Copy `.env.example` to `.env`
2. Fill in the Supabase values:
   ```bash
   SUPABASE_URL=https://your-project-ref.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

## Step 5: Test Connection

```bash
# Install dependencies
pip install supabase numpy

# Set environment variables
export SUPABASE_URL="your-url"
export SUPABASE_ANON_KEY="your-key"

# Run test script
python database/test_connection.py
```

You should see all tests pass ✅

## Step 6: Configure Production Settings

### Backups
1. Go to Settings → Database
2. Enable **Point-in-time Recovery** (PITR)
3. Set backup retention to **30 days**

### Performance
1. Go to Settings → Database
2. Review connection pooling settings
3. Consider **Connection pooling mode**: Transaction (for better concurrency)

### Security
1. Go to Authentication → Settings
2. Configure **Row Level Security** policies if needed
3. Review **JWT expiry settings**

### Monitoring
1. Go to Reports
2. Set up alerts for:
   - Database size (> 80% of limit)
   - API requests (approaching limits)
   - Error rates (> 1%)

## Step 7: Realtime Configuration (Phase 4)

For later phases, configure Realtime:

1. Go to Database → Replication
2. Enable replication for tables:
   - `notes`
   - `conversations`
   - `search_queries`

3. Configure realtime policies in SQL Editor:
   ```sql
   -- Enable realtime for notes
   ALTER PUBLICATION supabase_realtime ADD TABLE notes;
   ALTER PUBLICATION supabase_realtime ADD TABLE conversations;
   ```

## Cost Optimization Tips

### Supabase Pro Plan ($25/month includes):
- 8GB database
- 250GB bandwidth
- 100k monthly active users
- Point-in-time recovery
- Daily backups

### Monitor Usage:
- **Database size**: Watch for growth patterns
- **API requests**: Optimize queries to reduce calls
- **Bandwidth**: Use CDN for static assets
- **Storage**: Regular cleanup of old data

### Performance Tuning:
- Use **Connection pooling** for high concurrency
- Optimize **pgvector indexes** for your data size
- Consider **Read replicas** for future scaling
- Use **Materialized views** for complex queries

## Troubleshooting

### Common Issues:

**pgvector not working?**
- Make sure pgvector extension is enabled
- Check that embedding dimensions match (1536)
- Verify index creation was successful

**RPC functions failing?**
- Check function permissions
- Verify function parameters match exactly
- Test with simple queries first

**Connection timeouts?**
- Check connection pooling settings
- Verify network connectivity
- Consider connection limits

**Slow queries?**
- Use EXPLAIN ANALYZE for query plans
- Check if indexes are being used
- Consider query optimization

### Getting Help:
- Supabase Documentation: https://supabase.com/docs
- pgvector Documentation: https://github.com/pgvector/pgvector
- Community Discord: https://discord.supabase.com

## Next Steps

After successful setup:
1. ✅ Database schema applied
2. ✅ Connection test passes
3. ✅ Environment configured
4. ➡️ Move to Backend FastAPI setup (task_1_2)

Your Supabase infrastructure is now ready for Plume & Mimir! 🚀