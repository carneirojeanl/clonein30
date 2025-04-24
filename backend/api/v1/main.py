from fastapi import FastAPI

from backend.users.routers import users_router
from backend.cloneTTS.routers import cloneTTS_router

tags_metadata = [
        {
        "name": "Authentication",
        "description": "Create an account and use it to authenticate.",
    },
    {
        "name": "Clone TTS",
        "description": "Create a model based on any voice you want and use this voice to use the TTS functionality.",
    },
        {
        "name": "List models",
        "description": "List the models already created by you.",
    },

]

description = """
Voice clone and TTS 🚀

## Instructions to use the API:

**1. Create an account** using the endpoint **/users/signup/**.

**2. Authenticate** using the **Authorize** button. Use the same credentials you used to sign up.

**3. Create a model** using the **/create-model/** endpoint. You will need to upload the base voice you want to clone. Your audio file 
should be longer than 30 seconds and shorter than 3 minutes. Once your model is created, you will receive the model ID in the response. 
Make sure to copy it, as you’ll need it to use the TTS functionality.

**4. Convert text to speech** by using the endpoint **/text-to-speech/**. You will need to provide the text you want to convert and the ID of the model you created.
If you forgot your model ID, you can use the **/list-models/** endpoint to retrieve it.

**5. Credits:** This API is in BETA, so each user will have 4 credits to use. This means every time you use the **/create-model/** or **/text-to-speech/** endpoints, you will consume 1 credit.
Once you run out of credits, you will no longer be able to create models or convert text to speech.
"""

contact = {
    "name": "Jean Carneiro",
    "email": "jeanldcarneiro@gmail.com",
    "url": "https://www.linkedin.com/in/jeanldcarneiro/"
}


app = FastAPI(title="Clone em 30 - Beta", description=description, 
              contact=contact,
              openapi_tags=tags_metadata)

app.include_router(users_router, prefix="/api/v1/users")
app.include_router(cloneTTS_router, prefix="/api/v1/clone-tts")

