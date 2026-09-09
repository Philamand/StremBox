-- migrate:up
ALTER TABLE "public"."users" ADD COLUMN "trakt_slug" character varying(255) NULL;

-- migrate:down
ALTER TABLE "public"."users" DROP COLUMN "trakt_slug";
