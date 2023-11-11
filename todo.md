# TODO(Dev Plan)

## Doing

### P1

- [ ] build user system, user identity

- [ ] restore system state from events

- [ ] Deduplicate events

- [ ] enforce correct entity_id for events, currently there is a bug

- [x] refactor code with generic

### P2

- [ ] finish reading [YouTube: Vaughn Vernon: Reactive Domain-Driven Design Made Explicit
](https://www.youtube.com/watch?v=TkKhS3ImbQI)
- [-] ?we might seperate actor events like system_started and system_stoped, and domain events like SessionCreated, ChatMessageSent;

## Done

- [x] Journal and system should not be bounded to each other
Journal Actor should be created independently(done 10/28)

- [x] Debug: python -m src.adapter.cli --interactive --user_id="race" emits user_created event before system_started event.(start 10/29)

- [x] Feat: Catch KeyboardInterrupt event to quit system and publish event to eventlog