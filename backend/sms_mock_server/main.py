"""
SMS Mock Server

A standalone FastAPI application that simulates an SMS provider gateway.
This server receives SMS sending requests and logs them for testing purposes.
"""
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import logging
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SMS Mock Server",
    description="Mock SMS Gateway for testing debtor query system",
    version="1.0.0"
)

# In-memory storage
received_sms: List[dict] = []
webhook_calls: List[dict] = []


class SMSRequest(BaseModel):
    """SMS Send Request Model"""
    phone: str = Field(..., min_length=11, max_length=20, description="Recipient phone number")
    content: str = Field(..., min_length=1, description="SMS content")
    channel_id: Optional[int] = Field(None, description="SMS channel ID")
    task_id: Optional[str] = Field(None, description="SMS task ID")
    callback_url: Optional[str] = Field(None, description="Webhook callback URL")


class SMSResponse(BaseModel):
    """SMS Send Response Model"""
    code: int = Field(200, description="Response code")
    message: str = Field("success", description="Response message")
    msg_id: str = Field(..., description="Provider message ID")
    timestamp: int = Field(..., description="Unix timestamp")


class SMSTestRequest(BaseModel):
    """SMS Channel Test Request Model"""
    phone: str = Field(..., min_length=11, max_length=20)
    channel_id: Optional[int] = None


class SMSCallbackRequest(BaseModel):
    """SMS Delivery Status Callback Model"""
    msg_id: str
    phone: str
    status: str  # delivered, failed, pending
    delivered_at: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "SMS Mock Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "total_sms_received": len(received_sms),
        "total_webhook_calls": len(webhook_calls)
    }


@app.post("/api/send", response_model=SMSResponse)
async def send_sms(request: SMSRequest):
    """
    Send SMS endpoint.
    Simulates receiving an SMS sending request and logs it.
    """
    msg_id = f"MOCK-{uuid.uuid4().hex[:12].upper()}"
    timestamp = int(datetime.utcnow().timestamp())
    
    # Create SMS record
    sms_record = {
        "msg_id": msg_id,
        "phone": request.phone,
        "content": request.content,
        "channel_id": request.channel_id,
        "task_id": request.task_id,
        "callback_url": request.callback_url,
        "received_at": datetime.utcnow().isoformat(),
        "status": "sent"
    }
    
    received_sms.append(sms_record)
    
    logger.info(f"SMS Received - ID: {msg_id}, Phone: {request.phone}, Content: {request.content[:50]}...")
    
    # Simulate webhook callback if callback_url provided
    if request.callback_url:
        webhook_call = {
            "msg_id": msg_id,
            "phone": request.phone,
            "status": "delivered",
            "delivered_at": datetime.utcnow().isoformat(),
            "callback_url": request.callback_url
        }
        webhook_calls.append(webhook_call)
        logger.info(f"Webhook would be called: {request.callback_url}")
    
    return SMSResponse(
        code=200,
        message="success",
        msg_id=msg_id,
        timestamp=timestamp
    )


@app.post("/api/test")
async def test_channel(request: SMSTestRequest):
    """
    Test SMS channel connectivity.
    Used by the debtor query system to verify channel configuration.
    """
    logger.info(f"Channel Test - Phone: {request.phone}, Channel: {request.channel_id}")
    
    return {
        "code": 200,
        "message": "Test successful",
        "response_time_ms": round(50 + (hash(request.phone) % 100), 2),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/callback")
async def sms_callback(request: SMSCallbackRequest):
    """
    SMS delivery status callback endpoint.
    The debtor query system can call this to simulate delivery reports.
    """
    callback_record = {
        "msg_id": request.msg_id,
        "phone": request.phone,
        "status": request.status,
        "delivered_at": request.delivered_at,
        "error_code": request.error_code,
        "error_message": request.error_message,
        "received_at": datetime.utcnow().isoformat()
    }
    
    webhook_calls.append(callback_record)
    
    logger.info(f"Callback Received - MsgID: {request.msg_id}, Status: {request.status}")
    
    return {"code": 200, "message": "Callback received"}


@app.get("/api/sms/logs")
async def get_sms_logs(limit: int = 100):
    """
    Get all received SMS logs.
    Useful for testing and debugging.
    """
    return {
        "total": len(received_sms),
        "logs": received_sms[-limit:]
    }


@app.get("/api/webhook/logs")
async def get_webhook_logs(limit: int = 100):
    """
    Get all webhook call logs.
    Useful for testing and debugging.
    """
    return {
        "total": len(webhook_calls),
        "logs": webhook_calls[-limit:]
    }


@app.delete("/api/sms/logs")
async def clear_logs():
    """Clear all SMS and webhook logs"""
    global received_sms, webhook_calls
    received_sms = []
    webhook_calls = []
    logger.info("All logs cleared")
    return {"message": "Logs cleared"}


@app.post("/api/batch-send")
async def batch_send_sms(phones: List[str], content: str, channel_id: Optional[int] = None):
    """
    Simulate batch SMS sending.
    For load testing the debtor query system.
    """
    results = []
    
    for phone in phones:
        msg_id = f"MOCK-{uuid.uuid4().hex[:12].upper()}"
        
        sms_record = {
            "msg_id": msg_id,
            "phone": phone,
            "content": content,
            "channel_id": channel_id,
            "received_at": datetime.utcnow().isoformat(),
            "status": "sent"
        }
        received_sms.append(sms_record)
        
        results.append({
            "phone": phone,
            "msg_id": msg_id,
            "status": "sent"
        })
    
    logger.info(f"Batch SMS Sent - Count: {len(phones)}")
    
    return {
        "code": 200,
        "message": "Batch sent successfully",
        "total": len(phones),
        "results": results
    }


if __name__ == "__main__":
    print("Starting SMS Mock Server on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
