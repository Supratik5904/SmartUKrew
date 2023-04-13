from llama_index import SimpleDirectoryReader, GPTListIndex, readers, GPTSimpleVectorIndex, LLMPredictor, PromptHelper, ServiceContext,download_loader
from langchain import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS
import gradio as gr
import sys
import os
from llama_index.readers.base import BaseReader
from llama_index.readers.schema.base import Document
import json
from typing import List
os.environ["OPENAI_API_KEY"] = "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"

class WordpressReader(BaseReader):
    """Wordpress reader. Reads data from a Wordpress workspace.
    Args:
        wordpress_subdomain (str): Wordpress subdomain
    """

    #def __init__(self, url: str, password: str, username: str) -> None:
    def __init__(self, url: str) -> None:
        """Initialize Wordpress reader."""
        self.url = url
        #self.username = username
        #self.password = password
        print("*************************************************",url)

    def load_data(self) -> List[Document]:
        """Load data from the workspace.
        Returns:
            List[Document]: List of documents.
        """
        from bs4 import BeautifulSoup

        results = []

        articles = self.get_all_posts()
        print(len(articles))

        for article in articles:
            body = article.get("content", {}).get("rendered", None)
            if not body:
                body = article.get("content")

            soup = BeautifulSoup(body, "html.parser")
            body = soup.get_text()

            title = article.get("title", {}).get("rendered", None)
            if not title:
                title = article.get("title")

            extra_info = {
                "id": article["id"],
                "title": title,
                "url": article["link"],
                "updated_at": article["modified"],
            }

            results.append(
                Document(
                    body,
                    extra_info=extra_info,
                )
            )
        return results

    def get_all_posts(self):
        posts = []
        next_page = 1

        while True:
            response = self.get_posts_page(next_page)
            posts.extend(response["articles"])
            next_page = response["next_page"]

            if next_page is None:
                break

        return posts

    def get_posts_page(self, current_page: int = 1):
        import requests

        url = f"{self.url}/wp-json/wp/v2/posts?per_page=100&page={current_page}"
        #url = f"{self.url}"
        print("**********************",url)
        HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        }

        response = requests.get(url, verify=False,headers=HEADERS)
        headers = response.headers

        if "X-WP-TotalPages" in headers:
            num_pages = int(headers["X-WP-TotalPages"])
        else:
            num_pages = 1

        if num_pages > current_page:
            next_page = current_page + 1
        else:
            next_page = None
            
        #jsonD = json.dumps(response.text)
        
        
        
        response_json = json.loads(response.text)

        articles = response_json

        return {"articles": articles, "next_page": next_page}

def construct_index(directory_path):
    max_input_size = 4096
    num_outputs = 2048
    max_chunk_overlap = 20
    chunk_size_limit = 600

    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)

    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.7, model_name="text-davinci-003", max_tokens=num_outputs))

    documents1 = SimpleDirectoryReader(directory_path).load_data()
    loader = WordpressReader(url="https://academyselfdefense.com")
    documents2=loader.load_data();
    documents = documents1 + documents2
   
        
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, prompt_helper=prompt_helper)
    index = GPTSimpleVectorIndex.from_documents(documents, service_context=service_context)

    index.save_to_disk('index.json')

    return index

def chatbot(input_text):
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    response = index.query(input_text, response_mode="compact")
    return response.response


app = Flask(__name__)
cors = CORS(app)

@app.route("/chat", methods=["POST"])
def chat():
    message = request.form["message"]
    response = chatbot(message)
    messageResponse = jsonify({"message": response})
    messageResponse.headers.add('Access-Control-Allow-Origin', '*')
    return messageResponse


if __name__ == "__main__":
    index = construct_index('Documents')
    app.run(debug=True)
