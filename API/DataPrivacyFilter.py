import hashlib, re
import uuid
from LangSmithRunManager import LangSmithRunManager

class DataPrivacyFilter:
    def __init__(self):
        self.token_map = {}
        self.logger = LangSmithRunManager()

    def _generate_token(self, sensitive_data: str) -> str:
        return f"<TOKEN_{hashlib.sha1(sensitive_data.encode()).hexdigest()}>"

    def mask_sensitive_data(self, text: str, transaction_id) -> str:

        run_id = str(uuid.uuid4())
        self.logger.post_run(
            {"text to mask": text},
            f"DataPrivacyFilter Mask {transaction_id}", run_id, parent_run_id=transaction_id
        )

        patterns = {
            'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
            'Credit Card': r'\b\d{4}-\d{4}-\d{4}-\d{4}\b',
            'Bank Account': r'\b\d{9,18}\b'
        }

        for key, pattern in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                sensitive_data = match.group()
                token = self._generate_token(sensitive_data)
                self.token_map[token] = sensitive_data
                text = text.replace(sensitive_data, token)

        self.logger.patch_run(
            run_id=run_id,
            output={"masked text": text}
        )

        return text

    def unmask_sensitive_data(self, text: str, transaction_id) -> str:
        run_id = str(uuid.uuid4())
        self.logger.post_run(
            {"text to unmask": text},
            f"DataPrivacyFilter Unmask {transaction_id}", run_id, parent_run_id=transaction_id
        )

        for token, sensitive_data in self.token_map.items():
            text = text.replace(token, sensitive_data)

        self.logger.patch_run(
            run_id=run_id,
            output={"unmasked text": text}
        )
        return text