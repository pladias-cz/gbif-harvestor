CREATE TABLE IF NOT EXISTS gbif.taxa
(
    id serial NOT NULL,
    gbif_taxon_key integer,
    scientific_name text COLLATE pg_catalog."default" NOT NULL,
    accepted_taxon_key text COLLATE pg_catalog."default" NOT NULL,
    accepted_scientific_name text COLLATE pg_catalog."default" NOT NULL,
    taxon_rank text COLLATE pg_catalog."default" NOT NULL,
    species text COLLATE pg_catalog."default",
    species_key text COLLATE pg_catalog."default",
    pladias_taxon_id integer,
    fsg_taxon_id integer,
    col_id text COLLATE pg_catalog."default",
    note text COLLATE pg_catalog."default",
    CONSTRAINT taxa_pkey PRIMARY KEY (id),
    CONSTRAINT taxa_col_id_key UNIQUE (col_id),
    CONSTRAINT taxa_col_id_key1 UNIQUE (col_id),
    CONSTRAINT taxa_taxon_key_key UNIQUE (gbif_taxon_key),
    CONSTRAINT fsg_taxon_id_fkey FOREIGN KEY (fsg_taxon_id)
    REFERENCES bayernflora.taxons_fsg (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE NO ACTION,
    CONSTRAINT taxa_pladias_taxon_id_fkey FOREIGN KEY (pladias_taxon_id)
    REFERENCES public.taxons (id) MATCH SIMPLE
    ON UPDATE NO ACTION
    ON DELETE CASCADE
    )

    TABLESPACE pg_default;


CREATE TABLE IF NOT EXISTS gbif.records
(
    id bigserial NOT NULL,
    gbif_id bigint NOT NULL,
    locality text COLLATE pg_catalog."default",
    recorded_by text COLLATE pg_catalog."default",
    institution_code text COLLATE pg_catalog."default",
    collection_code text COLLATE pg_catalog."default",
    coords geometry(Point,4326),
    coords_precision integer,
    day integer,
    month integer,
    year integer,
    imported_at timestamp without time zone NOT NULL DEFAULT now(),
    taxon_rank text COLLATE pg_catalog."default" NOT NULL,
    verbatim_scientific_name text COLLATE pg_catalog."default" NOT NULL,
    dataset_key character varying COLLATE pg_catalog."default",
    taxon_col_id text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT gbif_records_pkey PRIMARY KEY (id),
    CONSTRAINT gbif_records_taxon_fkey FOREIGN KEY (taxon_col_id)
    REFERENCES gbif.taxa (col_id) MATCH SIMPLE
                          ON UPDATE NO ACTION
                          ON DELETE CASCADE
    )

    TABLESPACE pg_default;


CREATE UNIQUE INDEX IF NOT EXISTS gbif_records_gbif_id_uidx
    ON gbif.records (gbif_id);

ALTER TABLE gbif.records
    ADD COLUMN IF NOT EXISTS modified timestamp,
    ADD COLUMN IF NOT EXISTS last_interpreted timestamp,
    ADD COLUMN IF NOT EXISTS deleted_at timestamp;

ALTER TABLE gbif.records
    ADD COLUMN IF NOT EXISTS last_seen_snapshot date;


ALTER TABLE gbif.records
ALTER COLUMN coords_precision TYPE double precision
    USING coords_precision::double precision;