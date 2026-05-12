-- migrate:up
ALTER TABLE "users"
ADD COLUMN "api_key" VARCHAR(255) NULL;

-- migrate:down
ALTER TABLE "users"
DROP COLUMN "api_key";
