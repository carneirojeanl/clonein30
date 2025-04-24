from fastapi import APIRouter
from fastapi import File, Form, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Annotated
from backend.users.routers import get_current_user
from backend.users.services import user_has_credits, user_is_admin, decrease_credits_for_free_users

import httpx
import os
from enum import Enum
from dotenv import load_dotenv
from backend.users.routers import get_current_user

load_dotenv()

API_KEY = os.getenv("API_KEY")

user_dependency = Depends(get_current_user)

cloneTTS_router = APIRouter(dependencies=[user_dependency])


class TTSModel(str, Enum):
    speech_15 = "speech-1.5"
    speech_16 = "speech-1.6"
    agent_x0 = "agent-x0"


async def get_models(user: Annotated[dict, user_dependency]):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            models = {}
            response = await client.get(
                "https://api.fish.audio/model", 
                params={"tag": user["username"], "self": True},
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
            items = response.json()["items"]
            for item in items:
                models[f"{item['_id']}"] = item['title']
            return models
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"External API error: {e}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")

@cloneTTS_router.get("/list-models", tags=["List models"])
async def list_models(models = Depends(get_models)):
    return models

@cloneTTS_router.post("/create-model", tags=["Clone TTS"])
async def create_model(
    user: Annotated[dict, user_dependency],
    voice: UploadFile = File(),
    title: str = Form("My model title"),
    description: str = Form(""),
    enhance_audio_quality: bool = Form(True),
):  
    user_credits = user_has_credits(user["username"])

    is_admin = user_is_admin(user["username"])

    if not user_credits and not is_admin:
        raise HTTPException(status_code=400, detail="You don't have enough credits to create a model")
    try:

        # Prepare voice file to send as the voice to be cloned
        voice_content = await voice.read()

        files = {
            "voices": (voice.filename, voice_content, voice.content_type),
        }


        # Prepare data
        data = {
            "visibility": "private",
            "type": "tts",
            "title": title,
            "description": description,
            "train_mode": "fast",
            "tags": user["username"]
        }

        if enhance_audio_quality:
            data["enhance_audio_quality"] = "true"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.fish.audio/model",
                files=files,
                data=data,
                headers={
                    "Authorization": f"Bearer {API_KEY}"
                }
            )
        
            # Check if the request was successful
            response.raise_for_status()

            if not is_admin:
                decrease_credits_for_free_users(user["username"])
            
            return response.json()

    except httpx.HTTPStatusError as e:
        # Handle HTTP errors from the Fish Audio API
        return JSONResponse(
            status_code=e.response.status_code,
            content={"detail": f"Error from Fish Audio API: {e.response.text}"}
        )
    except httpx.RequestError as e:
        # Handle network/connection errors
        return JSONResponse(
            status_code=500,
            content={"detail": f"Request error: {str(e)}"}
        )
    except Exception as e:
        # Handle any other errors
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error processing request: {str(e)}"}
        )

@cloneTTS_router.post("/text-to-speech", tags=["Clone TTS"])
async def text_to_speech(user: Annotated[dict, user_dependency], text: str, reference_id: str, ttsModel: TTSModel = TTSModel.agent_x0):

    user_credits = user_has_credits(user["username"])

    is_admin = user_is_admin(user["username"])

    if not user_credits and not is_admin:
        raise HTTPException(status_code=400, detail="You don't have enough credits to use TTS")
    
    try:
        body = {
            "text": text,
            "reference_id": reference_id,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "model": ttsModel,
            }
            response = await client.post(
                "https://api.fish.audio/v1/tts",
                json=body,
                headers=headers
            )
            content_type = response.headers.get(
                "Content-Type", 
                "audio/wav"
            )

            if not is_admin:
                decrease_credits_for_free_users(user["username"])

            return StreamingResponse(
                content=response.iter_bytes(),
                media_type=content_type,
                headers={
                    "Content-Disposition": "attachment; filename=tts_output.wav"
                }
            )

    except httpx.HTTPStatusError as e: 
        return JSONResponse(
            status_code=e.response.status_code,
            content={"detail": f"Error from Fish Audio API: {e.response.text}"}
        )
    except httpx.RequestError as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Request error: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error processing request: {str(e)}"}
        )

