from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import asyncio
import logging

# Set up basic logging config
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/idle={idle}")
async def idel(idle: int, request: Request):
    logger.info(f"Received request from {request.client.host} with idle={idle}")

    if idle < 0 or idle > 600:
        logger.warning("Invalid idle received")
        raise HTTPException(status_code=400, detail="Idle must be between 0 and 600 seconds")

    logger.debug(f"Sleeping for {idle} seconds")
    await asyncio.sleep(idle)
    logger.info(f"Returning response after sleeping {idle} seconds")

    return JSONResponse(content={"message": f"Waited for {idle} seconds"}, status_code=200)

