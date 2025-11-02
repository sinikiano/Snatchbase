# 💰 Wallet Balance Checker

## Overview

The Snatchbase wallet feature automatically extracts and analyzes cryptocurrency wallets from stealer logs. It can:

- ✅ Parse mnemonics (12/15/18/21/24 word phrases)
- ✅ Extract private keys (hex and WIF formats)
- ✅ Detect wallet addresses (BTC, ETH, Polygon, BSC, Solana)
- ✅ Check real-time balances using blockchain APIs
- ✅ Store and track wallet values in USD
- ✅ Identify wallets with funds

## Features

### Supported Cryptocurrencies

| Coin | Address Detection | Balance Checking | Notes |
|------|------------------|------------------|-------|
| Bitcoin (BTC) | ✅ | ✅ | Legacy (1...) and SegWit (bc1...) |
| Ethereum (ETH) | ✅ | ✅ | ERC-20 compatible |
| Polygon (MATIC) | ✅ | ✅ | Polygon network |
| Binance Smart Chain (BNB) | ✅ | ✅ | BSC network |
| Solana (SOL) | ✅ | 🚧 | Coming soon |

### Wallet File Detection

The parser automatically detects these common wallet file names:

- **Browser Extensions**: `wallet.dat`, `metamask.txt`, `phantom.txt`, `exodus.txt`
- **Mnemonics**: Files containing `seed`, `mnemonic`, `phrase`
- **Bitcoin**: `bitcoin.txt`, `btc.txt`
- **Ethereum**: `ethereum.txt`, `eth.txt`
- **Multi-coin**: Files in `Wallets/` directories

## Usage

### 1. Automatic Processing (ZIP Ingestion)

When you drop a stealer log ZIP file into the ingestion folder, wallets are automatically:

1. **Extracted** from wallet files
2. **Parsed** for mnemonics, private keys, addresses
3. **Stored** in database with hashed sensitive data
4. **Ready** for balance checking

```bash
# Drop your ZIP file here:
backend/data/incoming/uploads/stealer_log.zip

# Wallets are automatically extracted during processing
```

### 2. API Endpoints

#### Get Device Wallets
```bash
GET /api/devices/{device_id}/wallets
```

**Query Parameters:**
- `wallet_type` - Filter by BTC, ETH, MATIC, etc.
- `has_balance` - Filter wallets with/without balance

**Example:**
```bash
curl "http://localhost:8000/api/devices/123/wallets?has_balance=true"
```

#### Search All Wallets
```bash
GET /api/wallets?wallet_type=BTC&has_balance=true&limit=100
```

#### Check Wallet Balances
```bash
POST /api/wallets/check-balance
Content-Type: application/json

{
  "device_id": 123  # Check all wallets for this device
}

# Or specific wallets
{
  "wallet_ids": [1, 2, 3, 4, 5]
}
```

#### Wallet Statistics
```bash
GET /api/stats/wallets
```

**Response:**
```json
{
  "total_wallets": 1523,
  "wallets_with_balance": 47,
  "total_value_usd": 12845.67,
  "breakdown_by_type": {
    "BTC": {
      "count": 234,
      "total_usd": 8500.00
    },
    "ETH": {
      "count": 892,
      "total_usd": 3200.50
    }
  },
  "top_wallets": [...]
}
```

### 3. Direct Balance Checking (CLI)

```bash
# Check a single Bitcoin address
cd backend
source venv/bin/activate
python app/services/wallet_balance_checker.py BTC 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa

# Check an Ethereum address
python app/services/wallet_balance_checker.py ETH 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

**Output:**
```
💰 Balance for 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa:
   Type: BTC
   Balance: 71.00543210 BTC
   USD Value: $4,235,678.90
