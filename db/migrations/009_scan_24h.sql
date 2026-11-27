-- 27 Nov 2026: Ore asked for 24-hour scanning on weekdays. pg_cron fires every 15 minutes Sunday-Friday (UTC);
-- the app itself skips when the forex market is closed (engine.calendar.market_open: Sunday 17:00 to Friday 17:00 New York).
select cron.alter_job((select jobid from cron.job where jobname = 'crt-scan'), schedule := '*/15 * * * 0-5');
