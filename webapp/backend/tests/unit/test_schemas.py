import pytest
from pydantic import ValidationError
from app.api.v1.classification import JobCreateRequest
from app.schemas.response import success_response, error_response, BaseResponse

def test_job_create_request_valid():
    """Verify JobCreateRequest accepts valid inputs and defaults strategy to 'sentence'."""
    req = JobCreateRequest(input_text="මෙය පරීක්ෂණ පෙළකි.")
    assert req.input_text == "මෙය පරීක්ෂණ පෙළකි."
    assert req.segmentation_strategy == "sentence"
    
    # Custom valid strategy
    req2 = JobCreateRequest(input_text="පෙළ", segmentation_strategy="paragraph")
    assert req2.segmentation_strategy == "paragraph"
    
    req3 = JobCreateRequest(input_text="පෙළ", segmentation_strategy="full_text")
    assert req3.segmentation_strategy == "full_text"
    
    req4 = JobCreateRequest(input_text="පෙළ", segmentation_strategy="auto")
    assert req4.segmentation_strategy == "auto"

def test_job_create_request_invalid_strategy():
    """Verify JobCreateRequest raises ValidationError on invalid segmentation strategy."""
    with pytest.raises(ValidationError) as exc:
        JobCreateRequest(input_text="පෙළ", segmentation_strategy="invalid_mode")
    assert "segmentation_strategy" in str(exc.value)

def test_job_create_request_empty_input():
    """Verify JobCreateRequest rejects empty string (min_length=1)."""
    with pytest.raises(ValidationError) as exc:
        JobCreateRequest(input_text="")
    assert "input_text" in str(exc.value)

def test_success_response_helper():
    """Verify success_response helper formats payload consistently."""
    res = success_response(data={"job_id": "123"}, message="Created")
    assert res["status"] == "success"
    assert res["message"] == "Created"
    assert res["data"] == {"job_id": "123"}

def test_error_response_helper():
    """Verify error_response helper formats payload consistently."""
    res = error_response(message="Invalid credentials", data=["field required"])
    assert res["status"] == "failed"
    assert res["message"] == "Invalid credentials"
    assert res["data"] == ["field required"]

def test_base_response_pydantic_model():
    """Verify BaseResponse Pydantic generic model parses data properly."""
    model = BaseResponse[dict](status="success", message="OK", data={"count": 5})
    assert model.status == "success"
    assert model.data["count"] == 5
