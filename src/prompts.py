import streamlit as st

SCHEMA_PATH = st.secrets.get("SCHEMA_PATH", "PRODUCTION.ANALYTICS")
QUALIFIED_TABLE_NAME = f"{SCHEMA_PATH}.LISTINGS"
TABLE_DESCRIPTION = """
This table contains information about listings on the listings on Ghost.
"""
# This query is optional if running Frosty on your own table, especially a wide table.
# Since this is a deep table, it's useful to tell Frosty what variables are available.
# Similarly, if you have a table with semi-structured data (like JSON), it could be used to provide hints on available keys.
# If altering, you may also need to modify the formatting logic in get_table_context() below.
# METADATA_QUERY = f"SELECT listing_created_at, listing_shared_at, listing_updated_at, listing_id, admin_id, lot_id, seller_id, listing_days_since_created, listing_days_since_posted, listing_days_to_share, listing_image_url, linesheet_url, listing_title, listing_state, listing_category_group_name, listing_internal_notes, listing_long_description, lot_has_release, lot_is_international, lot_internal_notes, lot_city, lot_state, lot_company_restrictions, lot_buyer_type_restrictions, lot_additional_restrictions, admin_name, admin_email, seller_name, seller_email, seller_company_name, seller_is_stealth, listing_minimum_order_quantity, offer_first_date, OFFER_LASTEST_DATE, offer_count_lifetime, offer_avg_price_per_unit_usd, offer_min_price_per_unit_usd, offer_max_price_per_unit_usd, listing_views_lifetime,  listing_favorites_lifetime, listing_total_events_lifetime, listing_unique_buyer_interest_lifetime, listing_buyer_share_count, listing_total_units, listing_item_count, listing_price_usd, listing_msrp_usd, listing_price_per_unit_usd, listing_msrp_per_unit_usd, listing_estimated_percent_off_msrp FROM {SCHEMA_PATH}.listings;"

GEN_SQL = """
You will be acting as an AI SQL Expert named 👻 whose a trained expert on Ghost's data.
Your goal is to give correct, executable sql query to users.
You will be replying to users who will be confused if you don't respond in the character of Frosty.
You are given one table, the table name is in <tableName> tag, the columns are in <columns> tag.
The user will ask questions, for each question you should respond and include a sql query based on the question and the table. 

{context}

Here are 10 critical rules for the interaction you must abide:
<rules>
1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. If I don't tell you to find a limited set of results in the sql query or question, you MUST limit the number of responses to 10.
3  If <columns> is an array data type, use "ARRAY_CONTAINS(lower(<columns>))" to filter down.
4. Text / string where clauses must be fuzzy match e.g ilike %keyword%
5. Make sure to generate a single snowflake sql code, not multiple. 
6. You should only use the table columns given in <columns>, and the table given in <tableName>, you MUST NOT hallucinate about the table names
7. DO NOT put numerical at the very front of sql variable.
8. If prompted with account manager, reference admin_name.
9. If prompted with posted always filter listing_state = 'posted'
10. If given a state name, use the abbreviated Postal version.
</rules>

Don't forget to use "ARRAY_CONTAINS(lower(%keyword%))" for filtering nested columns (especially for lot_company_restrictions, lot_buyer_type_restrictions)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```

For each question from the user, make sure to include a query in your response.

Now to get started, please briefly introduce yourself, describe the table at a high level, and share the available metrics in 2-3 sentences.
Then provide 3 example questions using bullet points.
"""

@st.cache_data(show_spinner="Loading Frosty's context...")
def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
    table = table_name.split(".")
    conn = st.connection("snowflake")
    columns = conn.query(f"""
        SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
        """, show_spinner=False,
    )
    columns = "\n".join(
        [
            f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
            for i in range(len(columns["COLUMN_NAME"]))
        ]
    )
    context = f"""
Here is the table name <tableName> {'.'.join(table)} </tableName>

<tableDescription>{table_description}</tableDescription>

Here are the columns of the {'.'.join(table)}

<columns>\n\n{columns}\n\n</columns>
    """
    if metadata_query:
        metadata = conn.query(metadata_query, show_spinner=False)
        metadata = "\n".join(
            [
                f"- **{metadata['VARIABLE_NAME'][i]}**: {metadata['DEFINITION'][i]}"
                for i in range(len(metadata["VARIABLE_NAME"]))
            ]
        )
        context = context + f"\n\nAvailable variables by VARIABLE_NAME:\n\n{metadata}"
    return context

def get_system_prompt():
    table_context = get_table_context(
        table_name=QUALIFIED_TABLE_NAME,
        table_description=TABLE_DESCRIPTION,
        # metadata_query=METADATA_QUERY
    )
    return GEN_SQL.format(context=table_context)

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("System prompt for Frosty")
    st.markdown(get_system_prompt())
