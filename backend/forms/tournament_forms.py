# backend/forms/tournament_forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class TournamentCreationForm(FlaskForm):
    """Form for creating a new tournament."""
    name = StringField(
        'Tournament Name',
        validators=[DataRequired(), Length(min=3, max=120)]
    )
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=5000)]
    )
    event_date = DateTimeField(
        'Event Date and Time (YYYY-MM-DD HH:MM or leave blank)',
        format='%Y-%m-%d %H:%M', # Format for input and display
        validators=[Optional()],
        description="Optional. If set, use YYYY-MM-DD HH:MM format."
    )
    # Using 'format_' in the form to avoid conflict with Python's built-in 'format'
    # but the model uses 'format'. The route will handle mapping form.format.data to model.format
    format = StringField( # Field name matches what's used in create-tournament.html and routes
        'Game Format (e.g., Commander, Modern, Sealed)',
        validators=[Optional(), Length(max=50)]
    )
    pairing_system = SelectField(
        'Pairing System',
        choices=[
            ('Swiss', 'Swiss'),
            ('Round Robin', 'Round Robin'),
            ('Single Elimination', 'Single Elimination')
            # Add more systems if they become available
        ],
        validators=[DataRequired()]
    )
    max_players = IntegerField(
        'Maximum Players (leave blank for no limit)',
        validators=[Optional(), NumberRange(min=2, message="Maximum players must be at least 2.")],
        description="Optional. Minimum 2 if specified."
    )
    submit = SubmitField('Create Tournament')


class TournamentSettingsForm(FlaskForm):
    """Form for editing existing tournament settings."""
    name = StringField(
        'Tournament Name',
        validators=[DataRequired(), Length(min=3, max=120)]
    )
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=5000)]
    )
    event_date = DateTimeField(
        'Event Date and Time (YYYY-MM-DD HH:MM or leave blank)',
        format='%Y-%m-%d %H:%M',
        validators=[Optional()],
        description="Optional. If set, use YYYY-MM-DD HH:MM format."
    )
    # Using 'format_' here to distinguish from the model's 'format' attribute
    # The route will handle mapping form.format_.data to model.format
    format_ = StringField( # Note the underscore: form.format_
        'Game Format (e.g., Commander, Modern, Sealed)',
        validators=[Optional(), Length(max=50)],
        render_kw={"id": "format"} # Ensure HTML id is 'format' if needed by JS/CSS
    )
    status = SelectField(
        'Status',
        choices=[
            ('Planned', 'Planned'),
            ('Active', 'Active'),
            ('Completed', 'Completed'),
            ('Cancelled', 'Cancelled')
        ],
        validators=[DataRequired()]
    )
    pairing_system = SelectField(
        'Pairing System',
        choices=[
            ('Swiss', 'Swiss'),
            ('Round Robin', 'Round Robin'),
            ('Single Elimination', 'Single Elimination')
        ],
        validators=[DataRequired()]
    )
    max_players = IntegerField(
        'Maximum Players (leave blank for no limit)',
        validators=[Optional(), NumberRange(min=2, message="Maximum players must be at least 2.")],
        description="Optional. Minimum 2 if specified."
    )
    submit = SubmitField('Save Settings')