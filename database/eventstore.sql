CREATE TABLE
    IF NOT EXISTS domain_events (
        id varchar(256) NOT NULL,
        event_type varchar(128),
        event_body JSONB NOT NULL,
        aggregate_id varchar(128) NOT NULL,
        status varchar(64) NOT NULL,
        version int NOT NULL,
        gmt_create timestamp,
        gmt_modified timestamp,
        constraint domain_event_store_pkey primary key (id)
    );

-- Add a composite primary key constraint
CREATE UNIQUE INDEX PK_DomainEventEntry ON domain_events (aggregate_id, id);

-- Trigger to set gmt_create to the current timestamp on INSERT
CREATE TRIGGER set_gmt_create AFTER INSERT ON domain_events BEGIN
UPDATE domain_events
SET
    gmt_create = DATETIME ('now')
WHERE
    id = NEW.id;

END;

-- Trigger to set gmt_modified to the current timestamp on UPDATE
CREATE TRIGGER set_gmt_modified AFTER
UPDATE ON domain_events BEGIN
UPDATE domain_events
SET
    gmt_modified = DATETIME ('now')
WHERE
    id = NEW.id;

END;