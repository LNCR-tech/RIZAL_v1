"""CRUD routes for the event router package."""

from fastapi import Header

from .shared import *  # noqa: F403

router = APIRouter()


def _normalize_event_create_idempotency_key(raw_value: str | None) -> str | None:
    normalized = str(raw_value or "").strip()
    if not normalized:
        return None
    if len(normalized) > 128:
        raise HTTPException(
            status_code=400,
            detail="X-Idempotency-Key must not exceed 128 characters.",
        )
    return normalized


def _find_existing_idempotent_event(
    db: Session,
    *,
    school_id: int,
    current_user: UserModel,
    idempotency_key: str,
) -> EventModel | None:
    return (
        _school_scoped_event_query(db, school_id)
        .options(
            joinedload(EventModel.departments),
            joinedload(EventModel.programs),
            joinedload(EventModel.event_type),
            joinedload(EventModel.attendances),
        )
        .filter(
            EventModel.created_by_user_id == current_user.id,
            EventModel.create_idempotency_key == idempotency_key,
        )
        .first()
    )


@router.post(
    "/",
    response_model=EventWithRelations,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(lambda db=Depends(get_db), user=Depends(get_current_user): _ensure_event_manager(db, user))]
)
def create_event(
    event: EventCreate,
    governance_context: GovernanceUnitType | None = Query(default=None),
    idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    normalized_idempotency_key = _normalize_event_create_idempotency_key(idempotency_key)

    try:
        _ensure_event_manager(db, current_user)
        school_id = _require_school_scope(current_user)
        payload_fields_set = _get_payload_fields_set(event)

        # Enforce target-scope permissions before any DB writes.
        validate_event_targets_for_actor(
            db,
            current_user=current_user,
            event_targets=event.event_targets or [],
        )

        if normalized_idempotency_key is not None:
            existing_event = _find_existing_idempotent_event(
                db,
                school_id=school_id,
                current_user=current_user,
                idempotency_key=normalized_idempotency_key,
            )
            if existing_event is not None:
                return existing_event

        if event.start_datetime >= event.end_datetime:
            raise HTTPException(status_code=400, detail="End datetime must be after start datetime")

        validate_event_geolocation_fields(
            latitude=event.geo_latitude,
            longitude=event.geo_longitude,
            radius_m=event.geo_radius_m,
            required=event.geo_required,
        )

        resolved_governance_unit, scoped_department_ids, scoped_program_ids = (
            _resolve_governance_event_write_unit_and_scope(
                db,
                current_user=current_user,
                governance_context=governance_context,
            )
        )
        school_settings = _get_school_settings(db, school_id=school_id)
        (
            default_early_check_in_minutes,
            default_late_threshold_minutes,
            default_sign_out_grace_minutes,
        ) = resolve_governance_event_default_values(
            school_settings=school_settings,
            governance_unit=resolved_governance_unit,
        )
        effective_early_check_in_minutes = (
            event.early_check_in_minutes
            if "early_check_in_minutes" in payload_fields_set
            else default_early_check_in_minutes
        )
        effective_late_threshold_minutes = (
            event.late_threshold_minutes
            if "late_threshold_minutes" in payload_fields_set
            else default_late_threshold_minutes
        )
        effective_sign_out_grace_minutes = (
            event.sign_out_grace_minutes
            if "sign_out_grace_minutes" in payload_fields_set
            else default_sign_out_grace_minutes
        )
        effective_sign_out_open_delay_minutes = int(event.sign_out_open_delay_minutes or 0)
        if effective_sign_out_open_delay_minutes > effective_sign_out_grace_minutes:
            raise HTTPException(
                status_code=400,
                detail=(
                    "sign_out_open_delay_minutes cannot be greater than "
                    "sign_out_grace_minutes."
                ),
            )
        now_local = datetime.now(get_event_timezone()).replace(microsecond=0)
        (
            present_until_override_at,
            late_until_override_at,
        ) = _resolve_near_start_attendance_override_window(
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            early_check_in_minutes=effective_early_check_in_minutes,
            late_threshold_minutes=effective_late_threshold_minutes,
            current_time=now_local,
        )

        db_event = EventModel(
            school_id=school_id,
            created_by_user_id=current_user.id,
            create_idempotency_key=normalized_idempotency_key,
            name=event.name,
            location=event.location,
            geo_latitude=event.geo_latitude,
            geo_longitude=event.geo_longitude,
            geo_radius_m=event.geo_radius_m,
            geo_required=event.geo_required,
            geo_max_accuracy_m=event.geo_max_accuracy_m,
            early_check_in_minutes=effective_early_check_in_minutes,
            late_threshold_minutes=effective_late_threshold_minutes,
            sign_out_grace_minutes=effective_sign_out_grace_minutes,
            sign_out_open_delay_minutes=effective_sign_out_open_delay_minutes,
            present_until_override_at=present_until_override_at,
            late_until_override_at=late_until_override_at,
            start_datetime=event.start_datetime,
            end_datetime=event.end_datetime,
            status=ModelEventStatus[event.status.value.upper()].value,
            event_type=_resolve_event_type(
                db,
                school_id=school_id,
                event_type_id=event.event_type_id,
            ),
        )
        db.add(db_event)
        db.flush()

        # Handle Event Targets (Phase 4)
        targets_to_create = []
        if event.event_targets:
            targets_to_create = event.event_targets
        elif event.department_ids or event.program_ids:
            # Backward compatibility: migrate legacy ids to targets
            for dept_id in event.department_ids:
                targets_to_create.append(EventTargetCreate(scope_type=EventTargetScope.DEPARTMENT, department_id=dept_id))
            for prog_id in event.program_ids:
                targets_to_create.append(EventTargetCreate(scope_type=EventTargetScope.COURSE, course_id=prog_id))
        else:
            # Default to ALL if nothing specified (preserves old behavior)
            targets_to_create.append(EventTargetCreate(scope_type=EventTargetScope.ALL))

        if not targets_to_create:
            raise HTTPException(status_code=400, detail="Event must have at least one target audience.")

        for target_data in targets_to_create:
            # Validation of department/program existence within the same school
            if target_data.department_id:
                dept_exists = db.query(DepartmentModel).filter(
                    DepartmentModel.id == target_data.department_id,
                    DepartmentModel.school_id == school_id
                ).first()
                if not dept_exists:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Department ID {target_data.department_id} not found in this school."
                    )
            if target_data.course_id:
                prog_exists = db.query(ProgramModel).filter(
                    ProgramModel.id == target_data.course_id,
                    ProgramModel.school_id == school_id
                ).first()
                if not prog_exists:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Program ID {target_data.course_id} not found in this school."
                    )

            db_target = EventTargetModel(
                event_id=db_event.id,
                school_id=school_id,
                scope_type=target_data.scope_type,
                year_level=target_data.year_level,
                department_id=target_data.department_id,
                course_id=target_data.course_id
            )
            db.add(db_target)

        target_department_ids = list(event.department_ids or [])
        target_program_ids = list(event.program_ids or [])
        if resolved_governance_unit is not None:
            target_department_ids, target_program_ids = scoped_department_ids, scoped_program_ids

        if target_department_ids:
            departments = db.query(DepartmentModel).filter(
                DepartmentModel.school_id == school_id,
                DepartmentModel.id.in_(target_department_ids)
            ).all()
            if len(departments) != len(target_department_ids):
                missing = set(target_department_ids) - {department.id for department in departments}
                raise HTTPException(status_code=404, detail=f"Departments not found: {missing}")
            db_event.departments = departments

        if target_program_ids:
            programs = db.query(ProgramModel).options(
                joinedload(ProgramModel.departments)
            ).filter(
                ProgramModel.school_id == school_id,
                ProgramModel.id.in_(target_program_ids)
            ).all()
            if len(programs) != len(target_program_ids):
                missing = set(target_program_ids) - {program.id for program in programs}
                raise HTTPException(status_code=404, detail=f"Programs not found: {missing}")
            db_event.programs = programs

        auto_sync_result = None
        if db_event.status not in {ModelEventStatus.CANCELLED, ModelEventStatus.COMPLETED}:
            auto_sync_result = sync_event_workflow_status(db, db_event)

        if db_event.status == ModelEventStatus.COMPLETED and not (
            auto_sync_result and auto_sync_result.attendance_finalized
        ):
            finalize_completed_event_attendance(db, db_event)
            generate_sanctions_for_completed_event(db, db_event)

        db.commit()
        db.refresh(db_event)
        return db_event

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        logger.error("Event creation integrity error: %s", exc)
        if normalized_idempotency_key is not None:
            existing_event = _find_existing_idempotent_event(
                db,
                school_id=school_id,
                current_user=current_user,
                idempotency_key=normalized_idempotency_key,
            )
            if existing_event is not None:
                return existing_event
        raise HTTPException(status_code=400, detail="Event creation failed (possible duplicate)")
    except Exception as exc:
        db.rollback()
        logger.error("Event creation error: %s", exc)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.patch("/{event_id}", response_model=EventSchema)
