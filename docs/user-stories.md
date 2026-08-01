# User Stories

| ID | User Story | Priority | Acceptance Criteria |
|---|---|---|---|
| US-001 | As a resident, I want to view PM2.5 at each station on a map so I know which areas to avoid. | P0 | The map displays at least five markers, each with current PM2.5. |
| US-002 | As a resident, I want to see the latest update time so I know whether data is fresh. | P0 | A popup or card shows the latest timestamp. |
| US-003 | As a resident, I want to view station PM2.5 history so I can understand trends. | P0 | A history API returns time-series data. |
| US-004 | As a manager, I want to know whether sensors are offline so I can check data quality. | P0 | Offline stations have a different status. |
| US-005 | As a manager, I want an alert when PM2.5 exceeds a threshold. | P0 | The system returns active alerts for high PM2.5. |
| US-006 | As a sensitive user, I want stricter recommendations than a normal user. | P1 | Agent responses use the user sensitivity group. |
| US-007 | As a runner, I want to know whether outdoor activity is safe in the next 1-3 hours. | P1 | Agent uses forecast data for recommendations. |
| US-008 | As a manager, I want to approve broad warnings before they are sent. | P1 | Approval requests support pending, approved, and rejected states. |
| US-009 | As a manager, I want to approve simulated device actions before execution. | P1 | Only approved requests publish MQTT commands. |
| US-010 | As a development team, I want audit logs for important actions. | P2 | Important requests and reviews are logged. |