```

### 4. Testing

Run the comprehensive test suite:

```bash
cd backend
source venv/bin/activate
python test_wallet_features.py
```

This will:
- Test wallet parsing for different formats
- (Optionally) Check real blockchain balances
- Show integration status

## Database Schema

### Wallets Table

```sql
CREATE TABLE wallets (
    id SERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES devices(id),
    wallet_type VARCHAR(50),           -- BTC, ETH, etc.
    address VARCHAR(255),               -- Wallet address
    mnemonic_hash VARCHAR(64),          -- SHA256 hash of mnemonic
    private_key_hash VARCHAR(64),       -- SHA256 hash of private key
    password TEXT,                      -- Wallet password (if any)
    path TEXT,                          -- File path where found
    source_file VARCHAR(500),           -- Wallet file name
    balance NUMERIC(36, 18),            -- Balance in native currency
    balance_usd NUMERIC(20, 2),         -- Balance in USD
    has_balance BOOLEAN DEFAULT FALSE,  -- Quick filter flag
    last_checked TIMESTAMP,             -- Last balance check time
    token_balances TEXT,                -- JSON of token balances
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_wallet_address ON wallets(address);
CREATE INDEX idx_wallet_type ON wallets(wallet_type);
CREATE INDEX idx_has_balance ON wallets(has_balance);
CREATE INDEX idx_device_wallet ON wallets(device_id, wallet_type);
```

**Security Notes:**
- ⚠️ Mnemonics and private keys are **hashed** with SHA256
- ⚠️ Never store plaintext private keys or mnemonics
- ⚠️ Hashes allow deduplication without exposing sensitive data

## Architecture

### Wallet Parser (`wallet_parser.py`)

Extracts wallet information from text files using:

1. **Pattern Matching** - Regex for addresses, keys, mnemonics
2. **Structured Parsing** - Key-value format detection
3. **File Type Detection** - Common wallet file names
4. **Validation** - Mnemonic word count, address formats

### Balance Checker (`wallet_balance_checker.py`)

Queries blockchain APIs to get real-time balances:

1. **Async Requests** - Concurrent balance checking
2. **Caching** - 5-minute TTL to reduce API calls
3. **Fallback APIs** - Multiple sources per chain
4. **Rate Limiting** - Respects API limits

**API Sources:**
- **Bitcoin**: blockchain.info, blockchair.com, blockcypher.com
- **Ethereum**: etherscan.io, blockchair.com
- **Polygon**: polygonscan.com
- **BSC**: bscscan.com

### ZIP Ingestion Integration

Wallets are automatically processed during ZIP ingestion:

```python
# From zip_ingestion.py

# 1. Detect wallet files
wallet_files = [f for f in files if parser.is_wallet_file(f.name)]

# 2. Parse wallet data
wallets = parser.parse_wallet_file(content, filename)

# 3. Hash sensitive data
mnemonic_hash = sha256(wallet.mnemonic).hexdigest()

# 4. Store in database
db.add(Wallet(...))
```

## Configuration

No configuration needed! The system uses:

- ✅ **Public blockchain APIs** (no API keys required)
- ✅ **Free tier limits** respected with caching
- ✅ **Fallback sources** if primary API fails

## Rate Limits

| API | Rate Limit | Fallback |
|-----|-----------|----------|
| blockchain.info | ~1 req/sec | blockchair |
| etherscan.io | ~5 req/sec | blockchair |
| polygonscan | ~5 req/sec | None |
| bscscan | ~5 req/sec | None |

**Recommendations:**
- Check balances in batches of 10-20
- Use the cache (5 min TTL)
- Schedule bulk checks during off-peak hours

## Examples

### Example 1: Find All Bitcoin Wallets with Balance

```bash
curl "http://localhost:8000/api/wallets?wallet_type=BTC&has_balance=true"
```

### Example 2: Get Total Wallet Value

```bash
curl "http://localhost:8000/api/stats/wallets" | jq '.total_value_usd'
```

### Example 3: Check Balances for New Device

```python
import asyncio
from app.services.wallet_balance_checker import check_wallet_balances
from app.database import SessionLocal

async def check_device_wallets(device_id: int):
    db = SessionLocal()
    wallets = db.query(Wallet).filter(Wallet.device_id == device_id).all()
    
    wallet_infos = [WalletInfo(wallet_type=w.wallet_type, address=w.address) 
                    for w in wallets if w.address]
    
    balances = await check_wallet_balances(wallet_infos)
    
    for addr, balance in balances.items():
        wallet = db.query(Wallet).filter(Wallet.address == addr).first()
        wallet.balance = balance.balance
        wallet.balance_usd = balance.balance_usd
        wallet.has_balance = balance.balance > 0
        wallet.last_checked = datetime.utcnow()
    
    db.commit()
    print(f"✅ Updated {len(balances)} wallet balances")

asyncio.run(check_device_wallets(123))
```

## Troubleshooting

### Balance Checks Failing

**Problem**: API returns errors or timeouts

**Solutions:**
1. Check internet connectivity
2. Wait 60 seconds (rate limit cooldown)
3. Verify address format is correct
4. Try a different wallet type

### Wallets Not Detected

**Problem**: ZIP processing doesn't find wallets

**Solutions:**
1. Check file names match patterns (see "Wallet File Detection")
2. Verify wallet files contain addresses/mnemonics
3. Check backend logs for parsing errors
4. Test parser directly: `python app/services/wallet_parser.py`

### Database Errors

**Problem**: "column does not exist: wallets"

**Solutions:**
```bash
# Run migration to create table
cd backend
source venv/bin/activate
python -c "from app.database import engine; from app.models import Wallet; Wallet.__table__.create(engine)"
```

## Future Enhancements

- 🚧 Solana balance checking
- 🚧 Token balance detection (ERC-20, BEP-20)
- 🚧 NFT detection and valuation
- 🚧 Historical price tracking
- 🚧 Wallet clustering (same owner detection)
- 🚧 Automatic mnemonic-to-address derivation
- 🚧 Support for more chains (Cardano, Polkadot, etc.)

## Security Considerations

1. **Never log plaintext mnemonics/private keys**
2. **Store only hashes** for deduplication
3. **Limit API exposure** - require authentication in production
4. **Encrypt database** - wallets contain valuable information
5. **Audit access** - track who views wallet data
6. **Rate limit checks** - prevent API abuse

## License

Part of Snatchbase - see main repository for license details.
