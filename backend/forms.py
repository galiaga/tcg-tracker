# backend/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class TournamentCreationForm(FlaskForm):
    name = StringField(
        'Tournament Name',
        validators=[DataRequired(), Length(min=3, max=100)]
    )
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=5000)]
    )
    event_date = DateTimeField(
        'Event Date and Time',
        format='%Y-%m-%d %H:%M:%S',
        validators=[DataRequired()],
        description="Format: YYYY-MM-DD HH:MM:SS (e.g., 2024-12-31 18:00:00)"
    )
    format = StringField(
        'Game Format',
        validators=[Optional(), Length(max=50)]
    )
    pairing_system = SelectField(
        'Pairing System',
        choices=[
            ('', '-- Select Pairing System --'),
            ('swiss', 'Swiss'),
            ('round_robin', 'Round Robin'),
            ('single_elimination', 'Single Elimination'),
            ('double_elimination', 'Double Elimination')
        ],
        validators=[DataRequired()]
    )
    max_players = IntegerField(
        'Maximum Players',
        validators=[Optional(), NumberRange(min=2)],
        description="Leave blank for unlimited"
    )
    submit = SubmitField('Create Tournament')