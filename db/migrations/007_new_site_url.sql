-- Site moved to a new Vercel account: https://fx-bot-vert.vercel.app (was fxbot-ochre.vercel.app).
-- Re-points the two scheduled jobs. Applied to the live project on 25 Nov 2026.
select cron.unschedule(jobid) from cron.job where jobname in ('crt-scan', 'crt-reminders');

select cron.schedule(
  'crt-scan',
  '*/15 5-22 * * 1-5',
  $$
  select net.http_post(
    url := 'https://fx-bot-vert.vercel.app/api/cron/scan',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || (select token from public.app_secrets where name = 'cron'),
      'Content-Type', 'application/json'),
    body := '{}'::jsonb,
    timeout_milliseconds := 60000
  );
  $$
);

select cron.schedule(
  'crt-reminders',
  '7 8 * * *',
  $$
  select net.http_post(
    url := 'https://fx-bot-vert.vercel.app/api/cron/reminders',
    headers := jsonb_build_object(
      'Authorization', 'Bearer ' || (select token from public.app_secrets where name = 'cron'),
      'Content-Type', 'application/json'),
    body := '{}'::jsonb,
    timeout_milliseconds := 60000
  );
  $$
);
