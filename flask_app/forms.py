from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp

class RequestResetForm(FlaskForm):
    discord_id = StringField('Votre ID Discord', validators=[DataRequired(), Regexp(r'^\d+$', message="L'ID Discord ne doit contenir que des chiffres.")])
    submit = SubmitField('Recevoir le code')