from langchain_openai import AzureOpenAIEmbeddings
from config import OPENAI_API_KEY, OPENAI_API_VERSION, EMBEDDING_DEPLOYMENT, AZURE_ENDPOINT


class Embeddings:
    def __init__(self) -> None:
        self.client = AzureOpenAIEmbeddings(
            azure_endpoint=AZURE_ENDPOINT,
            openai_api_key=OPENAI_API_KEY,
            openai_api_version=OPENAI_API_VERSION,
            azure_deployment=EMBEDDING_DEPLOYMENT,
            dimensions=1536,
            max_retries=2,
        )

    def embed(self, text: str) -> list[float]:
        print("Text to embed:", text)
        print(f""" ${AZURE_ENDPOINT} ${OPENAI_API_KEY} ${OPENAI_API_VERSION} ${EMBEDDING_DEPLOYMENT} """)
        return self.client.embed_query(text)