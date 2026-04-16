CREATE TABLE
  public.users (
    id uuid NOT NULL DEFAULT uuidv7 (),
    created_at timestamp without time zone NOT NULL DEFAULT now(),
    c411_key character varying(255) NULL,
    torr9_key character varying(255) NULL,
    lacale_key character varying(255) NULL,
    qbit_host character varying(255) NOT NULL,
    qbit_port integer NOT NULL,
    qbit_user character varying(255) NOT NULL,
    qbit_pass character varying(255) NOT NULL
  );

ALTER TABLE
  public.users
ADD
  CONSTRAINT users_pkey PRIMARY KEY (id)
