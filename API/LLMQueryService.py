from fastapi import FastAPI, Query, HTTPException, Body
import time

from ModerationService import ModerationService
from RetrieverService import RetrieverService
from LLMService import LLMService
from DataPrivacyFilter import DataPrivacyFilter
from ResponseValidationService import ResponseValidationService
from LangSmithRunManager import LangSmithRunManager

import uuid
class LLMQueryService:
    def __init__(self):
        self.app = FastAPI(title="LLM Query Service",
                           description="API for querying an LLM and retrieving response metrics.",
                           version="1.0.0")

        self.llm_service = LLMService()
        self.moderation_service = ModerationService()
        self.retriever_service = RetrieverService()
        self.data_privacy_filter = DataPrivacyFilter()
        self.response_validation_service = ResponseValidationService()
        self.logger = LangSmithRunManager()
        #self.app.get("/query")(self.get_llm_response)
        self.app.post("/query")(self.get_llm_response)



    async def get_llm_response(self,
                               request_body: dict = Body(..., description="Request body containing query details.")):
        try:
            query = request_body.get("query")
            data_domain = request_body.get("data_domain", "")
            llm_name = request_body.get("llm_name")
            version = request_body.get("version")
            transaction_id = request_body.get("transaction_id", "")

            if not transaction_id:
                transaction_id = str(uuid.uuid4())
            start_time = time.time()

            # Start LangSmith run
            self.logger.post_run(
                {"query": query, "data_domain": data_domain, "llm_name": llm_name, "version": version,
                 "transaction_id": transaction_id},
                f"LLM Ecosystem Run {transaction_id}", transaction_id, parent_run_id=None
            )

            # Run moderation on the input query
            moderation_result = self.moderation_service.moderate_content(query, transaction_id)

            # Check moderation result
            if moderation_result["safety_score"] < 1 or moderation_result["bias_score"] > 0.1:
                response_text = f"Unsafe query: '{query}' for LLM '{llm_name}' version '{version}'"
                response_usage_metadata = ""
                validation_result = ""

            else:
                # Retrieve context from Pinecone using the retriever
                if data_domain:
                    context = self.retriever_service.retrieve_context(query, data_domain, transaction_id)
                    query = f"Answer this question '''{query}''' with the following context: " + context

                # Apply Data Privacy Filter to mask sensitive data
                masked_query = self.data_privacy_filter.mask_sensitive_data(context or query, transaction_id)

                # Get LLM from LLMService
                llm = self.llm_service.get_llm(llm_name, version)
                if llm:
                    # Run the query using the LLM (adjusted for chat models if applicable)
                    response = llm.invoke(masked_query)
                    response_text = self.data_privacy_filter.unmask_sensitive_data(response.content, transaction_id)
                    response_usage_metadata = response.usage_metadata
                else:
                    response_text = f"No matching LLM found for '{llm_name}' version '{version}'"

                # Validate the response for relevance and harmful content
                validation_result = self.response_validation_service.validate_response(response_text, query,
                                                                                       transaction_id)
                if validation_result["is_harmful"]:
                    response_text = f"Warning: The generated response may contain harmful or biased content. Flagged categories: {validation_result['flagged_categories']}"

            time_taken = f"{time.time() - start_time:.2f} seconds"

            self.logger.patch_run(
                run_id=transaction_id,
                output={
                    "response": response_text,
                    "usage_metadata": response_usage_metadata,
                    "time_taken": time_taken,
                    "llm_used": f"{llm_name} v{version}",
                    "safety_score": moderation_result["safety_score"],
                    "bias_score": moderation_result["bias_score"],
                    "feedback": moderation_result["feedback"],
                    "validation_result": validation_result
                }
            )

            return {
                "response": response_text,
                "usage_metadata": response_usage_metadata,
                "time_taken": time_taken,
                "llm_used": f"{llm_name} v{version}",
                "safety_score": moderation_result["safety_score"],
                "bias_score": moderation_result["bias_score"],
                "feedback": moderation_result["feedback"],
                "validation_result": validation_result
            }
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e))

service = LLMQueryService()
app = service.app
