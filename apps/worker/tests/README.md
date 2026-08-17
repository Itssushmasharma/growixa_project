# Worker Test Layout

Worker tests are grouped by the job or runtime area they exercise:

- `core/` - generic consumer parsing and healthcheck handler behavior.
- `dispatch/` - campaign dispatch queue consumption.
- `email/` - email sending and campaign send jobs.
- `social/` - social post publishing and dispatch consumption.
