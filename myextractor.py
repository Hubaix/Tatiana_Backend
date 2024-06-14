import os
import json
import requests
from dotenv import load_dotenv
import wikipedia
import urllib.parse
import pandas as pd
from openai import OpenAI
import numpy as np

class KnowledgeExtraction:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.temp_dir = "temp"

    async def insert_files_into_vector_store(self, filename:str, company_name:str, vs_id:str):
        filename = f"{self.temp_dir}/{company_name}_linkedin.txt"
        file_paths = [filename]
        file_streams = []
        try:
            for path in file_paths:
                file_streams.append(open(path, "rb"))
            file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vs_id, files=file_streams
            )
            # print("File batch status:", file_batch.status)
            # print("File counts:", file_batch.file_counts)
        except Exception as e:
            print(f"Error occurred while uploading file: {e}")
        finally:
            for stream in file_streams:
                stream.close()
 
    async def linkedin_scrape(self, company_name: str, linkedin_url: str, vs_id: str):
            headers = {'Authorization': 'Bearer mDt5FpcupcX03A5qdJ5miw'}
            api_endpoint = 'https://nubela.co/proxycurl/api/linkedin/company'
            params = {
                'url': linkedin_url,
                'resolve_numeric_id': 'true',
                'categories': 'include',
                'funding_data': 'include',
                'exit_data': 'include',
                'acquisitions': 'include',
                'extra': 'include',
                'use_cache': 'if-present',
                'fallback_to_cache': 'on-error',
            }
            response = requests.get(api_endpoint, params=params, headers=headers)
            if response.status_code == 200:
                company_data = response.json()
                extracted_data = {
                    "Description": company_data.get('description'),
                    "Website": company_data.get("website"),
                    "Industry": company_data.get('industry'),
                    "Company Size": company_data.get('company_size'),
                    "Company Size on Linkedin": company_data.get('company_size_on_linkedin'),
                    "Head Quarters": company_data.get('hq'),
                    "Company Type": company_data.get('company_type'),
                    "Founded Year": company_data.get('founded_year'),
                    "Specialities": company_data.get('specialities'),
                    "Name": company_data.get('name'),
                    "Universal Name ID": company_data.get('universal_name_id'),
                    "Profile Pic URL": company_data.get('profile_pic_url'),
                    "Background Cover Image URL": company_data.get('background_cover_image_url'),
                    "Search ID": company_data.get('search_id'),
                    "Affiliated Companies": company_data.get('affiliated_companies'),
                    "Updates": company_data.get('updates'),
                    "Follower Count": company_data.get('follower_count'),
                    "Acquisitions": company_data.get('acquisitions'),
                    "exit_data": company_data.get('exit_data'),
                    "extra": company_data.get('extra'),
                    "Funding Data": company_data.get('funding_data'),
                    "Categories": company_data.get('categories'),
                    "Customer List": company_data.get('customer_list'),
                }
                filename = f"{self.temp_dir}/{company_name}_linkedin.txt"
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(json.dumps(extracted_data, indent=4))
                
                print(f"Company profile data saved to {filename}")
                self.insert_files_into_vector_store(filename, company_name, vs_id)
                return extracted_data, filename  # Return the filename at the end
            else:
                print(f"Failed to retrieve company data. Status code: {response.status_code}")
                return None  # Return None if the request fails
      
    async def extract_text_from_files(self, uploaded_files: list, vs_id: str):
        extracted_data = []
        
        for file_path in uploaded_files:
            try:
                with open(file_path, "rb") as f:
                    file_content = f.read()
                    
                    # Assuming self.client.beta.tools.extract sends file_content and returns extracted data
                    response = await self.client.beta.tools.extract(file=file_content)
                    
                    # Optionally, you can append additional metadata if needed
                    return response
            except Exception as e:
                print(f"Error occurred while extracting text from file {file_path}: {e}")
        
        return extracted_data

    async def save_extracted_text_to_vs(self, company_name: str, extracted_data: list, vs_id: str):
        for data in extracted_data:
            try:
                text = data['document']
                filename = f"{self.temp_dir}/{company_name}_extracted_text.txt"
                with open(filename, 'w', encoding='utf-8') as file:
                    file.write(text)
                self.insert_files_into_vector_store(filename, company_name, vs_id)
                print(f"Extracted text saved to {filename}")
            except Exception as e:
                print(f"Error occurred while saving extracted text to Vector store: {e}")

    async def insert_wikipedia_files_into_vector_store(self, file_path:str, vs_id:str):
        try:
            with open(file_path, "rb") as f:
                batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vs_id, files=[f]
                )
                # print("File batch status:", batch.status)
                # print("File counts:", batch.file_counts)
        except Exception as e:
            print(f"Error occurred while uploading file to Vector store: {e}")
 
    async def fetch_wikipedia_data(self, company_name: str, url: str, vs_id: str):
        # Decode the URL to get the proper page title
        page_title = urllib.parse.unquote(url.split('/')[-1])

        while True:
            try:
                page = wikipedia.page(page_title, auto_suggest=False, redirect=True, preload=False)
                content = page.content
                references = page.references
                break
            except wikipedia.exceptions.DisambiguationError as e:
                page_title = e.options[0]
            except wikipedia.exceptions.PageError:
                return None

        try:
            tables = pd.read_html(url)
        except ValueError:
            tables = []

        # Convert tables to a list of dictionaries, ensuring keys are strings and handling NaN values
        tables_as_dict = []
        for table in tables:
            # Replace NaN values with None
            table = table.replace({np.nan: None})
            table_dict = table.to_dict(orient='records')
            cleaned_table_dict = []
            for row in table_dict:
                cleaned_row = {str(k): v for k, v in row.items()}
                cleaned_table_dict.append(cleaned_row)
            tables_as_dict.append(cleaned_table_dict)

        # Create a dictionary to hold the scraped data
        data = {
            "Title": page.title,
            "Content": content,
            "References": references,
            "Tables": tables_as_dict
        }

        # Define the file path
        file_path = f"{self.temp_dir}/{company_name}_wikipedia.json"

        # Save the data to a JSON file
        with open(file_path, "w", encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

        print(f"Data has been saved to the JSON file: {file_path}")

        return data, file_path

    async def files_input(self, uploaded_files :list, company_name:str, vs_id:str):
        for file in uploaded_files:
            self.insert_files_into_vector_store(file, company_name, vs_id,)
            print("Files uploaded successfully.")
        return vs_id

    async def capture_doc(self, doc_path:str, vs_id:str):
        try:
            if doc_path.lower().endswith('.docx') or doc_path.lower().endswith('.txt'):
                if not os.path.exists(doc_path):
                    print(f"Error: The file '{doc_path}' does not exist.")
                    return
                self.insert_docs_vector_store(doc_path, vs_id)
                print(f"Document '{doc_path}' inserted into vector store.")
            else:
                print("Error: The provided file is neither a .docx nor a .txt file.")
        except Exception as e:
            print(f"Error occurred while inserting document: {e}")

    async def capture_meeting_notes(self, Company_Name:str, meeting_notes:str, vs_id:str):
        filename = f"{self.temp_dir}/{Company_Name}_MeetingNotes.txt"
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(meeting_notes)
        print(f"Company Meeting Notes saved to {filename}")
        self.insert_meeting_notes_into_vector_store(filename, vs_id)
        return filename, vs_id