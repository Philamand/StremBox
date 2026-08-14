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
  "transmission_id" INT NULL, "api_key" VARCHAR(255) NULL, "betaseries_id" INT NULL,
  primary key (`id`),
  foreign key (`transmission_id`) references transmission (id) on update cascade on delete cascade
);
CREATE UNIQUE INDEX "users_api_key_index" on "users" ("api_key" ASC);
CREATE TABLE IF NOT EXISTS "files" (
  `id` integer not null primary key autoincrement,
  `created_at` datetime not null default CURRENT_TIMESTAMP,
  `user_id` varchar(255) not null,
  `name` varchar(255) not null,
  `size` INT null,
  unique (`id`),
  foreign key (`user_id`) references users (id) on update cascade on delete cascade
);
CREATE TABLE `torrents` (
  `id` integer not null primary key autoincrement,
  `created_at` datetime not null default CURRENT_TIMESTAMP,
  `user_id` varchar(255) not null,
  `hash` varchar(255) not null,
  `done` BOOLEAN not null default false,
  unique (`id`),
  foreign key (`user_id`) references users (id) on update cascade on delete cascade
);
CREATE TABLE `torrents_files_relation` (
  `id` integer not null primary key autoincrement,
  `torrents_id` INT not null,
  `files_id` INT not null,
  unique (`id`),
  foreign key (`torrents_id`) references torrents (id) on update cascade on delete cascade,
  foreign key (`files_id`) references files (id) on update cascade on delete cascade
);
CREATE TABLE `zip_directory` (
  `id` integer not null primary key autoincrement,
  `created_at` datetime not null default CURRENT_TIMESTAMP,
  `done` BOOLEAN not null default false,
  `path` varchar(255) not null,
  unique (`id`)
);
CREATE TABLE `unzip_directory` (
  `id` integer not null primary key autoincrement,
  `created_at` datetime not null default CURRENT_TIMESTAMP,
  `done` BOOLEAN not null default false,
  `source_path` varchar(255) not null,
  `destination_path` varchar(255) not null,
  unique (`id`)
);
-- Dbmate schema migrations
INSERT INTO "schema_migrations" (version) VALUES
  ('20260510084639'),
  ('20260510084643'),
  ('20260511121423'),
  ('20260512091456'),
  ('20260512091717'),
  ('20260601083102'),
  ('20260814100000');
