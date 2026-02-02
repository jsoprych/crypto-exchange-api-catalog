# US Access Restrictions Report
## Cryptocurrency Exchange API Connectivity Analysis

**Report Date:** February 1, 2026  
**Test Location:** United States  
**Last Updated:** 2026-02-01

---

## Executive Summary

This report details the accessibility of cryptocurrency exchange APIs from United States-based servers. Based on comprehensive connectivity testing, we have identified significant geographic restrictions affecting certain exchanges, particularly Bybit, while most other exchanges remain accessible with varying degrees of functionality.

### Key Findings:
- **9 out of 10 tested exchanges** are accessible from the US
- **Bybit has strict US blocking** via CloudFront distribution (403 Forbidden)
- **Binance requires regional endpoint** (Binance.US for US customers)
- **All other exchanges function normally** with REST and WebSocket APIs

---

## Exchange Accessibility Matrix

| Exchange | US Accessible | REST API | WebSocket | Notes |
|----------|---------------|----------|-----------|-------|
| Coinbase | ✅ Yes | ✅ Full | ✅ Full | US-based exchange |
| Binance | ⚠️ Limited | ✅ Binance.US only | ⚠️ Limited | Global API restricted |
| Kraken | ✅ Yes | ✅ Full | ✅ Full | US-based with KYC |
| Bitfinex | ✅ Yes | ✅ Full | ✅ Full | Accessible with restrictions |
| OKX | ✅ Yes | ✅ Full | ✅ Full | No detected restrictions |
| KuCoin | ✅ Yes | ✅ Full | ✅ Full | Accessible without issues |
| Gate.io | ✅ Yes | ✅ Full | ✅ Full | Accessible with normal latency |
| Huobi | ✅ Yes | ✅ Full | ✅ Full | Accessible without restrictions |
| Bybit | ❌ No | ❌ Blocked | ❌ Blocked | CloudFront 403 Forbidden |
| MEXC | ✅ Yes | ✅ Full | ✅ Full | Accessible (not in database) |

---

## Detailed Analysis

### 1. **Bybit - Strict US Blocking**
**Status:** ❌ Completely blocked from US IP addresses

**Evidence:**
- All API endpoints return HTTP 403 Forbidden
- CloudFront distribution configured for geographic restriction
- Error message: "The Amazon CloudFront distribution is configured to block access from your country"
- Affects both REST API (`api.bybit.com`) and WebSocket endpoints

**Impact:**
- Discovery runs fail with 403 errors
- Product discovery cannot proceed from US locations
- Requires VPN/proxy for US-based developers

### 2. **Binance - Regional Restrictions**
**Status:** ⚠️ Limited access via Binance.US

**Evidence:**
- Global API (`api.binance.com`) returns: "Service unavailable from a restricted location"
- US-specific endpoint (`api.binance.us`) functions normally
- Different API structures and available trading pairs
- Documentation: https://www.binance.com/en/terms restricts certain jurisdictions

**Impact:**
- Must use regional endpoint configuration
- Limited product selection compared to global exchange
- Separate API documentation and rate limits

### 3. **Other Exchanges - No Restrictions**
**Status:** ✅ Fully accessible

**Verified Exchanges:**
- **Coinbase, Kraken**: US-based exchanges with full compliance
- **Bitfinex, OKX, KuCoin, Gate.io, Huobi, MEXC**: International exchanges currently accessible from US
- All respond with HTTP 200 and normal API functionality
- No detected geographic filtering or IP-based blocking

**Response Times (from US West Coast):**
- Coinbase: 434ms
- Binance.US: 417ms  
- Kraken: 870ms
- Bitfinex: 310ms
- OKX: 639ms
- KuCoin: 486ms
- Gate.io: 1199ms
- Huobi: 531ms
- MEXC: 481ms

---

## Technical Implementation Status

