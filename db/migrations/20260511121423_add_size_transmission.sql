-- migrate:up
ALTER TABLE "transmission"
ADD COLUMN "size" INT DEFAULT 10000 NOT NULL;

-- migrate:down
ALTER TABLE "transmission"
DROP COLUMN "size";
