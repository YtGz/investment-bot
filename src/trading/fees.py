# Note that as soon as the account is flagged as a business account, the fees would be higher.
class FeeCalculator:
    def calculate_sell_fees(self, principal: float, shares: float) -> float:
        # SEC fee calculation ($22.90 per $1M)
        sec_fee = math.ceil(principal * 22.90 / 1_000_000 * 100) / 100
        
        # FINRA TAF calculation ($0.000119 per share, max $5.95)
        finra_fee = min(math.ceil(shares * 0.000119 * 100) / 100, 5.95)
        
        return sec_fee + finra_fee