"""Quick test to find related stocks for ORCL"""

from find_related_stocks import RelatedStocksFinder

# Initialize finder
finder = RelatedStocksFinder()

# Find related stocks for ORCL
print("\n" + "="*60)
print("Finding Related Stocks for ORCL (Oracle Corporation)")
print("="*60 + "\n")

# Get related tickers with details
finder.print_related_stocks('ORCL', show_details=True)
