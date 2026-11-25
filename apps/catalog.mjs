/* Generated from reviewed catalog and local utility definitions. */
export const catalog = {
  "brand": "Swapnil AI Labs",
  "industries": [
    {
      "id": "everyday",
      "name": "Everyday life"
    },
    {
      "id": "education",
      "name": "Education"
    },
    {
      "id": "healthcare",
      "name": "Healthcare"
    },
    {
      "id": "finance",
      "name": "Finance and accounting"
    },
    {
      "id": "agriculture",
      "name": "Agriculture"
    },
    {
      "id": "retail",
      "name": "Retail and e-commerce"
    },
    {
      "id": "manufacturing",
      "name": "Manufacturing"
    },
    {
      "id": "logistics",
      "name": "Logistics"
    },
    {
      "id": "legal",
      "name": "Legal"
    },
    {
      "id": "government",
      "name": "Public services"
    },
    {
      "id": "hospitality",
      "name": "Hospitality"
    },
    {
      "id": "real_estate",
      "name": "Real estate"
    },
    {
      "id": "hr",
      "name": "HR and careers"
    },
    {
      "id": "media",
      "name": "Media and creators"
    },
    {
      "id": "nonprofit",
      "name": "Nonprofits"
    },
    {
      "id": "energy",
      "name": "Energy and environment"
    },
    {
      "id": "construction",
      "name": "Construction"
    },
    {
      "id": "research",
      "name": "Research and science"
    },
    {
      "id": "software",
      "name": "Software and AI"
    },
    {
      "id": "small_business",
      "name": "Small businesses"
    },
    {
      "id": "accessibility",
      "name": "Accessibility"
    },
    {
      "id": "transport",
      "name": "Transport"
    },
    {
      "id": "insurance",
      "name": "Insurance"
    },
    {
      "id": "cybersecurity",
      "name": "Cybersecurity"
    }
  ],
  "tools": [
    {
      "id": "everyday-1",
      "industry": "everyday",
      "title": "Personal planning",
      "risk": "low",
      "mode": "plan",
      "inputLabel": "List activities, one per line",
      "example": "Buy groceries\nStudy for 45 minutes\nCall family",
      "options": [
        "Prioritize urgent items|Allocate time blocks|Check completed tasks"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "everyday-2",
      "industry": "everyday",
      "title": "Document simplification",
      "risk": "low",
      "mode": "read",
      "inputLabel": "Paste a document you want to review",
      "example": "Your subscription renews on 1 December. Cancel before renewal to avoid the next charge.",
      "options": [
        "Review the original; extracted sentences are not an AI paraphrase."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "everyday-3",
      "industry": "everyday",
      "title": "Budget education",
      "risk": "low",
      "mode": "budget",
      "inputLabel": "Income and expenses as label,amount",
      "example": "Salary,35000\nRent,12000\nFood,5000",
      "options": [
        "First row is income; remaining rows are expenses. Use one currency."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "education-1",
      "industry": "education",
      "title": "Study practice",
      "risk": "medium",
      "mode": "quiz",
      "inputLabel": "Enter your own question|answer pairs, one per line",
      "example": "What is 2 + 2?|4\nWhat is the capital of India?|New Delhi",
      "options": [
        "Practice only with supplied answers; verify facts."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "education-2",
      "industry": "education",
      "title": "Lesson plans",
      "risk": "medium",
      "mode": "draft",
      "inputLabel": "Enter subject, learner level, objective and duration on separate lines",
      "example": "Fractions\nGrade 5\nCompare simple fractions\n40 minutes",
      "options": [
        "Subject|Learner level|Learning objective|Duration",
        "Opening activity|Worked example|Independent practice|Assessment"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "education-3",
      "industry": "education",
      "title": "Language learning",
      "risk": "medium",
      "mode": "quiz",
      "inputLabel": "Enter word|translation pairs",
      "example": "Hello|नमस्ते\nWater|पानी",
      "options": [
        "Review translations with a fluent speaker."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "healthcare-1",
      "industry": "healthcare",
      "title": "Appointment preparation",
      "risk": "high",
      "mode": "draft",
      "inputLabel": "Enter appointment purpose, symptom notes and questions (avoid identifiers)",
      "example": "Routine follow-up\nQuestions about sleep\nWhat should I bring?",
      "options": [
        "Purpose|Notes to discuss|Questions",
        "Confirm appointment details|Bring relevant documents|Discuss concerns with clinician"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "healthcare-2",
      "industry": "healthcare",
      "title": "Medical terminology",
      "risk": "high",
      "mode": "lookup",
      "inputLabel": "Paste glossary entries, then search a term",
      "example": "CBC: complete blood count\nBP: blood pressure",
      "options": [
        "CBC",
        "Supplied glossary only; not medical advice."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "healthcare-3",
      "industry": "healthcare",
      "title": "Administrative workflows",
      "risk": "high",
      "mode": "check",
      "inputLabel": "Enter completed administrative tasks, one per line",
      "example": "Confirm appointment\nConfirm contact preference",
      "options": [
        "Confirm appointment|Confirm contact preference|Check required documents|Verify consent",
        "Administrative only; do not enter patient identifiers."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "finance-1",
      "industry": "finance",
      "title": "Invoice review",
      "risk": "high",
      "mode": "sum",
      "inputLabel": "Enter invoice ID,amount (same currency)",
      "example": "INV-001,125.00\nINV-002,75.00",
      "options": [
        "Invoice total",
        "Review source invoice and approvals; no payment is made."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "finance-2",
      "industry": "finance",
      "title": "Expense categorization",
      "risk": "high",
      "mode": "group",
      "inputLabel": "Enter category,amount (same currency)",
      "example": "Travel,250\nOffice,100\nTravel,50",
      "options": [
        "Expense totals by supplied category",
        "No automatic accounting classification; verify categories."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "finance-3",
      "industry": "finance",
      "title": "Financial literacy",
      "risk": "high",
      "mode": "budget",
      "inputLabel": "Income first, then expenses as label,amount",
      "example": "Income,1000\nRent,400\nFood,200",
      "options": [
        "Educational cash-flow arithmetic, not investment advice."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "agriculture-1",
      "industry": "agriculture",
      "title": "Crop knowledge lookup",
      "risk": "medium",
      "mode": "lookup",
      "inputLabel": "Paste trusted crop-reference notes, then search",
      "example": "Wheat: check local agricultural extension advice for sowing dates.\nRice: consult locally validated water guidance.",
      "options": [
        "wheat",
        "Use verified local sources; no pesticide or treatment recommendations."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "agriculture-2",
      "industry": "agriculture",
      "title": "Market information",
      "risk": "medium",
      "mode": "compare",
      "inputLabel": "Enter market,price (same unit and currency)",
      "example": "Market A,22\nMarket B,25",
      "options": [
        "Compare user-supplied prices, not live market data."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "agriculture-3",
      "industry": "agriculture",
      "title": "Record keeping",
      "risk": "medium",
      "mode": "draft",
      "inputLabel": "Enter date, field, crop and observation",
      "example": "2026-11-25\nField A\nWheat\nIrrigation completed",
      "options": [
        "Date|Field|Crop|Observation",
        "Verify record|Save to your farm log"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "retail-1",
      "industry": "retail",
      "title": "Inventory summaries",
      "risk": "medium",
      "mode": "sum",
      "inputLabel": "Enter SKU,quantity (same unit)",
      "example": "SKU-A,12\nSKU-B,8",
      "options": [
        "Total units",
        "Use actual inventory data; no stock modifications."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "retail-2",
      "industry": "retail",
      "title": "Product catalog drafts",
      "risk": "medium",
      "mode": "draft",
      "inputLabel": "Enter product name, features and price",
      "example": "Notebook\n100 ruled pages\nINR 80",
      "options": [
        "Product|Verified features|Price",
        "Verify description|Check price and availability"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "retail-3",
      "industry": "retail",
      "title": "Customer FAQs",
      "risk": "medium",
      "mode": "quiz",
      "inputLabel": "Enter question|approved answer pairs",
      "example": "What are opening hours?|9 AM to 6 PM\nDo you deliver?|Ask the store",
      "options": [
        "Use as a FAQ review deck; answers are supplied by the business."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "manufacturing-1",
      "industry": "manufacturing",
      "title": "Maintenance documentation",
      "risk": "high",
      "mode": "check",
      "inputLabel": "Enter completed documentation tasks",
      "example": "Record asset ID\nRecord observation",
      "options": [
        "Record asset ID|Record observation|Attach approved maintenance record|Escalate safety concerns",
        "No machine operation instructions."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "manufacturing-2",
      "industry": "manufacturing",
      "title": "Quality summaries",
      "risk": "high",
      "mode": "group",
      "inputLabel": "Enter defect category,count",
      "example": "Surface,2\nPackaging,3\nSurface,1",
      "options": [
        "Recorded defects by category",
        "Not a safety or quality release decision."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "manufacturing-3",
      "industry": "manufacturing",
      "title": "Shift reports",
      "risk": "high",
      "mode": "draft",
      "inputLabel": "Enter shift, output, issue and handover",
      "example": "Morning\n120 units\nPackaging delay\nFollow up with supervisor",
      "options": [
        "Shift|Output|Issue|Handover",
        "Verify totals|Supervisor review"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "logistics-1",
      "industry": "logistics",
      "title": "Shipment lookup",
      "risk": "medium",
      "mode": "lookup",
      "inputLabel": "Paste shipment ID and status lines, search an ID",
      "example": "S-100: in transit\nS-101: delivered",
      "options": [
        "S-100",
        "Supplied records only; no live tracking."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "logistics-2",
      "industry": "logistics",
      "title": "Delivery exception summaries",
      "risk": "medium",
      "mode": "extract",
      "inputLabel": "Paste shipment exception notes",
      "example": "S-100 delivered.\nS-101 delayed due to weather.\nS-102 missing scan.",
      "options": [
        "delay|missing|exception|failed|damage",
        "Review extracted source lines; no dispatch changes."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "logistics-3",
      "industry": "logistics",
      "title": "Route planning support",
      "risk": "medium",
      "mode": "plan",
      "inputLabel": "Enter planned stops in desired order",
      "example": "Depot\nStop A\nStop B",
      "options": [
        "Confirm addresses|Check timing and restrictions|Verify route independently"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "legal-1",
      "industry": "legal",
      "title": "Plain-language document explanations",
      "risk": "high",
      "mode": "read",
      "inputLabel": "Paste a non-sensitive legal document excerpt",
      "example": "The agreement starts on 1 December. The notice period is 30 days.",
      "options": [
        "Source sentences only; consult a qualified lawyer."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "legal-2",
      "industry": "legal",
      "title": "Contract clause extraction",
      "risk": "high",
      "mode": "extract",
      "inputLabel": "Paste a non-sensitive contract excerpt",
      "example": "Payment is due within 30 days.\nTermination requires written notice.\nThe term is one year.",
      "options": [
        "payment|termination|notice|liability|renewal|term",
        "Keyword extraction only; lawyer review required."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "legal-3",
      "industry": "legal",
      "title": "Research assistance",
      "risk": "high",
      "mode": "lookup",
      "inputLabel": "Paste public legal reference excerpts, search keywords",
      "example": "Reference A: notice period provisions.\nReference B: filing requirements.",
      "options": [
        "notice",
        "Local supplied sources only; verify jurisdiction and currency."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "government-1",
      "industry": "government",
      "title": "Scheme navigation",
      "risk": "high",
      "mode": "lookup",
      "inputLabel": "Paste official scheme information, search a keyword",
      "example": "Scheme A: check official education eligibility criteria.\nScheme B: consult official business registration page.",
      "options": [
        "education",
        "No eligibility determination; verify official rules."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "government-2",
      "industry": "government",
      "title": "Form guidance",
      "risk": "high",
      "mode": "check",
      "inputLabel": "Enter documents you have, one per line",
      "example": "Read official instructions\nCheck deadline",
      "options": [
        "Read official instructions|Check deadline|Check required documents|Review form before submission",
        "No forms submitted; verify official requirements."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "government-3",
      "industry": "government",
      "title": "Public document search",
      "risk": "high",
      "mode": "lookup",
      "inputLabel": "Paste public document titles and excerpts",
      "example": "Public notice: road maintenance.\nPublic report: education expenditure.",
      "options": [
        "education",
        "Local search only; no live public web search."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "hospitality-1",
      "industry": "hospitality",
      "title": "Guest FAQs",
      "risk": "medium",
      "mode": "quiz",
      "inputLabel": "Enter guest question|approved answer pairs",
      "example": "Check-in time?|2 PM\nWi-Fi?|Ask reception",
      "options": [
        "Review hotel-approved answers."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "hospitality-2",
      "industry": "hospitality",
      "title": "Itinerary drafts",
      "risk": "medium",
      "mode": "plan",
      "inputLabel": "Enter itinerary stops in preferred order",
      "example": "Museum\nLunch\nPark",
      "options": [
        "Check opening hours|Confirm accessibility|Allow travel time"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "hospitality-3",
      "industry": "hospitality",
      "title": "Service request summaries",
      "risk": "medium",
      "mode": "draft",
      "inputLabel": "Enter request, location and response notes",
      "example": "Extra towel\nRoom number omitted\nNotify housekeeping",
      "options": [
        "Request|Location|Response notes",
        "Check consent and availability|Confirm resolution"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "real_estate-1",
      "industry": "real_estate",
      "title": "Listing comparison",
      "risk": "medium",
      "mode": "compare",
      "inputLabel": "Enter listing label,monthly rent (same currency)",
      "example": "Listing A,15000\nListing B,18000",
      "options": [
        "Rent comparison only; no valuation or recommendation."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "real_estate-2",
      "industry": "real_estate",
      "title": "Lease summaries",
      "risk": "medium",
      "mode": "extract",
      "inputLabel": "Paste lease excerpt",
      "example": "Rent is due on the first day.\nThe deposit is refundable under specified terms.\nNotice period is 30 days.",
      "options": [
        "rent|deposit|notice|renewal|maintenance",
        "Keyword extraction, not legal advice."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "real_estate-3",
      "industry": "real_estate",
      "title": "Property document checklists",
      "risk": "medium",
      "mode": "check",
      "inputLabel": "Enter completed checks",
      "example": "Verify ownership\nReview lease",
      "options": [
        "Verify ownership|Review lease|Check fees|Verify deposit terms|Seek professional review",
        "Requirements vary by jurisdiction."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "hr-1",
      "industry": "hr",
      "title": "Interview practice",
      "risk": "high",
      "mode": "quiz",
      "inputLabel": "Enter practice question|your answer outline",
      "example": "Tell me about a project?|Describe context, action and outcome",
      "options": [
        "Self-practice; no hiring score or decision."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "hr-2",
      "industry": "hr",
      "title": "Resume assistance",
      "risk": "high",
      "mode": "draft",
      "inputLabel": "Enter role, skills and verified achievement",
      "example": "Data analyst\nSQL, reporting\nBuilt monthly dashboard",
      "options": [
        "Target role|Skills|Verified achievement",
        "Check factual accuracy|Tailor to role"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "hr-3",
      "industry": "hr",
      "title": "Job description drafting",
      "risk": "high",
      "mode": "draft",
      "inputLabel": "Enter role, responsibilities and essential qualifications",
      "example": "Support associate\nResolve customer queries\nCommunication skills",
      "options": [
        "Role|Responsibilities|Essential qualifications",
        "Remove discriminatory criteria|Human review"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "media-1",
      "industry": "media",
      "title": "Research outlines",
      "risk": "medium",
      "mode": "plan",
      "inputLabel": "Enter research topics or questions",
      "example": "Background\nEvidence\nCounterarguments",
      "options": [
        "Check primary sources|Outline findings|Fact-check before publication"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "media-2",
      "industry": "media",
      "title": "Captions",
      "risk": "medium",
      "mode": "draft",
      "inputLabel": "Enter topic, verified takeaway and call to action",
      "example": "Open-source tools\nTests are reproducible\nRead the repository",
      "options": [
        "Topic|Verified takeaway|Call to action",
        "Check accuracy and rights|Edit tone before posting"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "media-3",
      "industry": "media",
      "title": "Content repurposing",
      "risk": "medium",
      "mode": "read",
      "inputLabel": "Paste your own article or transcript",
      "example": "We tested a local demo. All test fixtures were synthetic. Independent review is pending.",
      "options": [
        "Extracted sentences only; no model rewriting."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "nonprofit-1",
      "industry": "nonprofit",
      "title": "Grant research",
      "risk": "medium",
      "mode": "lookup",
      "inputLabel": "Paste grant descriptions and search a topic",
      "example": "Grant A: education projects.\nGrant B: community health initiatives.",
      "options": [
        "education",
        "Verify eligibility and deadlines independently."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "nonprofit-2",
      "industry": "nonprofit",
      "title": "Volunteer coordination drafts",
      "risk": "medium",
      "mode": "draft",
      "inputLabel": "Enter event, tasks and timing",
      "example": "Community cleanup\nCollect supplies\nSaturday morning",
      "options": [
        "Event|Tasks|Timing",
        "Confirm consent|Check accessibility|Assign roles with approval"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "nonprofit-3",
      "industry": "nonprofit",
      "title": "Impact reporting",
      "risk": "medium",
      "mode": "sum",
      "inputLabel": "Enter program,beneficiary count (non-overlapping)",
      "example": "Workshop A,20\nWorkshop B,15",
      "options": [
        "Reported aggregate count",
        "Avoid double counting; verify source data."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "energy-1",
      "industry": "energy",
      "title": "Energy literacy",
      "risk": "high",
      "mode": "quiz",
      "inputLabel": "Enter term|definition pairs from trusted materials",
      "example": "kWh|Kilowatt-hour, a unit of energy\nWatt|A unit of power",
      "options": [
        "Educational reference only."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "energy-2",
      "industry": "energy",
      "title": "Sustainability summaries",
      "risk": "high",
      "mode": "group",
      "inputLabel": "Enter metric category,value (same unit)",
      "example": "Electricity,200\nElectricity,150\nElectricity,100",
      "options": [
        "Reported totals by category",
        "Use consistent units and verify data; no emissions claim."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "energy-3",
      "industry": "energy",
      "title": "Public data interpretation",
      "risk": "high",
      "mode": "compare",
      "inputLabel": "Enter location,value (same unit)",
      "example": "Site A,120\nSite B,95",
      "options": [
        "Compare supplied public data; no infrastructure control."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "construction-1",
      "industry": "construction",
      "title": "Project documentation",
      "risk": "high",
      "mode": "draft",
      "inputLabel": "Enter project, date, observation and next action",
      "example": "Project A\n2026-11-25\nMaterial received\nVerify count",
      "options": [
        "Project|Date|Observation|Next action",
        "Supervisor review|Record evidence"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "construction-2",
      "industry": "construction",
      "title": "Material inventory",
      "risk": "high",
      "mode": "sum",
      "inputLabel": "Enter material,quantity (same unit)",
      "example": "Tiles A,20\nTiles B,30",
      "options": [
        "Total quantity",
        "Do not mix units; no structural calculations."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "construction-3",
      "industry": "construction",
      "title": "Progress summaries",
      "risk": "high",
      "mode": "group",
      "inputLabel": "Enter work category,completed quantity (same unit)",
      "example": "Painting,10\nPainting,5",
      "options": [
        "Progress totals",
        "No safety or completion certification."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "research-1",
      "industry": "research",
      "title": "Literature organization",
      "risk": "medium",
      "mode": "lookup",
      "inputLabel": "Paste paper titles or notes, search keywords",
      "example": "Paper A: agent evaluation.\nPaper B: context compression.",
      "options": [
        "evaluation",
        "Verify citations and use licensed material."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "research-2",
      "industry": "research",
      "title": "Reproducibility checklists",
      "risk": "medium",
      "mode": "check",
      "inputLabel": "Enter completed reproducibility checks",
      "example": "Frozen dataset\nVersioned code",
      "options": [
        "Frozen dataset|Versioned code|Baseline specified|Raw results archived|Limitations documented",
        "Research checklist, not peer review."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "research-3",
      "industry": "research",
      "title": "Experiment tracking",
      "risk": "medium",
      "mode": "draft",
      "inputLabel": "Enter hypothesis, method, result and limitation",
      "example": "Host binding reduces scoped violations\nSynthetic cases\n96 authorized reads\nNo independent validation",
      "options": [
        "Hypothesis|Method|Result|Limitation",
        "Archive evidence|Review claims before publication"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "software-1",
      "industry": "software",
      "title": "Agent evaluation",
      "risk": "medium",
      "mode": "evaluate",
      "inputLabel": "Enter authorized,executed,correct as 1/0 per line",
      "example": "1,1,1\n0,0,0\n1,0,0",
      "options": [
        "Measure task completion and unsafe execution separately."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "software-2",
      "industry": "software",
      "title": "Execution guardrails",
      "risk": "medium",
      "mode": "guard",
      "inputLabel": "Enter action,authorized action on one line",
      "example": "read_record,read_record",
      "options": [
        "Exact action-name simulation only; not a security boundary."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "software-3",
      "industry": "software",
      "title": "Debugging",
      "risk": "medium",
      "mode": "extract",
      "inputLabel": "Paste redacted logs",
      "example": "INFO started\nERROR provider timeout\nWARN quota exceeded",
      "options": [
        "error|failed|timeout|denied|quota|warn",
        "Extract matching log lines; no automated repair."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "small_business-1",
      "industry": "small_business",
      "title": "SOP drafting",
      "risk": "medium",
      "mode": "draft",
      "inputLabel": "Enter process, owner, trigger and steps",
      "example": "Invoice review\nFinance team\nNew invoice\nCheck details and route for approval",
      "options": [
        "Process|Owner|Trigger|Steps",
        "Verify scope|Approve SOP|Review periodically"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "small_business-2",
      "industry": "small_business",
      "title": "Sales FAQ",
      "risk": "medium",
      "mode": "quiz",
      "inputLabel": "Enter sales question|approved answer",
      "example": "Do you offer trials?|Contact sales for current options",
      "options": [
        "Review approved responses."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "small_business-3",
      "industry": "small_business",
      "title": "Business record summaries",
      "risk": "medium",
      "mode": "group",
      "inputLabel": "Enter record category,amount (same unit)",
      "example": "Sales,500\nSales,200\nReturns,100",
      "options": [
        "Totals by supplied category",
        "No automatic transactions or financial advice."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "accessibility-1",
      "industry": "accessibility",
      "title": "Plain-language rewriting",
      "risk": "medium",
      "mode": "read",
      "inputLabel": "Paste text for sentence-by-sentence reading",
      "example": "Complete the form. Read the instructions before submitting.",
      "options": [
        "Extracts original sentences; not AI simplification."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "accessibility-2",
      "industry": "accessibility",
      "title": "Text navigation",
      "risk": "medium",
      "mode": "lookup",
      "inputLabel": "Paste text sections, then search",
      "example": "Section 1: introduction.\nSection 2: payment terms.",
      "options": [
        "payment",
        "Find matching text locally."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "accessibility-3",
      "industry": "accessibility",
      "title": "Reading assistance",
      "risk": "medium",
      "mode": "read",
      "inputLabel": "Paste text to read in separated sentences",
      "example": "Welcome to the library. Books can be borrowed for 14 days.",
      "options": [
        "Use browser accessibility tools or screen reader; no speech synthesis."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "transport-1",
      "industry": "transport",
      "title": "Travel information summaries",
      "risk": "high",
      "mode": "read",
      "inputLabel": "Paste official travel information",
      "example": "Train A departs at 9 AM. Check the official schedule for updates.",
      "options": [
        "Source sentences only; not live travel data."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "transport-2",
      "industry": "transport",
      "title": "Fleet documentation",
      "risk": "high",
      "mode": "draft",
      "inputLabel": "Enter vehicle label, observation and next action",
      "example": "Fleet A\nRoutine check recorded\nSend to supervisor",
      "options": [
        "Vehicle label|Observation|Next action",
        "Qualified safety review required"
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "transport-3",
      "industry": "transport",
      "title": "Schedule interpretation",
      "risk": "high",
      "mode": "lookup",
      "inputLabel": "Paste schedule lines, then search",
      "example": "Route A: 09:00 departure\nRoute B: 10:30 departure",
      "options": [
        "Route A",
        "Supplied schedule only; verify latest timetable."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "insurance-1",
      "industry": "insurance",
      "title": "Policy explanation",
      "risk": "high",
      "mode": "extract",
      "inputLabel": "Paste policy excerpt",
      "example": "Coverage is subject to exclusions.\nThe deductible is specified in the schedule.",
      "options": [
        "coverage|exclusion|deductible|limit|premium",
        "Keyword extraction only; consult insurer."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "insurance-2",
      "industry": "insurance",
      "title": "Claims document checklist",
      "risk": "high",
      "mode": "check",
      "inputLabel": "Enter documents already gathered",
      "example": "Policy reference\nClaim form",
      "options": [
        "Policy reference|Claim form|Required supporting records|Verify submission instructions",
        "No claim filed or eligibility assessed."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "insurance-3",
      "industry": "insurance",
      "title": "Record lookup",
      "risk": "high",
      "mode": "lookup",
      "inputLabel": "Paste authorized record labels and statuses",
      "example": "Claim A: under review\nClaim B: documents requested",
      "options": [
        "Claim B",
        "Supplied records only; no live insurer access."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "cybersecurity-1",
      "industry": "cybersecurity",
      "title": "Defensive audit checklist",
      "risk": "high",
      "mode": "check",
      "inputLabel": "Enter completed defensive controls",
      "example": "Asset inventory\nAccess review",
      "options": [
        "Asset inventory|Access review|Patch review|Backup restore test|Incident response plan",
        "Authorized environment only; not a security certification."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "cybersecurity-2",
      "industry": "cybersecurity",
      "title": "Policy review",
      "risk": "high",
      "mode": "extract",
      "inputLabel": "Paste non-sensitive policy text",
      "example": "Access requires approval.\nCredentials must be rotated.\nLogs must be reviewed.",
      "options": [
        "access|approval|credential|audit|log|retention",
        "Review source policy; no exploit guidance."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    },
    {
      "id": "cybersecurity-3",
      "industry": "cybersecurity",
      "title": "Safe synthetic evaluation",
      "risk": "high",
      "mode": "evaluate",
      "inputLabel": "Enter authorized,executed,correct as 1/0 per line",
      "example": "1,1,1\n0,0,0\n0,1,0",
      "options": [
        "Synthetic test results only; not a penetration test."
      ],
      "stage": "local_utility",
      "scope": "Deterministic browser utility; no AI model or external service."
    }
  ]
};
