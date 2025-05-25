from datetime import UTC, datetime, timedelta

import pytest
from pytest_mock import MockerFixture
from sqlmodel import Session

from app.models.grant_cycle import GrantCycle, GrantCycleStatus, GrantCycleUpdate
from app.services.status_updater import StatusUpdateService


@pytest.fixture
def status_updater(db: Session) -> StatusUpdateService:
    """Create a StatusUpdateService instance for testing."""
    return StatusUpdateService(db=db)


@pytest.fixture
def base_cycle() -> GrantCycle:
    """Create a base grant cycle for testing."""
    return GrantCycle(
        id=1,
        name="Test Grant Cycle",
        grant_program_id=1,
        status=GrantCycleStatus.AWAITING,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_update_grant_cycle_statuses_no_cycles(
    status_updater: StatusUpdateService, mocker: MockerFixture
) -> None:
    """Test updating statuses when there are no active cycles."""
    # Mock crud.grant_cycle.get_all_active to return empty list
    mocker.patch("app.crud.grant_cycle.GrantCycleCRUD.get_all_active", return_value=[])

    # Should not raise any exceptions
    await status_updater.update_grant_cycle_statuses()


@pytest.mark.asyncio
async def test_awaiting_to_in_progress_transition(
    status_updater: StatusUpdateService, base_cycle: GrantCycle, mocker: MockerFixture
) -> None:
    """Test transition from AWAITING to IN_PROGRESS when first_action_date is reached."""
    # Setup
    today = datetime.now(UTC)
    # Create a new cycle with the modified date to avoid read-only property error
    cycle = GrantCycle(
        **{
            **base_cycle.model_dump(),
            "application_open_date": today - timedelta(days=1),  # Yesterday
        }
    )

    # Mock crud calls
    mock_get_all = mocker.patch(
        "app.crud.grant_cycle.GrantCycleCRUD.get_all_active", return_value=[cycle]
    )
    mock_get = mocker.patch("app.crud.grant_cycle.GrantCycleCRUD.get", return_value=cycle)
    mock_update = mocker.patch("app.crud.grant_cycle.GrantCycleCRUD.update")
    mock_log_create = mocker.patch(
        "app.crud.log_automatic_status_change.LogAutomaticStatusChangeCRUD.create"
    )

    # Execute
    await status_updater.update_grant_cycle_statuses()

    # Verify
    assert mock_update.call_count == 1
    crud_update_call = mock_update.call_args
    assert crud_update_call is not None
    update_obj = crud_update_call[1]["obj_in"]
    assert isinstance(update_obj, GrantCycleUpdate)
    assert update_obj.status == GrantCycleStatus.IN_PROGRESS

    # Verify log creation
    assert mock_log_create.call_count == 1
    log_create_call = mock_log_create.call_args
    assert log_create_call is not None
    log_obj = log_create_call[1]["obj_in"]
    assert log_obj.previous_status == GrantCycleStatus.AWAITING
    assert log_obj.new_status == GrantCycleStatus.IN_PROGRESS
    assert "First action date" in log_obj.reason


@pytest.mark.asyncio
async def test_in_progress_to_submitted_transition(
    status_updater: StatusUpdateService, base_cycle: GrantCycle, mocker: MockerFixture
) -> None:
    """Test transition from IN_PROGRESS to SUBMITTED when conditions are met."""
    # Setup
    today = datetime.now(UTC)
    # Create a new cycle with the modified dates and status
    cycle = GrantCycle(
        **{
            **base_cycle.model_dump(),
            "status": GrantCycleStatus.IN_PROGRESS,
            "application_due_date": today - timedelta(days=1),  # Yesterday
            "application_submitted_date": today - timedelta(days=2),  # Two days ago
        }
    )

    # Mock crud calls
    mock_get_all = mocker.patch(
        "app.crud.grant_cycle.GrantCycleCRUD.get_all_active", return_value=[cycle]
    )
    mock_get = mocker.patch("app.crud.grant_cycle.GrantCycleCRUD.get", return_value=cycle)
    mock_update = mocker.patch("app.crud.grant_cycle.GrantCycleCRUD.update")
    mock_log_create = mocker.patch(
        "app.crud.log_automatic_status_change.LogAutomaticStatusChangeCRUD.create"
    )

    # Execute
    await status_updater.update_grant_cycle_statuses()

    # Verify
    assert mock_update.call_count == 1
    crud_update_call = mock_update.call_args
    assert crud_update_call is not None
    update_obj = crud_update_call[1]["obj_in"]
    assert isinstance(update_obj, GrantCycleUpdate)
    assert update_obj.status == GrantCycleStatus.SUBMITTED

    # Verify log creation
    assert mock_log_create.call_count == 1
    log_create_call = mock_log_create.call_args
    assert log_create_call is not None
    log_obj = log_create_call[1]["obj_in"]
    assert log_obj.previous_status == GrantCycleStatus.IN_PROGRESS
    assert log_obj.new_status == GrantCycleStatus.SUBMITTED
    assert "Application due date" in log_obj.reason


@pytest.mark.asyncio
async def test_no_transition_when_dates_not_met(
    status_updater: StatusUpdateService, base_cycle: GrantCycle, mocker: MockerFixture
) -> None:
    """Test no transition occurs when dates are not met."""
    # Setup
    today = datetime.now(UTC)
    # Create a new cycle with the modified date
    cycle = GrantCycle(
        **{
            **base_cycle.model_dump(),
            "application_open_date": today + timedelta(days=1),  # Tomorrow
        }
    )

    # Mock crud calls
    mocker.patch("app.crud.grant_cycle.GrantCycleCRUD.get_all_active", return_value=[cycle])
    mocker.patch("app.crud.grant_cycle.GrantCycleCRUD.update")
    mocker.patch("app.crud.log_automatic_status_change.LogAutomaticStatusChangeCRUD.create")

    # Execute
    await status_updater.update_grant_cycle_statuses()

    # Verify no updates occurred
    assert not mocker.patch("app.crud.grant_cycle.GrantCycleCRUD.update").called
    assert not mocker.patch(
        "app.crud.log_automatic_status_change.LogAutomaticStatusChangeCRUD.create"
    ).called


@pytest.mark.asyncio
async def test_error_handling(status_updater: StatusUpdateService, mocker: MockerFixture) -> None:
    """Test error handling when database operations fail."""
    # Mock crud.grant_cycle.get_all_active to raise an exception
    mocker.patch(
        "app.crud.grant_cycle.GrantCycleCRUD.get_all_active",
        side_effect=Exception("Database error"),
    )

    # Should raise the exception
    with pytest.raises(Exception, match="Database error"):
        await status_updater.update_grant_cycle_statuses()


@pytest.mark.asyncio
async def test_inactive_cycle_no_transition(
    status_updater: StatusUpdateService, base_cycle: GrantCycle, mocker: MockerFixture
) -> None:
    """Test that inactive cycles don't transition even if dates are met."""
    # Setup
    today = datetime.now(UTC)
    # Create a new cycle with modified properties
    cycle = GrantCycle(
        **{
            **base_cycle.model_dump(),
            "application_open_date": today - timedelta(days=1),  # Yesterday
            "status": GrantCycleStatus.DIDNT_APPLY,  # Sets is_active to False
        }
    )

    # Mock crud calls
    mock_get_all = mocker.patch(
        "app.crud.grant_cycle.GrantCycleCRUD.get_all_active", return_value=[]
    )  # Return empty list since cycle is inactive
    mock_get = mocker.patch("app.crud.grant_cycle.GrantCycleCRUD.get", return_value=cycle)
    mock_update = mocker.patch("app.crud.grant_cycle.GrantCycleCRUD.update")
    mock_log_create = mocker.patch(
        "app.crud.log_automatic_status_change.LogAutomaticStatusChangeCRUD.create"
    )

    # Execute
    await status_updater.update_grant_cycle_statuses()

    # Verify no updates occurred
    assert mock_update.call_count == 0
    assert mock_log_create.call_count == 0
