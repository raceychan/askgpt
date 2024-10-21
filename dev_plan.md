# Dev Plan

## 10-15

### FRONTEND

- [x] use microsoft/fetch-event-source to replace axios for chat api call

- [ ] let child component use parent component's error message

### BACKEND

- [ ] rewrite gpt service, deprecate gpt system, remove all actor-related code

- [x] rewrite outbox publisher, perhaps we should use eventstore directly?, just let eventstore uses uow.

- [x] deprecate event listener.
