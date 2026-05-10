-- migrate:up
CREATE TABLE `transmission` (
  `id` integer not null primary key autoincrement,
  `created_at` datetime not null default CURRENT_TIMESTAMP,
  `port` INT not null,
  `download_folder` varchar(255) not null,
  unique (`id`)
)

-- migrate:down
