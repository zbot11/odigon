# Classification prompts for different use cases
PROMPTS = {
    'default': """Search the internet for the company {company_name}, website {website} and determine if the company is a home furnishings manufacturer or not. 

A home furnishings manufacturer must meet ALL of these criteria:
- They must MANUFACTURE (not just retail) furniture
- The furniture must be for HOME/RESIDENTIAL use (not commercial, office, or institutional)
- They must make furniture like sofas, chairs, tables, beds, dressers, or other residential furniture
- They are NOT just cabinetry, casework, mattresses only, or building materials

Examples that should be YES: Albany Industries (upholstery), Intermountain Furniture (residential furniture), Bernhardt Design (home furniture)

Examples that should be NO:
- Kitchen/bathroom cabinet makers (like cabinetry companies)
- Office furniture manufacturers
- Retailers who don't manufacture
- Companies that only make mattresses/box springs
- Glass/building material companies
- Commercial/institutional furniture only

IMPORTANT: Respond with ONLY the single word YES or NO. Do not include any explanation.""",

    'industrial': """Search the internet for the company {company_name}, website {website} and determine if this is an industrial/manufacturing company.
    
Respond with ONLY YES or NO.""",

    'tech': """Search the internet for the company {company_name}, website {website} and determine if this is a technology company.
    
Respond with ONLY YES or NO."""
}