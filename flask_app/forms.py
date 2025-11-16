from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, Regexp

class RequestResetForm(FlaskForm):
    discord_id = StringField('Votre ID Discord', validators=[DataRequired(), Regexp(r'^\d+$', message="L'ID Discord ne doit contenir que des chiffres.")])
    submit = SubmitField('Recevoir le code')

class RegistrationForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired(), Length(min=2, max=20)])
    discord_id = StringField('Votre ID Discord', validators=[DataRequired(), Regexp(r'^\d+$', message="L'ID Discord ne doit contenir que des chiffres.")])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('S\'inscrire')

class LoginForm(FlaskForm):
    username = StringField('Nom d\'utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Se connecter')