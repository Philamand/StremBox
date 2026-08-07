-- migrate:up
ALTER TABLE "public"."users"
RENAME COLUMN "torr9_key" TO "tr4ker_key";

-- migrate:down
ALTER TABLE "public"."users"
RENAME COLUMN "tr4ker_key" TO "torr9_key";
