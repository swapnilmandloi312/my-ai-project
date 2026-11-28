# Agent acceptance matrix

The Git revision adapter can inspect an immutable commit in a host-selected checkout and store a local evidence receipt. It has no production queue credentials. Production acceptance requires an approved live job, a stored deliverable, a correlated execution event, and a matching private dashboard record.

| Agent category | Implementation | Test evidence | Production execution |
| --- | --- | --- | --- |
| `architecture` | Live GitHub revision adapter | Approved staging job, live GitHub API, persisted result, event and dashboard index | Unverified
| `automation` | Live GitHub revision adapter | Approved staging job, live GitHub API, persisted result, event and dashboard index | Unverified
| `backend` | Live GitHub revision adapter | Approved staging job, live GitHub API, persisted result, event and dashboard index | Unverified
| `ceo` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `competitive_intelligence` | Offline evidence export adapter; live connector pending | Export adapter + synthetic evaluator fixtures | Unverified |
| `compliance` | Offline evidence export adapter; live connector pending | Export adapter + synthetic evaluator fixtures | Unverified |
| `content_strategy` | Offline evidence export adapter; live connector pending | Export adapter + synthetic evaluator fixtures | Unverified |
| `customer_success` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `data_engineering` | Offline evidence export adapter; live connector pending | Export adapter + synthetic evaluator fixtures | Unverified |
| `developer_relations` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `devops` | Live GitHub revision adapter | Approved staging job, live GitHub API, persisted result, event and dashboard index | Unverified
| `engineering` | Live GitHub revision adapter | Approved staging job, live GitHub API, persisted result, event and dashboard index | Unverified
| `finance` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `finance_ops` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `frontend` | Live GitHub revision adapter | Approved staging job, live GitHub API, persisted result, event and dashboard index | Unverified
| `growth` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `hr_ops` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `incident_response` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `integration` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `it_ops` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `knowledge_ops` | Offline evidence export adapter; live connector pending | Export adapter + synthetic evaluator fixtures | Unverified |
| `lead_research` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `legal_ops` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `market_research` | Offline evidence export adapter; live connector pending | Export adapter + synthetic evaluator fixtures | Unverified |
| `marketing_analytics` | Offline evidence export adapter; live connector pending | Export adapter + synthetic evaluator fixtures | Unverified |
| `model_eval` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `observability` | Offline evidence export adapter; live connector pending | Export adapter + synthetic evaluator fixtures | Unverified |
| `partnership` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `privacy` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `procurement` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `product` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `quality` | Live GitHub revision adapter | Approved staging job, live GitHub API, persisted result, event and dashboard index | Unverified
| `recruiting` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `research` | Offline evidence export adapter; live connector pending | Export adapter + synthetic evaluator fixtures | Unverified |
| `sales_ops` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `security` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `seo` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `support_ops` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
| `technical_writing` | Live GitHub revision adapter | Approved staging job, live GitHub API, persisted result, event and dashboard index | Unverified
| `video_production` | Synthetic evaluator; live adapter pending | Synthetic evaluator fixture | Unverified |
