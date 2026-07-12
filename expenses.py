from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
import models, schemas
from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/expenses", tags=["expenses"])


def to_out(e: models.Expense) -> schemas.ExpenseOut:
    return schemas.ExpenseOut.from_orm(e)


def load_expense(db: Session, id: int) -> models.Expense:
    return (
        db.query(models.Expense)
        .options(joinedload(models.Expense.vehicle))
        .filter(models.Expense.id == id)
        .first()
    )


@router.get("", response_model=list[schemas.ExpenseOut])
def list_expenses(
    vehicle_id: Optional[int] = Query(None),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(models.Expense).options(joinedload(models.Expense.vehicle))
    if vehicle_id:
        q = q.filter(models.Expense.vehicle_id == vehicle_id)
    if type:
        q = q.filter(models.Expense.type == type)
    expenses = q.order_by(models.Expense.date.desc()).all()
    return [to_out(e) for e in expenses]


@router.post("", response_model=schemas.ExpenseOut, status_code=201)
def create_expense(body: schemas.ExpenseInput, db: Session = Depends(get_db), _=Depends(get_current_user)):
    vehicle = db.query(models.Vehicle).filter(models.Vehicle.id == body.vehicleId).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    expense = models.Expense(
        vehicle_id=body.vehicleId,
        trip_id=body.tripId,
        type=body.type,
        amount=body.amount,
        date=body.date,
        description=body.description,
        notes=body.notes,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return to_out(load_expense(db, expense.id))


@router.get("/{id}", response_model=schemas.ExpenseOut)
def get_expense(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    e = load_expense(db, id)
    if not e:
        raise HTTPException(status_code=404, detail="Expense not found")
    return to_out(e)


@router.patch("/{id}", response_model=schemas.ExpenseOut)
def update_expense(id: int, body: schemas.ExpenseUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    e = db.query(models.Expense).filter(models.Expense.id == id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Expense not found")
    for field, col in [
        ("type", "type"), ("amount", "amount"), ("date", "date"),
        ("description", "description"), ("notes", "notes"),
    ]:
        val = getattr(body, field, None)
        if val is not None:
            setattr(e, col, val)
    db.commit()
    db.refresh(e)
    return to_out(load_expense(db, e.id))


@router.delete("/{id}", status_code=204)
def delete_expense(id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    e = db.query(models.Expense).filter(models.Expense.id == id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(e)
    db.commit()
