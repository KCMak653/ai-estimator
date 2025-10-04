from openai import OpenAI
import logging

# TODO make agnostic to model

logger = logging.getLogger(__name__)

class ModelIO:
    def __init__(self, company_name, model, prompt = None):
        """ 
        Authenicate
        """
        
        self.company_name = company_name
        self.model = model
        self.client = self.authenticate()
        self.prompt = prompt


    def authenticate(self):
        """
        Authenticate the user.
        """
        # Implement authentication logic here
        try: # Only show first 5 chars for security
            client = OpenAI()
            return client
        except Exception as e:
            logger.error(f"Error initializing OpenAI client. Is OPENAI_API_KEY set? Error: {e}")
            exit()


    def get_response(self, input):
        """
        Send a chat completion request to the model.
        """
        # messages = [prompt, {"role": "user", "content": message}] if self.prompt else [{"role": "user", "content": message}]
        try:
            response = self.client.responses.create(
                model = self.model,
                instructions = self.prompt,
                input  = input)
            return response.output_text
            # response = self.client.chat.completions.create(
            #     model=self.model_name,
            #     messages=messages,
            # )
            # return response.choices[0].message['content']
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return None