from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Response, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import pandas as pd
from .. import oauth2
from ..database import get_db
from ..utils import process_data, create_graph, tsp_closest_to_max_distance, add_optimal_path_order, PIZZA_SHOP
from ..models import Order

router = APIRouter()


def complete_processing(data, db: Session):
    results = process_data(data)
    graph = create_graph(results)
    optimal_path, _ = tsp_closest_to_max_distance(graph)
    add_optimal_path_order(results, optimal_path)

    db.bulk_insert_mappings(Order, results)
    db.commit()


@router.post("/upload")
async def upload_csv(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(),  user_id: str = Depends(oauth2.require_user), db: Session = Depends(get_db)):
    try:
        if not file.filename.endswith(".csv"):
            raise HTTPException(
                status_code=400, detail="only csv files are allowed")

        df = pd.read_csv(file.file)

        dict_data = df.to_dict(orient='records')

        background_tasks.add_task(complete_processing, dict_data, db)

        success_message = dict(message="csv file uploaded successfully")

        return JSONResponse(content=success_message, status_code=200)

    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.get('/get_next_destination')
async def get_next_destination(response: Response, request: Request, user_id: str = Depends(oauth2.require_user), db: Session = Depends(get_db)):
    try:

        next_destination = db.query(Order).filter(
            Order.done == False, Order.order_by != None).order_by(Order.order_by).first()

        if next_destination:
            next_destination.done = True
            db.commit()
            db.refresh(next_destination)
            next_destination = dict(
                location=next_destination.location,
                latitude=next_destination.latitude,
                lonitude=next_destination.longitude
            )
        else:
            next_destination = PIZZA_SHOP

        return JSONResponse(next_destination, status_code=status.HTTP_200_OK)

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=error)
