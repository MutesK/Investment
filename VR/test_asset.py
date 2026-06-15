import unittest
from Asset import Asset, VRType, BandType, Cycle, TradingTable, PoolLimit

def print_trading_tables(asset: Asset, cycle_index: int = 0):
    if cycle_index >= len(asset.cycles):
        print(f"Cycle index {cycle_index} out of range.")
        return
    cycle = asset.cycles[cycle_index]
    print(f"\n==================================================")
    print(f" Asset: {asset.name} ({asset.ticker}) - Cycle {cycle.cycle_count}")
    print(f" Date: {cycle.start_time} ~ {cycle.end_time}")
    print(f" Current V: {cycle.current_v}, Min Band: {cycle.mininum_band:.2f}, Max Band: {cycle.maximum_band:.2f}")
    print(f" Pool Start: {cycle.pool_start}, Pool End: {cycle.pool_end}")
    print(f"--------------------------------------------------")
    
    print(f" [Buy Trading Table] (Max Buy Budget: {cycle.pool_start * PoolLimit:.2f})")
    if not cycle.buy_trading_tables:
        print("  (Empty)")
    for idx, table in enumerate(cycle.buy_trading_tables, 1):
        print(f"  {idx:02d}. {table.Type.name} -> Target Count: {table.AssetCount}, Price Point: {table.TradingPoint:.2f}, PoolStat: {table.PoolStat}")
        
    print(f" [Sell Trading Table]")
    if not cycle.sell_trading_tables:
        print("  (Empty)")
    for idx, table in enumerate(cycle.sell_trading_tables, 1):
        print(f"  {idx:02d}. {table.Type.name} -> Target Count: {table.AssetCount}, Price Point: {table.TradingPoint:.2f}, PoolStat: {table.PoolStat}")
    print(f"==================================================\n")

