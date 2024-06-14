from langchain_community.retrievers import TavilySearchAPIRetriever
from openai import OpenAI
import pandas as pd
import asyncio
import time
import time
import json
import os
import re

from dotenv import load_dotenv


class KnowledgeAssistant:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    ####___________________________ASSISTANT 1___________________________####

    async def setup_extraction_assistant(
        self, Company_Name: str,  vector_store_id: str
    ):
        json_file = {"key1": "value1", "key2": "value2"}
        instruction = f"""
            Hello, you are an expert in Website Knowledge Extraction and will act as a personal assistant for {Company_Name}.
            
            
            
            create a comprehensive company overview, formatted as a JSON file like {json_file}.
            The extracted information will be used to create a comprehensive company overview, formatted as a JSON file like {json_file}.

            Please extract and categorize the information according to the following guidelines:
            
            1. **Summary**: Provide a brief overview of {Company_Name} including key facts.
            2. **Foundation**: State the year {Company_Name} was established.
            3. **Headquarters**: Mention the location of {Company_Name}'s main office.
            4. **Employees**: Provide the current count of full-time employees at {Company_Name}.
            5. **About Us**: Summarize the company's history and mission.
            6. **Leadership**: Include profiles of key executives (CEO, CFO, COO).
            7. **KPIs**: List Key Performance Indicators relevant to the company's sector, along with descriptions.
            8. **Financials**: Detail financial metrics such as Revenue, EBITDA, Margins, Total Debt, Debt/EBITDA, and the last 2 years of Quarter-on-Quarter financials.
            9. **Latest Stories**: Include the most recent news articles or press releases.
            10. **Our Markets**: Describe the markets in which the company operates.
            11. **Our Products**: List and describe the company's products and services.
            12. **Our Vision**: Explain the company's vision and values.
            13. **Links**: Provide links to social media profiles or other relevant websites.
            14. **Association Memberships or Certifications**: Mention any industry affiliations or certifications.
            15. **Contact**: Provide the contact information for the company.
            16. **Market Segments**: Analyze the markets in which the company operates.
            17. **Products & Services**: Give a detailed list and description of the company’s offerings.
            18. **Buyout**: Provide information on any major acquisitions or buyouts.
            19. **Pictures**: Include product images, the company logo, leadership headshots, and other relevant visuals.
            20. **Major Customers and/or Partners**: List notable B2B clients or partners.
            21. **Strategic Fit**: Analyze the strategic fit for potential buyers or investors.
            
            Additionally, extract the **page content** and **titles** from the documents provided and include them in the JSON file under the keys "page_contents" and "titles".

            Ensure that the extracted information is accurate and well-organized. If the content is not publicly available, do not include it in the JSON file. If certain categories are not applicable, simply omit them without writing 'N/A'.

            Format the final JSON file properly, ensuring each category is correctly represented.
        """
        assistant = self.client.beta.assistants.create(
            name=f"{Company_Name}_Website Scraper",
            instructions=instruction,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            temperature=0.6,
        )

        # print(f"Assistant {assistant.id} is set up with vector store {vector_store_id}.")
        return assistant.id, vector_store_id

    async def run_chatbot(self, Company_URL: str, Company_Name: str ):
        Company_URL = re.sub(r"\W+", "_", Company_URL)
        retriever = TavilySearchAPIRetriever(search_depth="advanced", max_tokens=10000)
        retriever_result = retriever.invoke(Company_URL)
        retriever_str = str(retriever_result)
        retriever_result = f"Retrieved data from {Company_URL} for {Company_Name}"
        txt_file_path = f"{Company_Name}_website.txt"
        with open(txt_file_path, "w", encoding="utf-8") as file:
            file.write(retriever_str)
        print(f"The contents of 'retriever' have been saved to '{txt_file_path}'.")

        message_file = self.client.files.create(
            file=open(txt_file_path, "rb"), purpose="assistants"
        )
        print("File uploaded successfully.", message_file.id)
        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": "Company Data Scraping",
                    "attachments": [
                        {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
                    ],
                }
            ],
        )
        existing_vector_store_id = thread.tool_resources.file_search.vector_store_ids[0]
        assistant_id, vector_store_id = await self.setup_extraction_assistant(
            Company_Name, existing_vector_store_id
        )
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )
        time.sleep(5)

        # Polling loop to check the status
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status not in ["queued", "in_progress"]:
                break
            time.sleep(2)  # Poll every 2 seconds

        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id
        )

        return vector_store_id

    ####___________________________ASSISTANT 2___________________________####
    def financial_overview_assistant(self, Company_Name, vector_store_id):

        instruction = """
            YOU ARE "{Company_Name}" FINANCIAL ASSISTANT.
            Required to use "File Search" method to go through the Vector Store and then generate the RESPONSE
            # YOU NEED TO RESPOND BACK WITH A JSON RESPONSE ONLY, WHICH SHOULD HAVE THE FOLLOWING KEYS (You need to specify the year where (year) is mentioned in the keys, ONLY PROVIDE ANSWERS TO THE KEYS ACCORDING TO THE DATA STORED IN THE VECTOR STORE AND BEFORE GENERATING YOU NEED TO VERIFY IF THE INFORMATION IS CORRECT OR NOT YOU CANNOT HALLUCINATE ONLY PROVIDE ANSWERS FROM THE VECTOR STORE USING "File Search" Tool #GO THROUGH ALL THE FILES IN YOUR VECTOR STORE AND ENRICH YOURSELF WITH ALL THE RICH INFORMATION:
            - (year) Revenue
            - (year) EBITDA
            - (year) EBITDA MARGIN
            - TOTAL DEBT
            - DEBT/EBITDA
        """
        assistant = self.client.beta.assistants.create(
            name=f"{Company_Name}_Financial_Overview_Assistant",
            instructions=instruction,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            temperature=0.6,
        )
        print(f"My Assistant: {assistant}")

        return assistant.id, vector_store_id

    async def run_finance_bot(self, Company_Name: str, vector_store_id: str):

        assistant_id, vector_store_id = self.financial_overview_assistant(
            Company_Name, vector_store_id
        )

        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": "Company Data Scraping",
                }
            ],
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )
        time.sleep(5)

        # Polling loop to check the status
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status not in ["queued", "in_progress"]:
                break
            time.sleep(2)  # Poll every 2 seconds

        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id
        )

        response_message = next(
            (msg for msg in messages if msg.role == "assistant"), None
        )
        if response_message:
            response_content = response_message.content[0].text.value
            return response_content, vector_store_id
        return None

    ####___________________________ASSISTANT 3___________________________####

    def company_overview_assistant(self, Company_Name, vector_store_id):

        instruction = f"""
            <INSTRUCTIONS>Trends and Common Elements in Descriptions: 
            Conciseness and Clarity: Descriptions are concise and clearly state what the company does. Avoiding jargon and focusing on easily understandable language is key.
            Highlighting Unique Selling Points (USPs): Emphasize what makes the company unique or superior in its field.
            Customer and Market Focus: Clearly identify the target customers and market. Understanding the company’s customer base and market position is crucial.
            Achievements and Credibility: Including recent achievements, awards, and recognitions to build credibility.
            Forward-Looking Statements: Some profiles may include the company’s future plans or strategic goals, providing insight into their growth trajectory.
            Tone and Style
            Professional, Concise and Direct: The tone is formal and business-like, focusing on clarity and precision without unnecessary jargon. The tone is professional, focusing on delivering clear and precise information.
            Focused on Value and Benefits: The descriptions emphasize the value and benefits the company provides to its customers. Emphasis is placed on the value and benefits provided to customers, particularly in terms of efficiency, productivity, and quality.
            Highlighting Innovation/Technologically Advanced: There is a strong emphasis on the innovative aspects of the company's products and services. The description highlights the use of advanced technologies to convey innovation and industry leadership. 
            Customer-Centric: Many descriptions focus on how the company's offerings impact and benefit the customers.
            Industry-Specific: The language is tailored to address the specific needs and concerns of industrial companies, making it relevant and impactful.
            Common Characteristics of the "Description" Field
            Introduction to the Company’s Core Business: (First Sentence) Typically, the description starts with a brief introduction to the company's core business. This includes what the company does and the industry it operates in.
            "Hyland Software provides enterprise-level document content management solutions."
            "XYZ Manufacturing is a leading provider of industrial automation solutions, specializing in the design and manufacture of advanced machinery and equipment for the manufacturing sector."
            Highlighting Main Products and Services: (Key Offerings) The description often includes a concise list or mention of the company's main products and services, focusing on the most significant or innovative ones.
            "The Company offers OnBase, a content management software suite for enterprises to capture, route, manage, share, and archive corporate information for business operations, audits, and customer services."
            "The company offers a comprehensive range of products, including Automated Assembly Lines, CNC Machines, and Robotic Systems."
            Unique Selling Proposition (USP): (Differentiators) The description highlights what makes the company unique or superior in its field. This might include special features, technological advancements, or specific benefits of their offerings.
            "The combination of post-process deduplication, most recent backup cache and GRID scalability enables IT departments to achieve the shortest backup window and the fastest, most reliable restores."
            "What sets XYZ Manufacturing apart is its state-of-the-art automation technology, which integrates seamlessly with existing production lines to improve efficiency and productivity."
            Industry and Market Focus: (Target Markets) It often specifies the markets or industries the company serves, showcasing the breadth of their customer base.
            "Hyland serves a wide range of industries, including commercial, financial services, food and beverage, government, healthcare, higher education and insurance."
            "XYZ Manufacturing serves a wide range of industries, including automotive, aerospace, consumer goods, and electronics."
            Technological Integration and Innovation: Descriptions frequently mention any advanced technologies the company uses or has developed.
            "ExaGrid offers a disk-based backup appliance with data deduplication purpose-built for backup that uses a unique architecture optimized for performance, scalability and price."
            "The company leverages cutting-edge technologies such as IoT, AI, and machine learning to provide intelligent automation solutions."
            Impact and Benefits: They often conclude with the impact or benefits the company’s products/services have on their customers or industry.
            "By delivering technology that integrates all benefits in one place, Benefitfocus provides a way to engage consumers, educate employees and simplify benefit enrollment and management."
            "By utilizing XYZ Manufacturing's automation solutions, companies can achieve significant improvements in operational efficiency, product quality, and production speed."
            Common Format or Formula
            Opening Statement:
            Introduce the company and its core business.
            Example: "[Company Name] is a leading [industry/sector] company that specializes in [core competency or primary business function]."
            Main Products and Services:
            Highlight the key products and services.
            Example: "The company offers a range of [products/services], including [notable product/service 1], [notable product/service 2], and [notable product/service 3]."
            Unique Selling Proposition (USP):
            Emphasize what makes the company unique or superior.
            Example: "What sets [Company Name] apart is its [unique technology/approach/feature], which [explains the benefit]."
            Industry and Market Focus:
            Mention the primary markets or industries served.
            Example: "[Company Name] serves a diverse range of industries, including [industry 1], [industry 2], and [industry 3]."
            Technological Integration and Innovation:
            Detail any significant technologies or innovations.
            Example: "The company integrates advanced [technology/techniques], enabling [specific benefit or efficiency]."
            Impact and Benefits:
            Conclude with the overall impact and benefits to the customers or industry.
            Example: "By leveraging its [technology/products/services], [Company Name] helps [target audience] achieve [key benefits, such as increased efficiency, reduced costs, or improved performance]."
            Required to use "File Search" method to go through the Vector Store and then generate the RESPONSE</INSTRUCTIONS>
            #YOU NEED TO RESPOND BACK WITH A JSON RESPONSE ONLY, WHICH SHOULD HAVE THE FOLLOWING KEYS AND BEFORE GENERATING YOU NEED TO VERIFY IF THE INFORMATION IS CORRECT OR NOT FROM THE <INSTRUCTIONS> YOU CANNOT HALLUCINATE ONLY PROVIDE ANSWERS FROM THE VECTOR STORE USING "File Search" Tool:
            - Company Name
            - Company Owner
            - Company Website/Division
            - Company Tagline
            - Description [ABOUT 40 - 50 WORDS]
            - Founded
            - HeadQuaters
            - No. of Employees
            - KPIs
            - Buyouts
        """
        assistant = self.client.beta.assistants.create(
            name=f"{Company_Name}_Company_Overview_Assistant",
            instructions=instruction,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            temperature=0.6,
        )

        # print(f"Assistant {assistant.id} is set up with vector store {vector_store_id}.")
        return assistant.id, vector_store_id

    async def run_company_overview_bot(self, Company_Name: str, vector_store_id: str):

        assistant_id, vector_store_id = self.company_overview_assistant(
            Company_Name, vector_store_id
        )

        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{Company_Name} Company Overview",
                }
            ],
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )
        time.sleep(5)

        # Polling loop to check the status
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status not in ["queued", "in_progress"]:
                break
            time.sleep(2)  # Poll every 2 seconds
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id
        )

        response_message = next(
            (msg for msg in messages if msg.role == "assistant"), None
        )
        if response_message:
            response_content = response_message.content[0].text.value
            return response_content, vector_store_id
        return None

    ####___________________________ASSISTANT 4___________________________####

    def leadership_overview_assistant(self, Company_Name, vector_store_id):

        instruction = f"""
            YOU ARE "{Company_Name}" LEADERSHIP ASSISTANT YOU NEED TO PROVIDE "Leadership Overview: Profiles of key executives (CEO, CFO, COO), Name, Title, Bio if available if not drop key".
            Required to use "File Search" method to go through the Vector Store and then generate the RESPONSE
            #YOU NEED TO RESPOND BACK WITH A JSON RESPONSE ONLY, WHICH SHOULD HAVE THE FOLLOWING KEYS (You need to specify the year where (year) is mentioned in the keys, ONLY PROVIDE ANSWERS TO THE KEYS ACCORDING TO THE DATA STORED IN THE VECTOR STORE AND BEFORE GENERATING YOU NEED TO VERIFY IF THE INFORMATION IS CORRECT OR NOT YOU CANNOT HALLUCINATE ONLY PROVIDE ANSWERS FROM THE VECTOR STORE USING "File Search" Tool #GO THROUGH ALL THE FILES IN YOUR VECTOR STORE AND ENRICH YOURSELF WITH ALL THE RICH INFORMATION:
            - CEO NAME
            - CEO TITLE
            - CEO BIO
        """
        assistant = self.client.beta.assistants.create(
            name=f"{Company_Name}_Leadership_Overview_Assistant",
            instructions=instruction,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            temperature=0.6,
        )

        print(
            f"Assistant {assistant.id} is set up with vector store {vector_store_id}."
        )
        return assistant.id, vector_store_id

    async def run_leadership_overview_bot(
        self, Company_Name: str, vector_store_id: str
    ):

        assistant_id, vector_store_id = self.leadership_overview_assistant(
            Company_Name, vector_store_id
        )

        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{Company_Name} Leadership Overview",
                }
            ],
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )
        time.sleep(5)

        # Polling loop to check the status
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status not in ["queued", "in_progress"]:
                break
            time.sleep(2)  # Poll every 2 seconds
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id
        )

        response_message = next(
            (msg for msg in messages if msg.role == "assistant"), None
        )
        if response_message:
            response_content = response_message.content[0].text.value
            return response_content, vector_store_id
        return None

    ####___________________________ASSISTANT 5___________________________####
    def products_and_services_assistant(self, Company_Name, vector_store_id):

        instruction = f"""
        YOU ARE "{Company_Name}" PRODUCTS & SERVICES ASSISTANT YOU NEED TO PROVIDE "Products & Services: Detailed list and descriptions of the company’s offerings. For Example: Product 1 Name: Description, Product 2 Name: Description, etc (all Products or Services wih their Descriptions)...".
        Required to use "File Search" method to go through the Vector Store and then generate the RESPONSE
        #YOU NEED TO RESPOND BACK WITH A JSON RESPONSE ONLY, WHICH SHOULD HAVE THE FOLLOWING KEYS (You need to specify the year where (year) is mentioned in the keys, ONLY PROVIDE ANSWERS TO THE KEYS ACCORDING TO THE DATA STORED IN THE VECTOR STORE AND BEFORE GENERATING YOU NEED TO VERIFY IF THE INFORMATION IS CORRECT OR NOT YOU CANNOT HALLUCINATE ONLY PROVIDE ANSWERS FROM THE VECTOR STORE USING "File Search" Tool #GO THROUGH ALL THE FILES IN YOUR VECTOR STORE AND ENRICH YOURSELF WITH ALL THE RICH INFORMATION:
        - OFFERING: "PRODUCT" OR "SERVICES" #(Choose one according to the company details inside the Vector Store of {vector_store_id})
        #LIST DOWN ALL THE  OFFERINGS (PRODUCST/SERVICES) IN A SEPERATE FIELD CONTAINING THEIR DESCRIPTIONS
        "NAME" : "DESCRIPTION"


        """
        assistant = self.client.beta.assistants.create(
            name=f"{Company_Name}_Product_And_Services_Assistant",
            instructions=instruction,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            temperature=0.6,
        )

        # print(f"Assistant {assistant.id} is set up with vector store {vector_store_id}.")
        return assistant.id, vector_store_id

    async def run_product_and_services_bot(
        self, Company_Name: str, vector_store_id: str
    ):

        assistant_id, vector_store_id = self.products_and_services_assistant(
            Company_Name, vector_store_id
        )

        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{Company_Name} Products or Services Overview",
                }
            ],
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )
        time.sleep(5)

        # Polling loop to check the status
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status not in ["queued", "in_progress"]:
                break
            time.sleep(2)  # Poll every 2 seconds
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id
        )

        response_message = next(
            (msg for msg in messages if msg.role == "assistant"), None
        )
        if response_message:
            response_content = response_message.content[0].text.value
            return response_content, vector_store_id
        return None

    ####___________________________ASSISTANT 6___________________________####

    def market_segment_assistant(self, Company_Name, vector_store_id):

        instruction = f"""
        YOU ARE "{Company_Name}" MARKET SEGMENT ASSISTANT YOU NEED TO PROVIDE "Market Segments: Analysis of the markets in which the company operates. #HEADING THAT REPRESENTS THEIR MARKET SEGMENT FOR EXAMPLE  'Fastening Systems' :
        'market segmet 1 name' : 'Description',
        'market segmet 2 name' : 'Description'
        etc..".
        Required to use "File Search" method to go through the Vector Store and then generate the RESPONSE
        #YOU NEED TO RESPOND BACK WITH A JSON RESPONSE ONLY, WHICH SHOULD HAVE THE FOLLOWING KEYS (You need to specify the year where (year) is mentioned in the keys, ONLY PROVIDE ANSWERS TO THE KEYS ACCORDING TO THE DATA STORED IN THE VECTOR STORE AND BEFORE GENERATING YOU NEED TO VERIFY IF THE INFORMATION IS CORRECT OR NOT YOU CANNOT HALLUCINATE ONLY PROVIDE ANSWERS FROM THE VECTOR STORE USING "File Search" Tool #GO THROUGH ALL THE FILES IN YOUR VECTOR STORE AND ENRICH YOURSELF WITH ALL THE RICH INFORMATION: 
        - #CREATE MARKET SEGMENT NAME:  #(Choose one according to the company details inside the Vector Store)
        - #YOU CAN NOT CREATE A NESTED STRUCTURED JSON RESPONSE YOU ONLY NEED TO PROVIDE A FLAT JSON RESPONSE WITH ALL THE KEYS AND THEIR VALUES
        
        """
        assistant = self.client.beta.assistants.create(
            name=f"{Company_Name}_Market_Segment_Assistant",
            instructions=instruction,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            temperature=0.6,
        )

        print(
            f"Assistant {assistant.id} is set up with vector store {vector_store_id}."
        )
        return assistant.id, vector_store_id

    async def run_market_segment_bot(self, Company_Name: str, vector_store_id: str):

        assistant_id, vector_store_id = self.market_segment_assistant(
            Company_Name, vector_store_id
        )

        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{Company_Name} Market Segment",
                }
            ],
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )
        time.sleep(5)

        # Polling loop to check the status
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status not in ["queued", "in_progress"]:
                break
            time.sleep(2)  # Poll every 2 seconds
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id
        )

        response_message = next(
            (msg for msg in messages if msg.role == "assistant"), None
        )
        if response_message:
            response_content = response_message.content[0].text.value
            return response_content, vector_store_id
        return None

    ####___________________________ASSISTANT 8___________________________####

    def customer_partner_assistant(self, Company_Name, vector_store_id):

        instruction = """
        YOU ARE "{Company_Name}" MAJOR CUSTOMERS AND/OR PARTNER ASSISTANT YOU NEED TO PROVIDE "Major Customers and/or Partners: Notable B2B clients or partners.. #
        'Partner 1 Name' : 'Which Segment',
        'Partner 2 Name' : 'Which Segment'
        etc..
        
        
        'Customer 1 Name' : 'Which Segment',
        'Customer 2 Name' : 'Which Segment'
        etc..
       
        Required to use "File Search" method to go through the Vector Store and then generate the RESPONSE
        #YOU NEED TO RESPOND BACK WITH A JSON RESPONSE ONLY, WHICH SHOULD HAVE THE FOLLOWING KEYS (You need to specify the year where (year) is mentioned in the keys, ONLY PROVIDE ANSWERS TO THE KEYS ACCORDING TO THE DATA STORED IN THE VECTOR STORE AND BEFORE GENERATING YOU NEED TO VERIFY IF THE INFORMATION IS CORRECT OR NOT YOU CANNOT HALLUCINATE ONLY PROVIDE ANSWERS FROM THE VECTOR STORE USING "File Search" Tool #GO THROUGH ALL THE FILES IN YOUR VECTOR STORE AND ENRICH YOURSELF WITH ALL THE RICH INFORMATION: 
        - #IDENTIFY PARTNERS OR CUSTOMERS:  #(Choose one according to the company details inside the Vector Store)
      
        #LIST DOWN ALL THE PARTNERS WITH THEIR ASSOCIATE DESCRIPTION
        "NAME" : "DESCRIPTION"
      
        #LIST DOWN ALL THE CUSTOMERS WITH THEIR ASSOCIATE DESCRIPTION
        "NAME" : "DESCRIPTION"
       
        #LIST DOWN ALL THE SOURCES REFERENCES FOR THE CUSTOMERS AND PARTNERS
        "SOURCE1" : "SOURE1 URL"
       
        
        """
        assistant = self.client.beta.assistants.create(
            name=f"{Company_Name}_Market_Segment_Assistant",
            instructions=instruction,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            temperature=0.6,
        )

        print(
            f"Assistant {assistant.id} is set up with vector store {vector_store_id}."
        )
        return assistant.id, vector_store_id

    async def run_customer_partner_bot(self, Company_Name: str, vector_store_id: str):

        assistant_id, vector_store_id = self.customer_partner_assistant(
            Company_Name, vector_store_id
        )

        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{Company_Name} Customers and Partners",
                }
            ],
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )
        time.sleep(5)

        # Polling loop to check the status
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run_status.status not in ["queued", "in_progress"]:
                break
            time.sleep(2)  # Poll every 2 seconds
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id
        )

        response_message = next(
            (msg for msg in messages if msg.role == "assistant"), None
        )
        if response_message:
            response_content = response_message.content[0].text.value
            return response_content, vector_store_id
        return None

    ####___________________________ASSISTANT 9___________________________####
    def strategic_fit_assistant(self, Company_Name, vector_store_id):

        instruction = """
        YOU ARE "{Company_Name}" STRATEGIC ASSISTANT YOU NEED TO PROVIDE "Strategic Fit: Analysis on the fit for potential buyers or investors. #{
        'Rationale' : 'Describe',
        'Issues for Consideration' : 'Define'
        etc..
        }"

        Required to use "File Search" method to go through the Vector Store and then generate the RESPONSE
        #YOU NEED TO RESPOND BACK WITH A JSON RESPONSE ONLY, WHICH SHOULD HAVE THE FOLLOWING KEYS (You need to specify the year where (year) is mentioned in the keys, ONLY PROVIDE ANSWERS TO THE KEYS ACCORDING TO THE DATA STORED IN THE VECTOR STORE AND BEFORE GENERATING YOU NEED TO VERIFY IF THE INFORMATION IS CORRECT OR NOT YOU CANNOT HALLUCINATE ONLY PROVIDE ANSWERS FROM THE VECTOR STORE USING "File Search" Tool #GO THROUGH ALL THE FILES IN YOUR VECTOR STORE AND ENRICH YOURSELF WITH ALL THE RICH INFORMATION: 

        """
        assistant = self.client.beta.assistants.create(
            name=f"{Company_Name}_Market_Segment_Assistant",
            instructions=instruction,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            temperature=0.6,
        )

        print(
            f"Assistant {assistant.id} is set up with vector store {vector_store_id}."
        )
        return assistant.id, vector_store_id

    async def run_strategic_fit_bot(self, Company_Name: str, vector_store_id: str):

        assistant_id, vector_store_id = self.strategic_fit_assistant(
            Company_Name, vector_store_id
        )

        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{Company_Name}'s Strategic Fit",
                }
            ],
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )

        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id
        )

        response_message = next(
            (msg for msg in messages if msg.role == "assistant"), None
        )
        if response_message:
            response_content = response_message.content[0].text.value
            return response_content, vector_store_id
        return None

    ####___________________________ASSISTANT 10___________________________####

    # def response_validation_assistant(self, response, context, vector_store_id):

    #     instruction = f"""
    #         You will receive a JSON response and context. You need to validate the response and provide feedback on the accuracy of the response.
    #         The final response must follow the exact same formats in terms of keys and instances as received. The only thing you need to check is that the information is
    #         validated by the vector store accessed by {vector_store_id}.

    #         Cross check the information sent in {response} to the information saved in {vector_store_id}

    #         Prioritize {vector_store_id} response over the {response}

    #         Correct the values if any, but donot disturb the format the value is passed on.

    #         If {context} is not given or is not suitable for validation, send the response back.

    #         If there is an error, the response will be given as it is with JSON formatting. JSON formatting is MUST.

    #         No conversational response is needed. Just format the output as the response is given.

    #         If context is unavailable or not valid, send back the {response}.
    #         The end response should be:

    #      {
    #         response: {response}
    #     }

    #       """

    #     assistant = self.client.beta.assistants.create(
    #         name="Responses Validation Assistant",
    #         model="gpt-4o",
    #         instructions=instruction,
    #         tools=[{"type": "file_search"}],
    #         tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
    #         temperature=0.6,
    #     )
    #     print("Validation Assistant Created")
    #     return assistant.id, vector_store_id

    # async def run_response_validation_bot(
    #     self,
    #     Company_Name: str,
    #     response_name: str,
    #     response: dict,
    #     context: str,
    #     vector_store_id: str,
    # ):
    #     assistant_id, vector_store_id = self.response_validation_assistant(
    #         response, context, vector_store_id
    #     )

    #     thread = self.client.beta.threads.create(
    #         messages=[
    #             {
    #                 "role": "user",
    #                 "content": f"{Company_Name}'s {response_name} Validation",
    #             }
    #         ],
    #     )

    #     run = self.client.beta.threads.runs.create_and_poll(
    #         thread_id=thread.id, assistant_id=assistant_id
    #     )

    #     messages = self.client.beta.threads.messages.list(
    #         thread_id=thread.id, run_id=run.id
    #     )

    #     response_message = next(
    #         (msg for msg in messages if msg.role == "assistant"), None
    #     )
    #     if response_message:
    #         response_content = response_message.content[0].text.value
    #         return response_content, vector_store_id
    #     return None

    def response_validation_assistant(self, response, context, vector_store_id):
        instruction = f"""
        You will receive a JSON response and {context}. You need to validate the response and provide feedback on the accuracy of the response.
        The final response must follow the exact same formats in terms of keys and instances as received. The only thing you need to check is that the information is 
        validated by the vector store accessed by {vector_store_id}.
        
        Cross check the information sent in the response to the information saved in {vector_store_id}.

        Prioritize {vector_store_id} response over the provided {response}.

        Correct the values if any, but do not disturb the format the value is passed on.

        If {context} is not given or is not suitable for validation, send the response back. 
        
        If there is an error, the response will be given as it is with JSON formatting. JSON formatting is MUST and make sure the json response is not in nested form just use the "{" as start and add all the key values here and then  end with "}".
        
        No conversational response is needed. Just format the output as a JSON formatted resposne.
        
        If context is unavailable or not valid, send back the JSON FOrmatted response with just the validation from the "File_Search" Tool .
    
      
        """

        assistant = self.client.beta.assistants.create(
            name="Responses Validation Assistant",
            model="gpt-4o",
            instructions=instruction,
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
            temperature=0.6,
        )
        print("Validation Assistant Created")
        return assistant.id, vector_store_id

    async def run_response_validation_bot(
        self,
        Company_Name: str,
        response_name: str,
        response: dict,
        context: str,
        vector_store_id: str,
    ):
        assistant_id, vector_store_id = self.response_validation_assistant(
            json.dumps(response), json.dumps(context), vector_store_id
        )

        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{Company_Name}'s {response_name} Validation",
                }
            ],
        )

        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )

        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id, run_id=run.id
        )

        response_message = next(
            (msg for msg in messages if msg.role == "assistant"), None
        )
        if response_message:
            response_content = response_message.content[0].text.value
            return response_content, vector_store_id
        return None
