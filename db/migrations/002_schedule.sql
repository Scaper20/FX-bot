-- Scheduled scans: every 15 minutes, Monday-Friday 05:00-22:59 UTC (the site itself skips
-- times outside London 06:00 - New York 18:00). Replace YOUR-SITE with the Vercel address.
-- The token is read from app_secrets at call time; nobody needs to see or copy it.
create extension if not exists pg_cron;
create extension if not exists pg_net;

select cron.unschedule(jobid) from cron.job where jobname = 'crt-scan';
select cron.schedule(
  'crt-scan',
  '*/15 5-22 * * 1-5',
  $$
  select net.http_post(
    url := 'https://YOUR-SITE.vercel.app/api/cron/scan',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || (select token from public.app_secrets where name = 'cron'),
      'Content-Type', 'application/json'),
    body := '{}'::jsonb,
    timeout_milliseconds := 60000
  );
  $$
);

-- Keep pg_net's response log small.
select cron.unschedule(jobid) from cron.job where jobname = 'crt-net-cleanup';
select cron.schedule('crt-net-cleanup', '17 3 * * *', $$ delete from net._http_response where created < now() - interval '2 days' $$);
