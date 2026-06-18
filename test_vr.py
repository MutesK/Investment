from InvestmentHub.services.vr_engine import VREngine

# Mock data
current_shares = 100
pool = 5000000
current_v = 15000000 # 15M KRW
band_ratio = 0.15
pool_limit = 0.75

print("Testing VR Engine Trading Table Generation...")
table = VREngine.get_trading_table(current_shares, pool, current_v, band_ratio, pool_limit)

print("\nBuy Points (First 3):")
for p in table['buy'][:3]:
    print(f"  Price: {p['price']}, Shares: {p['shares']}, Pool Left: {p['pool_left']}")

print("\nSell Points (First 3):")
for p in table['sell'][:3]:
    print(f"  Price: {p['price']}, Shares: {p['shares']}, Pool Left: {p['pool_left']}")

# Test V calculation
v_before = 10000000
pool_end = 2000000
g = 10
eval_end = 11000000
extra = 500000

next_v = VREngine.calculate_next_v(v_before, pool_end, g, eval_end, extra)
print(f"\nNext V Calculation: {next_v}")