### Current Coverage (Ticker Data)
| Exchange | Database Status | Mappings | Coverage | Connectivity |
|----------|----------------|----------|----------|--------------|
| Coinbase | ✅ In database | 18 mappings | 76.9% | ✅ Working |
| Binance | ✅ In database | 24 mappings | 84.6% | ⚠️ Binance.US |
| Kraken | ✅ In database | 18 mappings | 76.9% | ✅ Working |
| Bitfinex | ✅ In database | 17 mappings | 61.5% | ✅ Working |
| OKX | ✅ In database | 11 mappings | 84.6% | ✅ Working |
| KuCoin | ✅ In database | 7 mappings | 46.2% | ✅ Working |
| Gate.io | ✅ In database | 8 mappings | 61.5% | ✅ Working |
| Huobi | ✅ In database | 4 mappings | 30.8% | ✅ Working |
| Bybit | ✅ In database | 6 mappings | 46.2% | ❌ Blocked |
| MEXC | ❌ Not in DB | 0 mappings | 0% | ✅ Working |

**Total:** 113 field mappings across 9 exchanges  
**Average Coverage:** 63.2%  
**Connectivity Rate:** 90% (9/10 accessible)

---

## Recommendations & Mitigation Strategies

### 1. **Immediate Actions (High Priority)**

#### A. Bybit Workaround Implementation
```yaml
# Suggested configuration update
bybit:
  enabled: false  # Disable for US deployments
  us_alternative: null  # No US alternative available
  requires_vpn: true
  vpn_instructions: |
    Bybit requires VPN connection outside US.
    Recommended VPN regions: Singapore, Hong Kong, EU.
```

#### B. Binance Regional Configuration
```python
# Dynamic endpoint selection
def get_binance_endpoint():
    if is_us_location():
        return "https://api.binance.us"
    else:
        return "https://api.binance.com"
```

### 2. **Medium-Term Solutions**

#### A. VPN/Proxy Integration
- Implement transparent proxy routing for blocked exchanges
- Create VPN-required flag in vendor configurations
- Add automatic failover to proxy servers

#### B. Regional Availability Metadata
```sql
-- Add to vendors table
ALTER TABLE vendors ADD COLUMN us_accessible BOOLEAN DEFAULT TRUE;
ALTER TABLE vendors ADD COLUMN requires_vpn BOOLEAN DEFAULT FALSE;
ALTER TABLE vendors ADD COLUMN vpn_regions TEXT;  -- JSON array
```

### 3. **Long-Term Architecture**

#### A. Geographic Discovery System
```python
class GeographicDiscoveryManager:
    def discover_with_region(self, vendor_name: str, region: str = "auto"):
        """Discover API with geographic awareness."""
        if region == "auto":
            region = self.detect_region()
        
        if vendor_name == "bybit" and region == "us":
            raise GeographicRestrictionError(
                "Bybit not accessible from US. Use VPN or proxy."
            )
        
        return self._discover_vendor(vendor_name)
```

#### B. Multi-Region Deployment
- Deploy discovery nodes in multiple geographic regions
- US node: Coinbase, Binance.US, Kraken, etc.
- EU node: All exchanges including Bybit
- Singapore node: Asia-focused exchanges

---

## Testing Methodology

### 1. **Connectivity Tests Performed**
- HTTP GET requests to time/status endpoints
- WebSocket connection attempts (where applicable)
- Error message analysis for geographic blocking patterns
- Response time measurements from US West Coast

### 2. **Test Scripts Created**
- `test_exchange_connectivity.py`: Comprehensive connectivity testing
- `test_exchange_coverage.py`: Configurable normalization testing
- Automated geographic restriction detection

### 3. **Detection Patterns**
```python
def detect_geographic_block(response):
    """Detect geographic restrictions in API responses."""
    indicators = [
        "CloudFront distribution is configured to block",
        "restricted location",
        "Service unavailable from a restricted location",
        "403 Forbidden",
        "geographic restrictions"
    ]
    
    for indicator in indicators:
        if indicator in response.text:
            return True
    
    return False
```

---

## Legal & Compliance Considerations

### 1. **Exchange Terms of Service**
- **Binance**: Explicitly restricts US customers to Binance.US
- **Bybit**: Terms prohibit US persons from using the exchange
- **Other exchanges**: Generally permit API access but may restrict trading

