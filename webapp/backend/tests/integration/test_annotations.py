"""Integration tests for the annotation endpoints.

Annotations hang off classified segments, which are normally written by the
classification worker. No worker runs in the suite, so each test seeds a job
and its segments directly, then exercises the API against those rows.
"""
import uuid
from datetime import datetime, timezone

import pytest

from app.config import settings

API = settings.API_V1_STR


async def create_segment(user_id: str, *, text: str = "ශ්‍රී ලංකාව", language: str = "sinhala") -> str:
    """Seed a completed job with one segment and return the segment id."""
    from app.db.models.classification_job import ClassificationJob, JobStatus
    from app.db.models.classified_segment import ClassifiedSegment
    from app.db.session import async_session_maker

    async with async_session_maker() as session:
        job = ClassificationJob(
            user_id=uuid.UUID(user_id),
            input_text=text,
            model_name="sklearn_langid",
            segmentation_strategy="sentence",
            status=JobStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc),
        )
        session.add(job)
        await session.flush()

        segment = ClassifiedSegment(
            job_id=job.id,
            segment_index=0,
            text=text,
            predicted_language=language,
            confidence=0.91,
            probabilities={"sinhala": 0.91, "pali": 0.06, "sanskrit": 0.03},
            start_char_offset=0,
            end_char_offset=len(text),
        )
        session.add(segment)
        await session.commit()
        return str(segment.id)


