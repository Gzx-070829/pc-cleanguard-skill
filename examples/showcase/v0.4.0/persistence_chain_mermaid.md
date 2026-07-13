```mermaid
flowchart LR
  app["Example Alpha"] --> startup["Startup updater"]
  app --> service["Service"]
  app --> task["Scheduled task"]
  safety["review-only"] -.-> app
```
