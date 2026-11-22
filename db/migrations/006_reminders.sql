-- Practice reminders: remember when each trader was last reminded, and run the reminder job daily
-- at 08:07 UTC (09:07 Lagos), every day including weekends. The token is read from app_secrets
-- at call time, as in 002.
alter table community_users add column if not exists last_reminded_at timestamptz;

select cron.unschedule(jobid) from cron.job where jobname = 'crt-reminders';
select cron.schedule(
  'crt-reminders',
  '7 8 * * *',
  $$
  select net.http_post(
    url := 'https://fxbot-ochre.vercel.app/api/cron/reminders',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || (select token from public.app_secrets where name = 'cron'),
      'Content-Type', 'application/json'),
    body := '{}'::jsonb,
    timeout_milliseconds := 60000
  );
  $$
);
