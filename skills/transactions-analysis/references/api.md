# Transactions API Reference

## Description
Fetch transaction records for a specific time period.

## How to use?
- **API URL**: `https://example.com/api/v1/transactions/{period}`
- **Method**: `GET`

## Path Parameters
- `period`
  - `yyyy` (e.g. `2025`)
  - `yyyy-mm` (e.g. `2025-12`)

## Example Response
```json
[
  {
    "account_id": 2,
    "amount": "14.00",
    "date": "2025-12-31",
    "desc": "专二",
    "from_account_id": null,
    "id": 11203,
    "item": "咖啡",
    "opposite_trans_id": null,
    "to_account_id": null,
    "type": -1
  },
  {
    "account_id": 1,
    "amount": "34.93",
    "date": "2025-12-31",
    "desc": "都城",
    "from_account_id": null,
    "id": 11204,
    "item": "餐饮",
    "opposite_trans_id": null,
    "to_account_id": null,
    "type": -1
  }
]
