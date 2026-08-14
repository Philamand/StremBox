-- migrate:up
CREATE TABLE `unzip_directory` (
  `id` integer not null primary key autoincrement,
  `created_at` datetime not null default CURRENT_TIMESTAMP,
  `done` BOOLEAN not null default false,
  `source_path` varchar(255) not null,
  `destination_path` varchar(255) not null,
  unique (`id`)
);

-- migrate:down
DROP TABLE `unzip_directory`;
