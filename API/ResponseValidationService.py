import openai
import uuid
from LangSmithRunManager import LangSmithRunManager

class ResponseValidationService:
    def __init__(self):
        self.logger = LangSmithRunManager()

    def validate_response(self, response_text: str, original_query: str, transaction_id) -> dict:
        run_id = str(uuid.uuid4())
        self.logger.post_run(
            {"response_text": response_text, "original_query": original_query},
            f"ResponseValidationService {transaction_id}", run_id, parent_run_id=transaction_id
        )

        try:
            # Check for harmful or biased content in the response
            client = openai.OpenAI()
            moderation_result = client.moderations.create(
                model="omni-moderation-latest",
                input=response_text,
            )
            results = moderation_result.results[0]
            categories = results.categories
            flagged_categories = {category: flagged for category, flagged in categories.__dict__.items() if flagged}

            is_harmful = bool(flagged_categories)

            self.logger.patch_run(
                run_id=run_id,
                output={
                    "is_harmful": is_harmful,
                    "flagged_categories": flagged_categories
                }
            )
            return {
                "is_harmful": is_harmful,
                "flagged_categories": flagged_categories
            }

        except Exception as e:
            #raise HTTPException(status_code=500, detail=f"Response validation service error: {str(e)}")
            self.logger.patch_run(
                run_id=run_id,
                output={
                    "is_harmful": None,
                    "flagged_categories": None
                }
            )
            return {
                "is_harmful": None,
                "flagged_categories": None
            }