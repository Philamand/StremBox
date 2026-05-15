CREATE TABLE IF NOT EXISTS "schema_migrations" (version varchar(128) primary key);
CREATE TABLE `transmission` (
  `id` integer not null primary key autoincrement,
  `created_at` datetime not null default CURRENT_TIMESTAMP,
  `port` INT not null,
  `download_folder` varchar(255) not null, "size" INT DEFAULT 10000 NOT NULL,
  unique (`id`)
);
CREATE TABLE `users` (
  `id` VARCHAR(255) not null,
  `created_at` datetime not null default CURRENT_TIMESTAMP,
  "transmission_id" INT NULL, "api_key" VARCHAR(255) NULL,
  primary key (`id`),
  foreign key (`transmission_id`) references transmission (id) on update cascade on delete cascade
);
CREATE UNIQUE INDEX "users_api_key_index" on "users" ("api_key" ASC);
-- Dbmate schema migrations
INSERT INTO "schema_migrations" (version) VALUES
  ('20260510084639'),
  ('20260510084643'),
  ('20260511121423'),
  ('20260512091456'),
  ('20260512091717');