def update_event(
    event_id: int,
    event_update: EventUpdate,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    try:
        _ensure_event_manager(db, current_user)
        school_id = _require_school_scope(current_user)

        db_event = (
            _school_scoped_event_query(db, school_id)
            .options(
                joinedload(EventModel.departments),
                joinedload(EventModel.programs),
                joinedload(EventModel.event_type),
            )
            .filter(EventModel.id == event_id)
            .first()
        )
        if not db_event:
            raise HTTPException(status_code=404, detail="Event not found")
        _ensure_event_is_writable_in_governance_scope(
            db,
            current_user=current_user,
            event=db_event,
            governance_context=governance_context,
        )

        # Enforce target-scope permissions when the caller is replacing targets.
        if event_update.event_targets is not None:
            validate_event_targets_for_actor(
                db,
                current_user=current_user,
                event_targets=event_update.event_targets,
            )

        was_completed = db_event.status == ModelEventStatus.COMPLETED

        new_start = (
            event_update.start_datetime
            if event_update.start_datetime is not None
            else db_event.start_datetime
        )
        new_end = (
            event_update.end_datetime
            if event_update.end_datetime is not None
            else db_event.end_datetime
        )
        if new_start >= new_end:
            raise HTTPException(status_code=400, detail="End datetime must be after start datetime")

        new_geo_latitude = (
            event_update.geo_latitude if event_update.geo_latitude is not None else db_event.geo_latitude
        )
        new_geo_longitude = (
            event_update.geo_longitude if event_update.geo_longitude is not None else db_event.geo_longitude
        )
        new_geo_radius = (
            event_update.geo_radius_m if event_update.geo_radius_m is not None else db_event.geo_radius_m
        )
        new_geo_required = (
            event_update.geo_required if event_update.geo_required is not None else bool(db_event.geo_required)
        )
        validate_event_geolocation_fields(
            latitude=new_geo_latitude,
            longitude=new_geo_longitude,
            radius_m=new_geo_radius,
            required=new_geo_required,
        )
        merged_early_check_in_minutes = (
            event_update.early_check_in_minutes
            if event_update.early_check_in_minutes is not None
            else int(db_event.early_check_in_minutes or 0)
        )
        merged_late_threshold_minutes = (
            event_update.late_threshold_minutes
            if event_update.late_threshold_minutes is not None
            else int(db_event.late_threshold_minutes or 0)
        )
        merged_sign_out_grace_minutes = (
            event_update.sign_out_grace_minutes
            if event_update.sign_out_grace_minutes is not None
            else int(db_event.sign_out_grace_minutes or 0)
        )
        merged_sign_out_open_delay_minutes = (
            event_update.sign_out_open_delay_minutes
            if event_update.sign_out_open_delay_minutes is not None
            else int(getattr(db_event, "sign_out_open_delay_minutes", 0) or 0)
        )
        if merged_sign_out_open_delay_minutes > merged_sign_out_grace_minutes:
            raise HTTPException(
                status_code=400,
                detail=(
                    "sign_out_open_delay_minutes cannot be greater than "
                    "sign_out_grace_minutes."
                ),
            )
        now_local = datetime.now(get_event_timezone()).replace(microsecond=0)
        (
            present_until_override_at,
            late_until_override_at,
        ) = _resolve_near_start_attendance_override_window(
            start_datetime=new_start,
            end_datetime=new_end,
            early_check_in_minutes=merged_early_check_in_minutes,
            late_threshold_minutes=merged_late_threshold_minutes,
            current_time=now_local,
        )

        if event_update.name is not None:
            db_event.name = event_update.name
        if event_update.location is not None:
            db_event.location = event_update.location
        if event_update.geo_latitude is not None:
            db_event.geo_latitude = event_update.geo_latitude
        if event_update.geo_longitude is not None:
            db_event.geo_longitude = event_update.geo_longitude
        if event_update.geo_radius_m is not None:
            db_event.geo_radius_m = event_update.geo_radius_m
        if event_update.geo_required is not None:
            db_event.geo_required = event_update.geo_required
        if event_update.geo_max_accuracy_m is not None:
            db_event.geo_max_accuracy_m = event_update.geo_max_accuracy_m
        if event_update.early_check_in_minutes is not None:
            db_event.early_check_in_minutes = event_update.early_check_in_minutes
        if event_update.late_threshold_minutes is not None:
            db_event.late_threshold_minutes = event_update.late_threshold_minutes
        if event_update.sign_out_grace_minutes is not None:
            db_event.sign_out_grace_minutes = event_update.sign_out_grace_minutes
        if event_update.sign_out_grace_minutes is None:
            db_event.sign_out_grace_minutes = merged_sign_out_grace_minutes
        if event_update.sign_out_open_delay_minutes is not None:
            db_event.sign_out_open_delay_minutes = event_update.sign_out_open_delay_minutes
        if event_update.sign_out_open_delay_minutes is None:
            db_event.sign_out_open_delay_minutes = merged_sign_out_open_delay_minutes
        db_event.start_datetime = new_start
        db_event.end_datetime = new_end
        db_event.present_until_override_at = present_until_override_at
        db_event.late_until_override_at = late_until_override_at
        if event_update.status is not None:
            db_event.status = ModelEventStatus[event_update.status.value.upper()].value
        event_type_id = getattr(event_update, "event_type_id", None)
        if event_type_id is not None or "event_type_id" in _get_payload_fields_set(event_update):
            db_event.event_type = _resolve_event_type(
                db,
                school_id=school_id,
                event_type_id=event_type_id,
            )

        resolved_scope = _resolve_governance_event_write_scope(
            db,
            current_user=current_user,
            governance_context=governance_context,
        )
        target_department_ids = (
            list(event_update.department_ids) if event_update.department_ids is not None else None
        )
        target_program_ids = (
            list(event_update.program_ids) if event_update.program_ids is not None else None
        )
        if resolved_scope is not None:
            target_department_ids, target_program_ids = resolved_scope

        if target_department_ids is not None:
            db_event.departments = []
            db.flush()
            departments = db.query(DepartmentModel).filter(
                DepartmentModel.school_id == school_id,
                DepartmentModel.id.in_(target_department_ids)
            ).all()
            if len(departments) != len(target_department_ids):
                missing = set(target_department_ids) - {department.id for department in departments}
                raise HTTPException(status_code=404, detail=f"Departments not found: {missing}")
            db_event.departments = departments

        if target_program_ids is not None:
            db_event.programs = []
            db.flush()
            programs = db.query(ProgramModel).options(
                joinedload(ProgramModel.departments)
            ).filter(
                ProgramModel.school_id == school_id,
                ProgramModel.id.in_(target_program_ids)
            ).all()
            if len(programs) != len(target_program_ids):
                missing = set(target_program_ids) - {program.id for program in programs}
                raise HTTPException(status_code=404, detail=f"Programs not found: {missing}")
            db_event.programs = programs

        # Handle Event Targets update (Phase 4)
        explicit_targets = event_update.event_targets

        # If legacy fields are explicitly updated but event_targets is not, migrate them
        if explicit_targets is None and (event_update.department_ids is not None or event_update.program_ids is not None):
            explicit_targets = []
            # Use provided lists or existing associations
            dept_ids = event_update.department_ids if event_update.department_ids is not None else [d.id for d in db_event.departments]
            prog_ids = event_update.program_ids if event_update.program_ids is not None else [p.id for p in db_event.programs]

            for dept_id in dept_ids:
                explicit_targets.append(EventTargetCreate(scope_type=EventTargetScope.DEPARTMENT, department_id=dept_id))
            for prog_id in prog_ids:
                explicit_targets.append(EventTargetCreate(scope_type=EventTargetScope.COURSE, course_id=prog_id))

            if not explicit_targets:
                explicit_targets.append(EventTargetCreate(scope_type=EventTargetScope.ALL))

        if explicit_targets is not None:
            if not explicit_targets:
                raise HTTPException(status_code=400, detail="Event must have at least one target audience.")

            # Remove existing targets and replace them
            db.query(EventTargetModel).filter(EventTargetModel.event_id == db_event.id).delete()
            db.flush()

            for target_data in explicit_targets:
                # Validation
                if target_data.department_id:
                    if not db.query(DepartmentModel).filter(
                        DepartmentModel.id == target_data.department_id,
                        DepartmentModel.school_id == school_id
                    ).first():
                        raise HTTPException(status_code=400, detail=f"Department {target_data.department_id} invalid")
                if target_data.course_id:
                    if not db.query(ProgramModel).filter(
                        ProgramModel.id == target_data.course_id,
                        ProgramModel.school_id == school_id
                    ).first():
                        raise HTTPException(status_code=400, detail=f"Program {target_data.course_id} invalid")

                db_target = EventTargetModel(
                    event_id=db_event.id,
                    school_id=school_id,
                    scope_type=target_data.scope_type,
                    year_level=target_data.year_level,
                    department_id=target_data.department_id,
                    course_id=target_data.course_id
                )
                db.add(db_target)

        auto_sync_result = None
        if db_event.status not in {ModelEventStatus.CANCELLED, ModelEventStatus.COMPLETED}:
            auto_sync_result = sync_event_workflow_status(db, db_event)

        if db_event.status == ModelEventStatus.COMPLETED and not was_completed and not (
            auto_sync_result and auto_sync_result.attendance_finalized
        ):
            finalize_completed_event_attendance(db, db_event)
            generate_sanctions_for_completed_event(db, db_event)

        db.commit()
        db.refresh(db_event)
        return db_event

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        logger.error("Integrity error during event update: %s", exc)
        raise HTTPException(status_code=400, detail="Update failed due to data integrity issues") from exc
    except ValueError as exc:
        db.rollback()
        logger.error("Value error during event update: %s", exc)
        raise HTTPException(status_code=400, detail=f"Invalid data format: {exc}") from exc
    except Exception as exc:
        db.rollback()
        logger.error("Unexpected error during event update: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    governance_context: GovernanceUnitType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    _ensure_event_manager(db, current_user)
    school_id = _require_school_scope(current_user)

    event = (
        _school_scoped_event_query(db, school_id)
        .options(
            joinedload(EventModel.attendances),
            joinedload(EventModel.departments),
            joinedload(EventModel.programs),
        )
        .filter(EventModel.id == event_id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    _ensure_event_is_writable_in_governance_scope(
        db,
        current_user=current_user,
        event=event,
        governance_context=governance_context,
    )

    event.departments = []
    event.programs = []
    for attendance in event.attendances:
        db.delete(attendance)

    db.delete(event)
    db.commit()
