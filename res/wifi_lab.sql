create table if not exists wifi_users (
  "id" integer primary key autoincrement,
  "mac" text NOT NULL,
  "status" text NOT NULL,
  "creation_date" DATETIME DEFAULT (datetime('now', 'localtime')),
  "expiration_date" DATETIME NOT NULL,
  "email" text NOT NULL,
  "device" text,
  "code" text NOT NULL
);
-- status is:  pending | accepted | expired
