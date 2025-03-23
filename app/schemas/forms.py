from datetime import datetime
from fastapi import Form
from pydantic import BaseModel


class CreateProductForm(BaseModel):
	name: str
	description: str
	area: str
	regions: str
	ingredients: str

	@classmethod
	def as_form(
		cls,
		name: str = Form(...),
		description: str = Form(...),
		area: str = Form(...),
		regions: str = Form(...),
		ingredients: str = Form(...),
	):
		return cls(
			name=name,
            		description=description,
	    		area=area,
            		regions=regions,
            		ingredients=ingredients,
        	)


class UpdateProductForm(BaseModel):
	name: str
	description: str
	area: str
	regions: str
	ingredients: str
	date_added: datetime
	user_id: int

	@classmethod
	def as_form(
		cls,
		name: str = Form(...),
		description: str = Form(...),
		area: str = Form(...),
		regions: str = Form(...),
		ingredients: str = Form(...),
		date_added: datetime = Form(...),
		user_id: int = Form(...),
	):
		return cls(
			name=name,
            		description=description,
	    		area=area,
            		regions=regions,
            		ingredients=ingredients,
			date_added=date_added,
			user_id=user_id,
        	)

