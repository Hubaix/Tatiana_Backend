from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
import os
import logging
import json

from myextractor import KnowledgeExtraction
from myassistant import KnowledgeAssistant
from models import CompanyInfo

app = FastAPI()
app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allows all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allows all methods
        allow_headers=["*"],  # Allows all headers
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Instance of your classes
extractor = KnowledgeExtraction()
assistant = KnowledgeAssistant()  # Pass the client to KnowledgeAssistant


async def handle_file_upload(files: List[UploadFile]) -> List[str]:
    file_names = []
    upload_folder = "uploads/"
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    for file in files:
        file_path = os.path.join(upload_folder, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        file_names.append(file_path)
    return file_names


    # @app.post("/run-extractors/")
    # async def fetch_company_info(
    #     context: Optional[str] = Form(None),
    #     company_name: str = Form(...),
    #     website: str = Form(...),
    #     wikipedia_link: str = Form(...),
    #     linkedin_url: str = Form(...),
    #     files: List[UploadFile] = File([]),
    # ):
    #     try:
    #         uploaded_files = await handle_file_upload(files)
    #         company_info = {
    #             "context": context,
    #             "company_name": company_name,
    #             "website": website,
    #             "wikipedia_link": wikipedia_link,
    #             "linkedin_url": linkedin_url,
    #             "uploaded_files": uploaded_files,
    #         }
    #         logger.info(f"Company Info: {company_info}")

    #         vs_id = await assistant.run_chatbot(
    #             company_info["website"],
    #             company_info["company_name"],
    #             company_info["uploaded_files"],
    #         )
    #         logger.info(f"Vector Store ID: {vs_id}")

    #         linkedin_response = await extractor.linkedin_scrape(
    #             company_info["company_name"], company_info["linkedin_url"], vs_id
    #         )
    #         wikipedia_response = await extractor.fetch_wikipedia_data(
    #             company_info["company_name"], company_info["wikipedia_link"], vs_id
    #         )

    #         response_data = {
    #             "LinkedIn Response": linkedin_response,
    #             "Wikipedia Response": wikipedia_response,
    #         }

    #         v_response = await assistant.run_response_validation_bot(
    #             company_info["company_name"],
    #             "extraction",
    #             response_data,
    #             company_info["context"],
    #             vs_id,
    #         )

    #         return JSONResponse(content=v_response, status_code=200)
    #     except Exception as e:
    #         logger.error(f"Error occurred: {e}", exc_info=True)
    #         raise HTTPException(status_code=500, detail=str(e))

@app.post("/run-extractors/")
async def fetch_company_info(
    context: Optional[str] = Form(None),
    company_name: str = Form(...),
    website: str = Form(...),
    wikipedia_link: str = Form(...),
    linkedin_url: str = Form(...),
    meeting_notes: Optional[str] = Form(None),
    files: List[UploadFile] = File([]),
):
    try:
        uploaded_files = await handle_file_upload(files)
        company_info = {
            "context": context,
            "company_name": company_name,
            "website": website,
            "wikipedia_link": wikipedia_link,
            "linkedin_url": linkedin_url,
            "meeting_notes": meeting_notes,
            "uploaded_files": uploaded_files,
        }
        logger.info(f"Company Info: {company_info}")

        vs_id = await assistant.run_chatbot(
            company_info["website"],
            company_info["company_name"]
           
        )
        logger.info(f"Vector Store ID: {vs_id}")

        linkedin_response = await extractor.linkedin_scrape(
            company_info["company_name"], company_info["linkedin_url"], vs_id
        )
        wikipedia_response = await extractor.fetch_wikipedia_data(
            company_info["company_name"], company_info["wikipedia_link"], vs_id
        )

        response_data = {
            "LinkedIn Response": linkedin_response,
            "Wikipedia Response": wikipedia_response,
        }

        v_response, vs_id = await assistant.run_response_validation_bot(
            company_info["company_name"],
            "extraction",
            response_data,
            company_info["context"],
            vs_id,
        )

        return JSONResponse(content=v_response, status_code=200)
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/financial_overview/")
async def financial_overview(
    context: Optional[str] = Form(None),
    company_name: str = Form(...),
    website: str = Form(...),
    wikipedia_link: str = Form(...),
    linkedin_url: str = Form(...),
    meeting_notes: Optional[str] = Form(None),
    files: List[UploadFile] = File([]),
):
    try:
        uploaded_files = await handle_file_upload(files)
        company_info = {
            "context": context,
            "company_name": company_name,
            "website": website,
            "wikipedia_link": wikipedia_link,
            "linkedin_url": linkedin_url,
            "meeting_notes": meeting_notes,
            "uploaded_files": uploaded_files,
        }
        logger.info(f"Company Info: {company_info}")

        vs_id = await assistant.run_chatbot(
            company_info["website"],
            company_info["company_name"]
           
        )
        logger.info(f"Vector Store ID: {vs_id}")

    
        # Run the financial bot asynchronously
        financial_overview, vs_id = await assistant.run_finance_bot(
            company_info["company_name"], vs_id
        )

        # Verify and Validae the response from Validation Bot
        v_financial_overview, vs_id= await assistant.run_response_validation_bot(company_info["company_name"], "financial_overview", financial_overview, company_info["context"], vs_id)
        return JSONResponse(content=v_financial_overview, status_code=200)

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/company_overview/")
async def company_overview(
   context: Optional[str] = Form(None),
    company_name: str = Form(...),
    website: str = Form(...),
    wikipedia_link: str = Form(...),
    linkedin_url: str = Form(...),
    meeting_notes: Optional[str] = Form(None),
    files: List[UploadFile] = File([]),
):
    try:
        uploaded_files = await handle_file_upload(files)
        company_info = {
            "context": context,
            "company_name": company_name,
            "website": website,
            "wikipedia_link": wikipedia_link,
            "linkedin_url": linkedin_url,
            "meeting_notes": meeting_notes,
            "uploaded_files": uploaded_files,
        }
        logger.info(f"Company Info: {company_info}")

        vs_id = await assistant.run_chatbot(
            company_info["website"],
            company_info["company_name"]
           
        )
        logger.info(f"Vector Store ID: {vs_id}")

    
        # Run company overview bot asynchronously
        company_overview, vs_id = await assistant.run_company_overview_bot(
            company_info["website"], vs_id
        )

        # Verify and Validae the response from Validation Bot
        v_company_overview, vs_id= await assistant.run_response_validation_bot(company_info["company_name"], "company_overview", company_overview, company_info["context"], vs_id)

        return JSONResponse(content=v_company_overview, status_code=200)

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/leadership_overview/")
async def leadership_overview(
    context: Optional[str] = Form(None),
    company_name: str = Form(...),
    website: str = Form(...),
    wikipedia_link: str = Form(...),
    linkedin_url: str = Form(...),
    meeting_notes: Optional[str] = Form(None),
    files: List[UploadFile] = File([]),
):
    try:
        uploaded_files = await handle_file_upload(files)
        company_info = {
            "context": context,
            "company_name": company_name,
            "website": website,
            "wikipedia_link": wikipedia_link,
            "linkedin_url": linkedin_url,
            "meeting_notes": meeting_notes,
            "uploaded_files": uploaded_files,
        }
        logger.info(f"Company Info: {company_info}")

        vs_id = await assistant.run_chatbot(
            company_info["website"],
            company_info["company_name"]
           
        )
        logger.info(f"Vector Store ID: {vs_id}")

    

        # Run leadership overview bot asynchronously
        leadership_overview, vs_id = await assistant.run_leadership_overview_bot(
            company_info["company_name"], vs_id
        )

        # Verify and Validae the response from Validation Bot
        v_leadership_overview, vs_id= await assistant.run_response_validation_bot(company_info["company_name"], "leadership_overview", leadership_overview, company_info["context"], vs_id)
        return JSONResponse(content=v_leadership_overview, status_code=200)

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/products_and_services/")
async def products_and_services(
    context: Optional[str] = Form(None),
    company_name: str = Form(...),
    website: str = Form(...),
    wikipedia_link: str = Form(...),
    linkedin_url: str = Form(...),
    meeting_notes: Optional[str] = Form(None),
    files: List[UploadFile] = File([]),
):
    try:
        uploaded_files = await handle_file_upload(files)
        company_info = {
            "context": context,
            "company_name": company_name,
            "website": website,
            "wikipedia_link": wikipedia_link,
            "linkedin_url": linkedin_url,
            "meeting_notes": meeting_notes,
            "uploaded_files": uploaded_files,
        }
        logger.info(f"Company Info: {company_info}")
        
        print(f"\n\n COMPANY INFO : {company_info} \n\n")
        print(f"\n\n COMPANY INFO : {company_info['company_name']} \n \n")

        vs_id = await assistant.run_chatbot(
            company_info["website"],
            company_info["company_name"]
           
        )
        logger.info(f"Vector Store ID: {vs_id}")

    
        # Run products and services bot asynchronously
        products_and_services, vs_id = await assistant.run_product_and_services_bot(
            company_info["company_name"], vs_id
        )

        # Verify and Validae the response from Validation Bot
        v_products_and_services, vs_id= await assistant.run_response_validation_bot(company_info["company_name"], "products_and_services", products_and_services, company_info["context"], vs_id)
        return JSONResponse(content=v_products_and_services, status_code=200)

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/market_segmentation/")
async def market_segmentation(
   context: Optional[str] = Form(None),
    company_name: str = Form(...),
    website: str = Form(...),
    wikipedia_link: str = Form(...),
    linkedin_url: str = Form(...),
    meeting_notes: Optional[str] = Form(None),
    files: List[UploadFile] = File([]),
):
    try:
        uploaded_files = await handle_file_upload(files)
        company_info = {
            "context": context,
            "company_name": company_name,
            "website": website,
            "wikipedia_link": wikipedia_link,
            "linkedin_url": linkedin_url,
            "meeting_notes": meeting_notes,
            "uploaded_files": uploaded_files,
        }
        logger.info(f"Company Info: {company_info}")

        print(f"\n\n COMPANY INFO : {company_info} \n\n")
        print(f"\n\n COMPANY INFO : {company_info['company_name']} \n \n")

        vs_id = await assistant.run_chatbot(
            company_info["website"],
            company_info["company_name"]
           
        )
        logger.info(f"Vector Store ID: {vs_id}")

    
        # Run market segmentation bot asynchronously
        market_segmentation, vs_id = await assistant.run_market_segment_bot(
            company_info["company_name"], vs_id
        )

        # Verify and Validae the response from Validation Bot
        v_market_segmentation, vs_id= await assistant.run_response_validation_bot(company_info["company_name"], "market_segmentation", market_segmentation, company_info["context"], vs_id)

        return JSONResponse(content=v_market_segmentation, status_code=200)

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/customer_partner/")
async def customer_partner(
 context: Optional[str] = Form(None),
    company_name: str = Form(...),
    website: str = Form(...),
    wikipedia_link: str = Form(...),
    linkedin_url: str = Form(...),
    meeting_notes: Optional[str] = Form(None),
    files: List[UploadFile] = File([]),
):
    try:
        uploaded_files = await handle_file_upload(files)
        company_info = {
            "context": context,
            "company_name": company_name,
            "website": website,
            "wikipedia_link": wikipedia_link,
            "linkedin_url": linkedin_url,
            "meeting_notes": meeting_notes,
            "uploaded_files": uploaded_files,
        }
        logger.info(f"Company Info: {company_info}")

        vs_id = await assistant.run_chatbot(
            company_info["website"],
            company_info["company_name"]
           
        )
        logger.info(f"Vector Store ID: {vs_id}")

        # Run customer and partner bot asynchronously
        customer_partner, vs_id = await assistant.run_customer_partner_bot(
            company_info["company_name"], vs_id
        )

        # Verify and Validae the response from Validation Bot
        v_customer_partner, vs_id= await assistant.run_response_validation_bot(company_info["company_name"], "customer_partner", customer_partner, company_info["context"], vs_id)

        return JSONResponse(content=v_customer_partner, status_code=200)

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/strategic_fit_overview/")
async def strategic_fit_overview(
    context: Optional[str] = Form(None),
    company_name: str = Form(...),
    website: str = Form(...),
    wikipedia_link: str = Form(...),
    linkedin_url: str = Form(...),
    meeting_notes: Optional[str] = Form(None),
    files: List[UploadFile] = File([]),
):
    try:
        uploaded_files = await handle_file_upload(files)
        company_info = {
            "context": context,
            "company_name": company_name,
            "website": website,
            "wikipedia_link": wikipedia_link,
            "linkedin_url": linkedin_url,
            "meeting_notes": meeting_notes,
            "uploaded_files": uploaded_files,
        }
        logger.info(f"Company Info: {company_info}")

        vs_id = await assistant.run_chatbot(
            company_info["website"],
            company_info["company_name"]
           
        )
        logger.info(f"Vector Store ID: {vs_id}")


        # Run strategic fit bot asynchronously
        strategic_fit, vs_id = await assistant.run_strategic_fit_bot(
            company_info["company_name"], vs_id
        )

        # Verify and Validae the response from Validation Bot
        v_strategic_fit, vs_id= await assistant.run_response_validation_bot(company_info["company_name"], "strategic_fit", strategic_fit, company_info.context, vs_id)
        return JSONResponse(content=v_strategic_fit, status_code=200)

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
