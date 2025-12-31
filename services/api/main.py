from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid
import time

from logic.llm import createGroqClient, generateManimCode
from logic.sanitizer import sanitizeCode
from logic.renderer import renderCode

