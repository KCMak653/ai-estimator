from llm_io.model_io import ModelIO

if __name__ == "__main__":
    print("This is the main module.")
    model = ModelIO("openai", "gpt-3.5-turbo")
    print(model.get_response("how are you?"))