-- migrate:up
CREATE UNIQUE INDEX "users_api_key_index" on "users" ("api_key" ASC);

-- migrate:down
DROP INDEX "users_api_key_index";