async def submit_annotation(client, headers, segment_id: str, **overrides) -> dict:
    """Submit a correction and return the created annotation."""
    payload = {"segment_id": segment_id, "corrected_language": "pali"}
    payload.update(overrides)

    response = await client.post(f"{API}/annotations", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


# --- create ----------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_annotation(async_client, auth_headers, test_user):
    """POST /annotations records a user's correction for a segment."""
    segment_id = await create_segment(test_user["user"]["id"])

    response = await async_client.post(
        f"{API}/annotations",
        headers=auth_headers,
        json={
            "segment_id": segment_id,
            "corrected_language": "pali",
            "comment": "This looks like Pali, not Sinhala",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "success"

    data = body["data"]
    assert data["segment_id"] == segment_id
    assert data["user_id"] == test_user["user"]["id"]
    assert data["corrected_language"] == "pali"
    assert data["comment"] == "This looks like Pali, not Sinhala"


@pytest.mark.asyncio
async def test_create_annotation_starts_unreviewed(async_client, auth_headers, test_user):
    """A new correction enters the queue unreviewed and unapproved."""
    segment_id = await create_segment(test_user["user"]["id"])

    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    assert annotation["admin_reviewed"] is False
    assert annotation["is_valid_for_training"] is False
    assert annotation["reviewed_by"] is None
    assert annotation["reviewed_at"] is None


@pytest.mark.asyncio
async def test_create_annotation_lowercases_language(async_client, auth_headers, test_user):
    """corrected_language is normalised, so labels stay comparable."""
    segment_id = await create_segment(test_user["user"]["id"])

    annotation = await submit_annotation(
        async_client, auth_headers, segment_id, corrected_language="SANSKRIT"
    )

    assert annotation["corrected_language"] == "sanskrit"


@pytest.mark.asyncio
async def test_create_annotation_without_comment(async_client, auth_headers, test_user):
    """The comment is optional."""
    segment_id = await create_segment(test_user["user"]["id"])

    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    assert annotation["comment"] is None


@pytest.mark.asyncio
async def test_create_duplicate_annotation_returns_400(
    async_client, auth_headers, test_user
):
    """A user may only correct a given segment once."""
    segment_id = await create_segment(test_user["user"]["id"])
    await submit_annotation(async_client, auth_headers, segment_id)

    response = await async_client.post(
        f"{API}/annotations",
        headers=auth_headers,
        json={"segment_id": segment_id, "corrected_language": "sanskrit"},
    )

    assert response.status_code == 400, response.text
    assert "already submitted" in response.json()["detail"]


@pytest.mark.asyncio
async def test_duplicate_check_is_per_user(
    async_client, auth_headers, second_user_headers, test_user
):
    """The one-correction rule is per user, not per segment.

    Two people may disagree with the same prediction, so a second user's
    correction for the same segment must still be accepted.
    """
    segment_id = await create_segment(test_user["user"]["id"])
    await submit_annotation(async_client, auth_headers, segment_id)

    response = await async_client.post(
        f"{API}/annotations",
        headers=second_user_headers,
        json={"segment_id": segment_id, "corrected_language": "sanskrit"},
    )
    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_create_annotation_for_missing_segment_returns_404(
    async_client, auth_headers
):
    """An unknown segment id is a 404."""
    response = await async_client.post(
        f"{API}/annotations",
        headers=auth_headers,
        json={"segment_id": str(uuid.uuid4()), "corrected_language": "pali"},
    )

    assert response.status_code == 404, response.text
    assert "Segment not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_annotation_with_malformed_segment_id_returns_422(
    async_client, auth_headers
):
    """segment_id must be a UUID."""
    response = await async_client.post(
        f"{API}/annotations",
        headers=auth_headers,
        json={"segment_id": "not-a-uuid", "corrected_language": "pali"},
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_create_annotation_without_language_returns_422(
    async_client, auth_headers, test_user
):
    """corrected_language is required."""
    segment_id = await create_segment(test_user["user"]["id"])

    response = await async_client.post(
        f"{API}/annotations", headers=auth_headers, json={"segment_id": segment_id}
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_create_annotation_without_token_returns_401(async_client, test_user):
    """Submitting a correction requires authentication."""
    segment_id = await create_segment(test_user["user"]["id"])

    response = await async_client.post(
        f"{API}/annotations",
        json={"segment_id": segment_id, "corrected_language": "pali"},
    )
    assert response.status_code == 401, response.text


# --- admin list ------------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_can_list_annotations(
    async_client, auth_headers, admin_headers, test_user
):
    """GET /annotations returns the review queue to an admin."""
    segment_id = await create_segment(test_user["user"]["id"])
    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    response = await async_client.get(f"{API}/annotations", headers=admin_headers)

    assert response.status_code == 200, response.text
    listed = {item["id"] for item in response.json()["data"]}
    assert annotation["id"] in listed


@pytest.mark.asyncio
async def test_admin_list_includes_review_context(
    async_client, auth_headers, admin_headers, test_user
):
    """Each row carries the segment text, prediction and submitter.

    An admin needs the original prediction next to the correction to judge it,
    so the listing joins in segment and user fields.
    """
    segment_id = await create_segment(
        test_user["user"]["id"], text="ධම්මං සරණං ගච්ඡාමි", language="sinhala"
    )
    await submit_annotation(
        async_client, auth_headers, segment_id, corrected_language="pali"
    )

    response = await async_client.get(f"{API}/annotations", headers=admin_headers)

    assert response.status_code == 200, response.text
    row = next(
        item for item in response.json()["data"] if item["segment_id"] == segment_id
    )
    assert row["original_text"] == "ධම්මං සරණං ගච්ඡාමි"
    assert row["predicted_language"] == "sinhala"
    assert row["corrected_language"] == "pali"
    assert row["user_email"] == test_user["email"]


@pytest.mark.asyncio
async def test_admin_list_defaults_to_pending_only(
    async_client, auth_headers, admin_headers, test_user
):
    """The default listing is the queue of work still to do."""
    segment_id = await create_segment(test_user["user"]["id"])
    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    review = await async_client.put(
        f"{API}/annotations/{annotation['id']}/review",
        headers=admin_headers,
        json={"is_valid_for_training": True},
    )
    assert review.status_code == 200, review.text

    response = await async_client.get(f"{API}/annotations", headers=admin_headers)

    assert response.status_code == 200, response.text
    listed = {item["id"] for item in response.json()["data"]}
    assert annotation["id"] not in listed


@pytest.mark.asyncio
async def test_admin_list_can_include_reviewed(
    async_client, auth_headers, admin_headers, test_user
):
    """pending_only=false widens the listing to reviewed annotations."""
    segment_id = await create_segment(test_user["user"]["id"])
    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    await async_client.put(
        f"{API}/annotations/{annotation['id']}/review",
        headers=admin_headers,
        json={"is_valid_for_training": True},
    )

    response = await async_client.get(
        f"{API}/annotations", headers=admin_headers, params={"pending_only": "false"}
    )

    assert response.status_code == 200, response.text
    listed = {item["id"] for item in response.json()["data"]}
    assert annotation["id"] in listed


@pytest.mark.asyncio
async def test_admin_list_respects_limit(
    async_client, auth_headers, admin_headers, test_user
):
    """The listing is paginated."""
    for _ in range(3):
        segment_id = await create_segment(test_user["user"]["id"])
        await submit_annotation(async_client, auth_headers, segment_id)

    response = await async_client.get(
        f"{API}/annotations", headers=admin_headers, params={"limit": 2}
    )

    assert response.status_code == 200, response.text
    assert len(response.json()["data"]) == 2


@pytest.mark.asyncio
async def test_admin_list_rejects_out_of_range_limit(async_client, admin_headers):
    """limit is bounded by ge=1 and le=100."""
    too_large = await async_client.get(
        f"{API}/annotations", headers=admin_headers, params={"limit": 101}
    )
    assert too_large.status_code == 422, too_large.text

    too_small = await async_client.get(
        f"{API}/annotations", headers=admin_headers, params={"limit": 0}
    )
    assert too_small.status_code == 422, too_small.text


@pytest.mark.asyncio
async def test_regular_user_cannot_list_annotations(async_client, auth_headers):
    """The review queue is admin-only."""
    response = await async_client.get(f"{API}/annotations", headers=auth_headers)
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_list_annotations_without_token_returns_401(async_client):
    """The review queue requires authentication."""
    response = await async_client.get(f"{API}/annotations")
    assert response.status_code == 401, response.text


# --- admin review ----------------------------------------------------------

@pytest.mark.asyncio
async def test_admin_can_approve_annotation(
    async_client, auth_headers, admin_headers, admin_user, test_user
):
    """PUT /{id}/review marks a correction reviewed and records the reviewer."""
    segment_id = await create_segment(test_user["user"]["id"])
    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    response = await async_client.put(
        f"{API}/annotations/{annotation['id']}/review",
        headers=admin_headers,
        json={"is_valid_for_training": True},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["admin_reviewed"] is True
    assert data["is_valid_for_training"] is True
    assert data["reviewed_by"] == admin_user["user"]["id"]
    assert data["reviewed_at"] is not None


@pytest.mark.asyncio
async def test_admin_can_reject_annotation(
    async_client, auth_headers, admin_headers, test_user
):
    """A rejected correction is still marked reviewed, but not for training."""
    segment_id = await create_segment(test_user["user"]["id"])
    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    response = await async_client.put(
        f"{API}/annotations/{annotation['id']}/review",
        headers=admin_headers,
        json={"is_valid_for_training": False},
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["admin_reviewed"] is True
    assert data["is_valid_for_training"] is False


@pytest.mark.asyncio
async def test_review_persists(async_client, auth_headers, admin_headers, test_user):
    """The review decision survives a re-read."""
    segment_id = await create_segment(test_user["user"]["id"])
    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    await async_client.put(
        f"{API}/annotations/{annotation['id']}/review",
        headers=admin_headers,
        json={"is_valid_for_training": True},
    )

    response = await async_client.get(
        f"{API}/annotations", headers=admin_headers, params={"pending_only": "false"}
    )
    row = next(
        item for item in response.json()["data"] if item["id"] == annotation["id"]
    )
    assert row["admin_reviewed"] is True
    assert row["is_valid_for_training"] is True


@pytest.mark.asyncio
async def test_review_can_be_changed(
    async_client, auth_headers, admin_headers, test_user
):
    """An admin can revise an earlier decision."""
    segment_id = await create_segment(test_user["user"]["id"])
    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    await async_client.put(
        f"{API}/annotations/{annotation['id']}/review",
        headers=admin_headers,
        json={"is_valid_for_training": True},
    )
    response = await async_client.put(
        f"{API}/annotations/{annotation['id']}/review",
        headers=admin_headers,
        json={"is_valid_for_training": False},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["is_valid_for_training"] is False


@pytest.mark.asyncio
async def test_review_missing_annotation_returns_404(async_client, admin_headers):
    """An unknown annotation id is a 404."""
    response = await async_client.put(
        f"{API}/annotations/{uuid.uuid4()}/review",
        headers=admin_headers,
        json={"is_valid_for_training": True},
    )
    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_review_without_decision_returns_422(
    async_client, auth_headers, admin_headers, test_user
):
    """is_valid_for_training is required."""
    segment_id = await create_segment(test_user["user"]["id"])
    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    response = await async_client.put(
        f"{API}/annotations/{annotation['id']}/review",
        headers=admin_headers,
        json={},
    )
    assert response.status_code == 422, response.text


@pytest.mark.asyncio
async def test_regular_user_cannot_review(
    async_client, auth_headers, test_user
):
    """A user cannot approve their own correction as training data."""
    segment_id = await create_segment(test_user["user"]["id"])
    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    response = await async_client.put(
        f"{API}/annotations/{annotation['id']}/review",
        headers=auth_headers,
        json={"is_valid_for_training": True},
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_rejected_review_leaves_annotation_unreviewed(
    async_client, auth_headers, admin_headers, test_user
):
    """A forbidden review attempt changes nothing."""
    segment_id = await create_segment(test_user["user"]["id"])
    annotation = await submit_annotation(async_client, auth_headers, segment_id)

    forbidden = await async_client.put(
        f"{API}/annotations/{annotation['id']}/review",
        headers=auth_headers,
        json={"is_valid_for_training": True},
    )
    assert forbidden.status_code == 403, forbidden.text

    listing = await async_client.get(f"{API}/annotations", headers=admin_headers)
    row = next(
        item for item in listing.json()["data"] if item["id"] == annotation["id"]
    )
    assert row["admin_reviewed"] is False
    assert row["is_valid_for_training"] is False


@pytest.mark.asyncio
async def test_review_without_token_returns_401(async_client):
    """Reviewing requires authentication."""
    response = await async_client.put(
        f"{API}/annotations/{uuid.uuid4()}/review",
        json={"is_valid_for_training": True},
    )
    assert response.status_code == 401, response.text
