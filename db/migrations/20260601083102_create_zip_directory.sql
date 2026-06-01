-- migrate:up
CREATE TABLE `zip_directory` (
  `id` integer not null primary key autoincrement,
  `created_at` datetime not null default CURRENT_TIMESTAMP,
  `done` BOOLEAN not null default false,
  unique (`id`)
);

-- migrate:down
DROP TABLE `zip_directory`;