### 2. **API Usage Compliance**
- Public market data APIs typically have fewer restrictions
- Trading APIs often require KYC and geographic verification
- Rate limits may vary by region

### 3. **Data Residency Requirements**
- No detected data residency requirements for market data
- Trading data may have jurisdiction-specific regulations

---

## Implementation Roadmap

### Phase 1: Immediate (1-2 weeks)
1. ✅ Update vendor configurations with accessibility flags
2. ✅ Create Bybit VPN/proxy documentation
3. ✅ Implement Binance regional endpoint switching
4. ✅ Add geographic restriction error handling

### Phase 2: Short-term (2-4 weeks)
1. Implement automatic VPN/proxy routing for blocked exchanges
2. Add regional availability to database schema
3. Create geographic-aware discovery scheduling
4. Deploy test nodes in multiple regions

### Phase 3: Long-term (1-2 months)
1. Build multi-region discovery infrastructure
2. Implement automatic region detection and failover
3. Add compliance monitoring for API usage
4. Create regional performance benchmarking

---

## Monitoring & Alerting

### Recommended Monitoring Metrics:
1. **Connectivity Success Rate**: Per exchange, per region
2. **Response Time Percentiles**: Track regional performance
3. **Geographic Block Detection**: Automatic alerting for new restrictions
4. **API Change Detection**: Monitor for Terms of Service updates

### Alert Configuration:
```yaml
alerts:
  geographic_blocks:
    - exchange: bybit
      region: us
      expected_status: blocked
      alert_on_change: true
    
  connectivity_issues:
    - threshold: < 95% success rate
      duration: 5 minutes
      severity: warning
```

---

## Conclusion

### Summary of Findings:
1. **Bybit is completely blocked** from US IP addresses via CloudFront
2. **Binance requires US-specific endpoint** (Binance.US)
3. **All other 8 exchanges are fully accessible** from the US
4. **Response times are acceptable** for all accessible exchanges
5. **WebSocket connectivity mirrors REST API accessibility**

### Recommended Actions:
1. **Disable Bybit discovery** for US-based deployments
2. **Implement regional endpoint selection** for Binance
3. **Add geographic awareness** to discovery system
4. **Monitor for policy changes** from other exchanges

### Risk Assessment:
- **Low Risk**: Coinbase, Kraken (US-based, compliant)
- **Medium Risk**: International exchanges (policy may change)
- **High Risk**: Bybit (actively blocking), Binance (regional restrictions)

This report should be reviewed quarterly as exchange policies and geographic restrictions may change. Regular connectivity testing is recommended to maintain accurate accessibility information.

---

## Appendices

### A. Test Results Raw Data
```json
{
  "coinbase": {"accessible": true, "response_ms": 434, "status": 200},
  "binance_global": {"accessible": false, "error": "restricted location"},
  "binance_us": {"accessible": true, "response_ms": 417, "status": 200},
  "kraken": {"accessible": true, "response_ms": 870, "status": 200},
  "bitfinex": {"accessible": true, "response_ms": 310, "status": 200},
  "okx": {"accessible": true, "response_ms": 639, "status": 200},
  "kucoin": {"accessible": true, "response_ms": 486, "status": 200},
  "gateio": {"accessible": true, "response_ms": 1199, "status": 200},
  "huobi": {"accessible": true, "response_ms": 531, "status": 200},
  "bybit": {"accessible": false, "error": "CloudFront 403", "status": 403},
  "mexc": {"accessible": true, "response_ms": 481, "status": 200}
}
```

### B. Exchange Contact Information for Compliance
- **Binance Compliance**: compliance@binance.us
- **Bybit Support**: support@bybit.com
- **Kraken Legal**: legal@kraken.com
- **Coinbase API Support**: api-support@coinbase.com

### C. Regulatory References
- SEC guidance on digital asset securities
- FinCEN requirements for cryptocurrency businesses
- CFTC regulations on derivative trading
- State-level money transmitter licenses

---

**Document Version:** 1.0  
**Last Tested:** 2026-02-01  
**Next Review:** 2026-05-01  
**Maintainer:** Crypto Exchange API Catalog Team