# TODO(Dev Plan)

## Doing

### P1

- [ ] call AI agents from APIs

## Done

- [x] README.md

- [x] deprive the AI agents part and make it a standalone project

- [x] Required OPENAI_API_KEY for user to use this system

- [x] build user system, user identity

- [x] restore system state from events

- [x] Deduplicate events

- [x] enforce correct entity_id for events, currently there is a bug

- [x] refactor code with generic

- [x] Journal and system should not be bounded to each other
Journal Actor should be created independently(done 10/28)

- [x] Debug: python -m src.adapter.cli --interactive --user_id="race" emits user_created event before system_started event.(start 10/29)

- [x] Feat: Catch KeyboardInterrupt event to quit system and publish event to eventlog