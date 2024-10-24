import openai, uuid
from LangSmithRunManager import LangSmithRunManager

class ModerationService:
    def __init__(self):
        # Initialization can include loading models or setting up configurations if needed
        self.client = openai.OpenAI()
        self.logger = LangSmithRunManager()

    def moderate_content(self, query: str, transaction_id) -> dict:
        try:
            # Start LangSmith run
            run_id = str(uuid.uuid4())
            self.logger.post_run(
                {"query_to_moderate": query},
                f"ModerationService {transaction_id}", run_id, parent_run_id=transaction_id
            )

            response = self.client.moderations.create(
                model="omni-moderation-latest",
                input=query,
            )
            results = response.results[0]
            categories = results.categories
            flagged_categories = {category: flagged for category, flagged in categories.__dict__.items() if flagged}
            total_categories = len(categories.__dict__)
            false_categories = total_categories - len(flagged_categories)
            safety_score = false_categories / total_categories if total_categories > 0 else 1.0

            # Placeholder bias score based on moderation results (you can refine this logic as needed)
            bias_score = 0.1 if flagged_categories else 0.0

            feedback = "Unsafe content detected." if flagged_categories else "Content is safe."

            self.logger.patch_run(
                run_id=run_id,
                output={
                    "safety_score": safety_score,
                    "bias_score": bias_score,
                    "feedback": feedback
                },
            )

            return {
                "safety_score": safety_score,
                "bias_score": bias_score,
                "feedback": feedback
            }

        except Exception as e:
            self.logger.patch_run(
                run_id=run_id,
                output={
                    "safety_score": None,
                    "bias_score": None,
                    "feedback": f"Moderation service error: {str(e)}"
                },
            )
            return {
                "safety_score": None,
                "bias_score": None,
                "feedback": f"Moderation service error: {str(e)}"
            }