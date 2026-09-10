# Integration Check

## Pipeline
`publish → broker/API → backend → database → query`

| Test | Expected | Actual | PASS/FAIL |
|---|---|---|---|
| Edge sends data | Backend receives |  |  |
| Backend validates JSON | Valid record |  |  |
| DB inserts record | 1 new row |  |  |
| API retrieves record | Correct data |  |  |
| Network failure | Graceful handling |  |  |
