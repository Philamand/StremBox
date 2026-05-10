-- migrate:up
CREATE TABLE `users` (
  `id` VARCHAR(255) not null,
  `created_at` datetime not null default CURRENT_TIMESTAMP,
  "transmission_id" INT NULL,
  primary key (`id`),
  foreign key (`transmission_id`) references transmission (id) on update cascade on delete cascade
)

-- migrate:down
