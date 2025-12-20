Current Pricing for GPT-4o-mini:
Input: $0.150 per 1 million tokens
Output: $0.600 per 1 million tokens
Analysis of Input Components:
To calculate tokens, we must include the "overhead" sent to the AI every time:
System Prompt: ~1,800 tokens (Rules, SQL examples, NULL handling instructions)
Semantic JSON: ~1,200 tokens (Your table structure and column definitions)
Column Hints: ~150 tokens (Dynamic suggestions)
Base Overhead: ~3,150 tokens per request.
Scenario 1: Easy Query
"top 5 handler by ytd sales"
Component	Estimated Tokens	Cost (USD)
Input (Prompt + Question)	~3,200 tokens	$0.00048
Output (SQL Generated)	~60 tokens	$0.000036
Total per Query	~3,260 tokens	~$0.000516
In simple terms: You can run about 1,930 of these queries for $1.00.
Scenario 2: Hard Query
"Show me handler code, handler name, customer count, total YTD sales, total outstanding, and total profit/loss grouped by handler code and handler name, replacing nulls with Unknown and No Name, ordered by total YTD sales descending with nulls last"
Component	Estimated Tokens	Cost (USD)

Input (Prompt + Long Question)	~3,350 tokens	$0.000502
Output (Complex SQL)	~250 tokens	$0.000150
Total per Query	~3,600 tokens	~$0.000652

In simple terms: You can run about 1,530 of these queries for $1.00