# Design Decisions

## 1. Three important decisions

1. **Separate database facts from policy guidance.** SQL is used for customer, booking, payment, vehicle, and damage records; retrieved document passages are used for rental and refund rules. This reduces the chance of inventing account facts or policy terms.
2. **Read-only database access.** The database is opened in SQLite read-only mode, and the query runner accepts only a single read query. The supplied database must remain unchanged.
3. **Role-aware interface and visible evidence.** The session begins as a customer with a customer ID or as a support agent. The interface shows the SQL query and policy passages used so answers can be checked.

## 2. Alternatives considered and rejected

- A polished React interface was rejected in favor of Streamlit to prioritize working behavior within the three-hour limit.
- Hard-coded answers were rejected because evaluation uses unseen questions.
- A local or third-party LLM was rejected because the event requires the NeoStats-provided model.

## 3. Current limitations

- Policy retrieval uses keyword overlap and may miss relevant passages expressed with different wording.
- The LLM-generated SQL may be invalid or fail to capture a complex question.
- The provided cancellation policy versions may conflict; applicability must be clarified from the source documents.
- Customer SQL scoping is a conservative starter safeguard, not production-grade authorization.
- The implementation assumes an OpenAI-compatible NeoStats endpoint.

## 4. What I would build next with one more week

- Add formal SQL parsing and robust row-level authorization tests.
- Add hybrid/embedding-based policy retrieval and reranking.
- Build a question test suite for both roles, including adversarial privacy tests.
- Add structured citations with document name and page number.
- Improve timeout handling, logging without sensitive data, and API rate-limit handling.
