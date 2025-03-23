from typing import Optional, Annotated
from datetime import datetime, timedelta
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session
from app.crud.user_crud import UserCRUD
from app.crud.product_crud import ProductCRUD
from app.schemas.forms import CreateProductForm, UpdateProductForm
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.token import Token, TokenData
from app.schemas.user import UserCreate, User
from .db import SessionLocal, Base, engine
from .models import Product
from .utils import create_access_token, get_password_hash, verify_token


templates = Jinja2Templates(directory="./app/templates")
app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(access_token: str = Cookie(...), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        if access_token:
            token = access_token.split()[1]
            payload = verify_token(token)
            if payload.get("sub") is None:
                raise credentials_exception
            token_data = TokenData(username=payload["sub"], expires_in=payload.get("exp"))
        else:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = UserCRUD.check_user(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user


@app.get('/login_form')
def login_form(request: Request, response_class=HTMLResponse):
    return templates.TemplateResponse(request=request, name="auth_form.html")


@app.post("/login_form")
def signup(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
    response_class=RedirectResponse,
):
    user = UserCRUD.check_user(db, form_data.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User already exists",
        )
    try:
        UserCRUD.create(
            db,
            UserCreate(username=form_data.username, hashed_password=get_password_hash(form_data.password)),
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjust your data to create a user",
        )
    return RedirectResponse('/login')


@app.post("/login")
def login(
    response: RedirectResponse,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    user = UserCRUD.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
    )
    token = Token(access_token=access_token, token_type="bearer")
    response = RedirectResponse('/products/read', status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {token.access_token}", httponly=True)
    return response


@app.get("/logout")
def logout(request: Request, response_class=RedirectResponse):
    response = RedirectResponse('/products/read', status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response


@app.get("/products/read")
def read_products(
    request: Request,
    db: Session = Depends(get_db),
    response_class=HTMLResponse,
):
    products = ProductCRUD.get_multi(
        db, 
    )
    try:
        current_user = get_current_user(request.cookies.get("access_token"), db)
    except:
        current_user = None
    areas = [product.area for product in products if product.area is not None]
    regions = [product.regions for product in products if product.regions is not None]
    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={"products": products, "current_user": current_user, "areas": areas, "regions": regions},
    )


@app.get("/products/create")
def create_product_form(
    request: Request,
    current_user = Depends(get_current_user),
    response_class=HTMLResponse,
):
    return templates.TemplateResponse(request=request, name="create_form.html")


@app.post("/products/create")
def create_product(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    form_data: CreateProductForm = Depends(CreateProductForm.as_form),
    response_class=RedirectResponse,
):
    obj_in = ProductCreate(
        name=form_data.name,
        description=form_data.description,
        area=form_data.area,
        regions=form_data.regions,
        ingredients=form_data.ingredients,
        date_added=datetime.now(),
        user_id=current_user.id,
    )
    db_product = ProductCRUD.create(db, obj_in)
    response = RedirectResponse('/products/read', status_code=status.HTTP_303_SEE_OTHER)
    return response


@app.get("/products/edit/{product_id}")
def edit_product_form(
    product_id: int,
    request: Request,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
    response_class=HTMLResponse,
):
    product = ProductCRUD.get(db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No product with such ID",
        )
    return templates.TemplateResponse(request=request, name="edit_form.html", context={"product": product})


@app.post("/products/edit/{product_id}")
def update_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    form_data: UpdateProductForm = Depends(UpdateProductForm.as_form)
):
    db_product = ProductCRUD.get(db, id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No product with such ID",
        )
    if db_product.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    product = ProductUpdate(
        name=form_data.name,
        description=form_data.description,
        area=form_data.area,
        regions=form_data.regions,
        ingredients=form_data.ingredients,
        date_added=form_data.date_added,
        user_id=form_data.user_id,
    )
    updated_product = ProductCRUD.update(db, db_obj=db_product, obj_in=product)
    response = RedirectResponse('/products/read', status_code=status.HTTP_303_SEE_OTHER)
    return response


@app.get("/products/search")
def search_products(
    request: Request,
    query: Optional[str] = None,
    user_id: Optional[str] = None,
    area: Optional[str] = None,
    region: Optional[str] = None,
    order_by: Optional[str] = None,
    direction: Optional[str] = None,
    db: Session = Depends(get_db),
    response_class=HTMLResponse,
):
    filters, sorting = {}, {}
    if area:
        filters["area"] = area
    if region:
        filters["region"] = region
    if user_id:
        filters["user_id"] = user_id
    if order_by and direction:
        sorting[order_by] = direction

    products = ProductCRUD.search(
        db,
        search_term=query,
        filters=filters,
        sorting=sorting,
    )
    areas = [product.area for product in products if product.area is not None]
    regions = [product.regions for product in products if product.regions is not None]
    try:
        current_user = get_current_user(request.cookies.get("access_token"), db)
    except:
        current_user = None
    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={"products": products, "current_user": current_user, "areas": areas, "regions": regions},
    )
