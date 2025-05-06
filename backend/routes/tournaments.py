# backend/routes/tournaments.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from backend import db, limiter
from backend.models.tournament import Tournament
from backend.models.user import User # Import User model
from backend.forms import TournamentCreationForm
from backend.utils.decorators import login_required

tournaments_bp = Blueprint('tournaments', __name__, url_prefix='/tournaments')

# Helper function (similar to the one in frontend.py, or move to a common util)
def _get_page_context():
    user_obj = None
    is_logged_in_status = False
    user_id_from_session = session.get("user_id")
    if user_id_from_session:
        user_obj = db.session.get(User, user_id_from_session)
        if user_obj:
            is_logged_in_status = True
        else: # Should not happen if @login_required works, but good for robustness
            session.clear()
    return user_obj, is_logged_in_status

@tournaments_bp.route('/new', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
@login_required
def create_tournament():
    user_id = session.get('user_id') # From @login_required, this should be valid
    form = TournamentCreationForm()

    if form.validate_on_submit():
        try:
            new_tournament = Tournament(
                name=form.name.data,
                description=form.description.data,
                event_date=form.event_date.data,
                format=form.format.data,
                pairing_system=form.pairing_system.data,
                max_players=form.max_players.data,
                organizer_id=user_id,
                status='Planned'
            )
            db.session.add(new_tournament)
            db.session.commit()
            current_app.logger.info(f"Tournament '{new_tournament.name}' (ID: {new_tournament.id}) created by user ID: {user_id}.")
            flash('Tournament created successfully!', 'success')
            return redirect(url_for('tournaments.view_tournament', tournament_id=new_tournament.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating tournament for user ID {user_id}: {str(e)}", exc_info=True)
            flash(f'Error creating tournament: An unexpected error occurred.', 'danger')

    # For GET request or if POST validation fails
    current_user_for_layout, is_logged_in_for_layout = _get_page_context()
    return render_template(
        'tournaments/create-tournament.html', # Use your hyphenated name
        title='Create New Tournament',
        form=form,
        is_logged_in=is_logged_in_for_layout,
        user=current_user_for_layout
    )

@tournaments_bp.route('/<int:tournament_id>')
@login_required
def view_tournament(tournament_id):
    tournament = db.session.get(Tournament, tournament_id)
    if not tournament:
        flash('Tournament not found.', 'danger')
        return redirect(url_for('frontend.index_page')) # Or your main dashboard/list page

    current_user_for_layout, is_logged_in_for_layout = _get_page_context()
    return render_template(
        'tournaments/view-tournament.html',
        title=tournament.name,
        tournament=tournament,
        is_logged_in=is_logged_in_for_layout,
        user=current_user_for_layout
    )