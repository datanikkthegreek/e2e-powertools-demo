# Genie tool instructions

Add `techsummit.search_product_manuals` as a function/tool in the Bosch Power Tools Genie space, then add this instruction:

> Use `search_product_manuals` for questions about operating a tool, safety, maintenance, troubleshooting, batteries, accessories, or warranty. Pass the user's complete service question. Answer only from returned `manual_text`, name `source_path` as the citation, and say when the search did not provide enough evidence. Continue to use the regular tables for sales, customer, funnel, and numeric specification analysis. For blended questions, query the tables and call the function before synthesizing one answer.