class TestAsset(unittest.TestCase):
    def test_asset_initialization(self):
        # Initializing Asset with TQQQ, count=10, and specific start_date (Monday, 2026-06-01)
        asset = Asset("TQQQ", "Nasdaq 3x", 10, 1500, 500, 10000, start_date="2026-06-01")
        
        self.assertEqual(asset.ticker, "TQQQ")
        self.assertEqual(asset.name, "Nasdaq 3x")
        self.assertEqual(asset.count, 10)
        self.assertEqual(asset.type, VRType.ACUMULATION)
        self.assertEqual(asset.extra, 10000)
        
        # Verify the first cycle date range (Monday-based, 2 weeks)
        self.assertEqual(len(asset.cycles), 1)
        cycle1 = asset.cycles[0]
        self.assertEqual(cycle1.cycle_count, 1)
        self.assertEqual(cycle1.start_time, "2026-06-01")
        self.assertEqual(cycle1.end_time, "2026-06-15")
        
        self.assertEqual(cycle1.eval_start, 1500)
        self.assertEqual(cycle1.current_v, 1500)
        self.assertEqual(cycle1.mininum_band, 1500 * 0.85)
        self.assertEqual(cycle1.maximum_band, 1500 * 1.15)
        self.assertEqual(cycle1.pool_start, 500)
        
        # Verify trading tables in first cycle
        self.assertGreater(len(cycle1.buy_trading_tables), 0)
        self.assertGreater(len(cycle1.sell_trading_tables), 0)
        
        # Check PoolStat is computed in buy table
        first_buy = cycle1.buy_trading_tables[0]
        self.assertEqual(first_buy.PoolStat, int(500 - first_buy.TradingPoint))
        
        # Check PoolStat is computed in sell table
        first_sell = cycle1.sell_trading_tables[0]
        self.assertEqual(first_sell.PoolStat, int(500 + cycle1.maximum_band))
        
        # Check that PoolStat increases cumulatively as more shares are sold
        second_sell = cycle1.sell_trading_tables[1]
        self.assertEqual(second_sell.PoolStat, int(500 + cycle1.maximum_band + (cycle1.maximum_band / 2)))
        
        # Print tables for user verification
        print("\n--- Test Asset Initialization (Cycle 1) ---")
        print_trading_tables(asset, 0)

    def test_change_type(self):
        asset = Asset("TQQQ", "Nasdaq 3x", 10, 1500, 500, 100)
        
        # Change type to DEFERRAL (extra should become 0)
        asset.ChangeType(VRType.DEFERRAL, 100)
        self.assertEqual(asset.type, VRType.DEFERRAL)
        self.assertEqual(asset.extra, 0)
        
        # Change type to WITHDRAWAL
        asset.ChangeType(VRType.WITHDRAWAL, 200)
        self.assertEqual(asset.type, VRType.WITHDRAWAL)
        self.assertEqual(asset.extra, 200)

    def test_calculate_cycle(self):
        asset = Asset("TQQQ", "Nasdaq 3x", 10, 1500, 500, 2000, start_date="2026-06-01")
        
        # End first cycle with eval_end = 1450 and calculate next cycle
        asset.CalculrateCycle(eval_end=1450)
        
        self.assertEqual(len(asset.cycles), 2)
        cycle1 = asset.cycles[0]
        cycle2 = asset.cycles[1]
        
        self.assertEqual(cycle1.eval_end, 1450)
        self.assertEqual(cycle2.cycle_count, 2)
        self.assertEqual(cycle2.eval_start, 1450)
        
        # Check that the dates roll forward by 2 weeks (2026-06-15 to 2026-06-29)
        self.assertEqual(cycle2.start_time, "2026-06-15")
        self.assertEqual(cycle2.end_time, "2026-06-29")
        
        # Check that new_cycle pool_start = before_cycle.pool_end (0) + extra (2000)
        self.assertEqual(cycle2.pool_start, 2000)
        
        # Verify bands are updated
        self.assertTrue(cycle2.current_v > 0)
        self.assertEqual(cycle2.mininum_band, cycle2.current_v * 0.85)
        self.assertEqual(cycle2.maximum_band, cycle2.current_v * 1.15)
        
        # Print tables for user verification
        print("\n--- Test Calculate Cycle (Cycle 2) ---")
        print_trading_tables(asset, 1)

    def test_multiple_cycles_simulation(self):
        # Start on 2026-06-01 with TQQQ
        asset = Asset("TQQQ", "Nasdaq 3x", 10, 1500, 1000, 200, start_date="2026-06-01")
        
        # Simulate 5 cycles with fluctuating market closing prices
        market_prices = [1480, 1550, 1620, 1580, 1420]
        # Varying pool_end change factors for each cycle (to simulate buy/sell transactions)
        pool_change_factors = [0.95, 1.15, 0.80, 1.05, 0.90]
        
        print("\n==================================================")
        print(" SIMULATING 5 CONSECUTIVE CYCLES")
        print("==================================================")
        
        for i, price in enumerate(market_prices, 1):
            current_cycle = asset.cycles[-1]
            # Simulate pool_end using varying factors
            factor = pool_change_factors[i - 1]
            current_cycle.pool_end = int(current_cycle.pool_start * factor)
            
            print(f"\n--- Cycle {current_cycle.cycle_count} (End Price: {price}) ---")
            print_trading_tables(asset, len(asset.cycles) - 1)
            
            # Advance to the next cycle
            asset.CalculrateCycle(eval_end=price)
        
        # Print final cycle
        final_cycle = asset.cycles[-1]
        print(f"\n--- Cycle {final_cycle.cycle_count} (Current Active Cycle) ---")
        print_trading_tables(asset, len(asset.cycles) - 1)
        
        self.assertEqual(len(asset.cycles), 6)

    def test_multiple_units_trading(self):
        # Initialize TQQQ with initial count 12, buy_unit=2, sell_unit=3
        asset = Asset("TQQQ", "Nasdaq 3x", 12, 1500, 1000, 200, start_date="2026-06-01", buy_unit=2, sell_unit=3)
        
        self.assertEqual(asset.buy_unit, 2)
        self.assertEqual(asset.sell_unit, 3)
        
        cycle1 = asset.cycles[0]
        
        # Verify buy trading table has steps of 2 (Target Count: 14, 16, 18...)
        for table in cycle1.buy_trading_tables:
            self.assertTrue((table.AssetCount - 12) % 2 == 0)
            
        # Verify sell trading table has steps of 3 (Target Count: 9, 6, 3...)
        for table in cycle1.sell_trading_tables:
            self.assertTrue((12 - table.AssetCount) % 3 == 0)

        # Print tables for user verification
        print("\n==================================================")
        print(" TESTING MULTIPLE UNITS TRADING (Buy Unit: 2, Sell Unit: 3)")
        print("==================================================")
        print_trading_tables(asset, 0)

    def test_empty_guards(self):
        # Test that negative / zero values do not trigger infinite loops or division by zero
        asset_zero_pool = Asset("TQQQ", "Nasdaq 3x", 10, 1500, 0, 0)
        cycle1 = asset_zero_pool.cycles[0]
        # max_usage is 0, so buy_trading_tables should be empty
        self.assertEqual(len(cycle1.buy_trading_tables), 0)
        
        asset_zero_count = Asset("TQQQ", "Nasdaq 3x", 0, 1500, 500, 100)
        # count is 0, so both tables should be empty (also test division by zero guard)
        self.assertEqual(len(asset_zero_count.cycles[0].buy_trading_tables), 0)
        self.assertEqual(len(asset_zero_count.cycles[0].sell_trading_tables), 0)

if __name__ == '__main__':
    unittest.main()
