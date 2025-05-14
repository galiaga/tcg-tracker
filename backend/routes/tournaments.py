# backend/routes/tournaments.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, abort
from sqlalchemy import desc, asc # Import asc for ascending sort

from backend import db, limiter 
from backend.models.tournament import Tournament, TournamentParticipant
from backend.models.user import User 

from backend.forms.tournament_forms import TournamentCreationForm, TournamentSettingsForm
from backend.utils.decorators import login_required as custom_login_required

tournaments_bp = Blueprint('tournaments', __name__, url_prefix='/tournaments')

def _get_page_context_for_session_user():
    user_obj = None
    is_logged_in_status = False
    user_id_from_session = session.get("user_id")
    if user_id_from_session:
        user_obj = db.session.get(User, user_id_from_session)
        if user_obj:
            is_logged_in_status = True
        else:
            current_app.logger.warning(f"User ID {user_id_from_session} from session not found. Clearing session.")
            session.clear()
    return user_obj, is_logged_in_status

@tournaments_bp.route('/', methods=['GET'])
@custom_login_required
def list_my_tournaments():
    current_user_id = session.get('user_id')
    
    # Define valid sortable columns and their corresponding model attributes
    valid_sort_columns = {
        'name': Tournament.name,
        'status': Tournament.status,
        'event_date': Tournament.event_date,
        'created_at': Tournament.created_at
    }

    # Get sort parameters from query string
    requested_sort_by = request.args.get('sort_by', 'event_date') 
    requested_sort_order = request.args.get('sort_order', 'desc')

    # Validate and set current sort parameters
    if requested_sort_by in valid_sort_columns:
        current_sort_by = requested_sort_by
    else:
        current_app.logger.warning(f"Invalid sort_by parameter: '{requested_sort_by}'. Defaulting to 'event_date'.")
        current_sort_by = 'event_date' # Default if invalid

    if requested_sort_order in ['asc', 'desc']:
        current_sort_order = requested_sort_order
    else:
        current_app.logger.warning(f"Invalid sort_order parameter: '{requested_sort_order}'. Defaulting to 'desc'.")
        current_sort_order = 'desc' # Default if invalid

    # Start building the query
    query = Tournament.query_active().filter_by(organizer_id=current_user_id)

    # Apply status filter (if you add it later)
    status_filter = request.args.get('status_filter', '')
    if status_filter:
        query = query.filter(Tournament.status == status_filter)

    # Apply sorting
    sort_column_attr = valid_sort_columns.get(current_sort_by) # Get the SQLAlchemy column object

    # This should always be true now due to validation above, but good for safety
    if sort_column_attr is not None: 
        order_func = asc if current_sort_order == 'asc' else desc
        
        if sort_column_attr == Tournament.event_date:
            if current_sort_order == 'asc': 
                query = query.order_by(Tournament.event_date.is_(None), order_func(sort_column_attr))
            else: 
                query = query.order_by(Tournament.event_date.isnot(None).desc(), order_func(sort_column_attr))
        elif sort_column_attr == Tournament.name:
            # Use db.engine.dialect.name to choose collation if needed, or stick to "C" if it works for SQLite too
            # Forcing BINARY for SQLite tests, "C" for others (like PostgreSQL)
            if db.engine.dialect.name == 'sqlite':
                query = query.order_by(order_func(Tournament.name.collate("BINARY")))
                current_app.logger.info(f"Applying SQLite BINARY collation for name sort: {current_sort_order}")
            else: 
                query = query.order_by(order_func(Tournament.name.collate("C")))
                current_app.logger.info(f"Applying 'C' collation for name sort: {current_sort_order}")
        else: # For other columns like status, created_at
            query = query.order_by(order_func(sort_column_attr))
            current_app.logger.info(f"Applying standard sort for {current_sort_by}: {current_sort_order}")
    else:
        # This else block should ideally not be reached if defaults are set correctly
        current_app.logger.error(f"Fallback: Sort column attribute for '{current_sort_by}' was None. Defaulting sort.")
        query = query.order_by(Tournament.event_date.isnot(None).desc(), desc(Tournament.event_date))
        current_sort_by = 'event_date' # Ensure these are passed to template
        current_sort_order = 'desc'

    organized_tournaments = query.all()
    
    user_for_layout, is_logged_in_for_layout = _get_page_context_for_session_user()
    return render_template(
        'tournaments/my-tournaments.html',
        title="My Tournaments",
        organized_tournaments=organized_tournaments,
        is_logged_in=is_logged_in_for_layout,
        user=user_for_layout,
        current_sort_by=current_sort_by,       
        current_sort_order=current_sort_order,
        current_status_filter=status_filter 
    )

@tournaments_bp.route('/explore', methods=['GET'])
def public_tournament_list():
    """Displays a list of publicly available tournaments."""
    user_for_layout, is_logged_in_for_layout = _get_page_context_for_session_user()

    # Fetch tournaments that are active and have a public-friendly status
    # For V1, let's list 'Planned' and 'Active' tournaments
    public_statuses = ['Planned', 'Active']
    
    # Default sorting: by event date, newest first (nulls last if ascending, first if descending)
    # To ensure events without dates are listed consistently, handle NULLS
    # For descending (newest first), we want non-NULL dates first.
    query = Tournament.query_active().filter(
        Tournament.status.in_(public_statuses)
    ).order_by(
        Tournament.event_date.is_(None).asc(), # False (dates exist) before True (dates are NULL)
        desc(Tournament.event_date), 
        Tournament.name.asc()
    )
    
    tournaments_to_display = query.all()

    return render_template(
        'tournaments/public-tournament-list.html', # New template
        title="Explore Tournaments",
        tournaments=tournaments_to_display,
        is_logged_in=is_logged_in_for_layout,
        user=user_for_layout
    )

@tournaments_bp.route('/new', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
@custom_login_required
def create_tournament():
    user_id = session.get('user_id')
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
            return redirect(url_for('tournaments.list_my_tournaments'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating tournament for user ID {user_id}: {str(e)}", exc_info=True)
            flash('Error creating tournament: An unexpected error occurred.', 'danger')

    current_user_for_layout, is_logged_in_for_layout = _get_page_context_for_session_user()
    return render_template(
        'tournaments/create-tournament.html',
        title='Create New Tournament',
        form=form,
        is_logged_in=is_logged_in_for_layout,
        user=current_user_for_layout
    )

@tournaments_bp.route('/<int:tournament_id>')
def view_tournament(tournament_id):
    tournament = db.session.get(Tournament, tournament_id)
    user_for_layout, is_logged_in_for_layout = _get_page_context_for_session_user()
    
    is_organizer = False
    if is_logged_in_for_layout and tournament and session.get('user_id') == tournament.organizer_id:
        is_organizer = True

    # Check if tournament exists and is active (not soft-deleted)
    if not tournament or not tournament.is_active:
        current_app.logger.info(f"Public access: Tournament ID {tournament_id} not found or not active. Aborting with 404.")
        abort(404)

    # Define statuses that are publicly viewable for a detail page
    publicly_viewable_statuses = ['Planned', 'Active', 'Completed', 'Cancelled']
    
    # If the user is not the organizer, only show tournaments with public statuses
    if not is_organizer and tournament.status not in publicly_viewable_statuses:
        current_app.logger.info(f"Public access: Tournament ID {tournament_id} status '{tournament.status}' is not public. User not organizer. Aborting with 404.")
        abort(404)

    # Fetch participants if the tournament status is one where participants are relevant and public
    # Example: Show for Planned, Active, Completed. Not for Cancelled.
    participants_list = []
    if tournament.status in ['Planned', 'Active', 'Completed']:
        participants_list = tournament.participants.join(TournamentParticipant.user)\
                                .filter(TournamentParticipant.is_active == True, TournamentParticipant.dropped == False)\
                                .order_by(User.first_name.asc(), User.last_name.asc(), User.username.asc())\
                                .all()
                                # .options(db.joinedload(TournamentParticipant.user)) # Eager load user

    return render_template(
        'tournaments/view-tournament.html',
        title=tournament.name,
        tournament=tournament,
        is_logged_in=is_logged_in_for_layout,
        user=user_for_layout,
        is_organizer=is_organizer, # Pass this flag to the template
        participants_list=participants_list # Pass the list of participants
    )

@tournaments_bp.route('/<int:tournament_id>/settings', methods=['GET', 'POST'])
@custom_login_required
def tournament_settings(tournament_id):
    current_user_id = session.get('user_id')
    tournament = Tournament.query_active().filter_by(id=tournament_id).first()
    if not tournament:
        flash("Tournament not found or has been archived.", "danger")
        return redirect(url_for('tournaments.list_my_tournaments'))

    if tournament.organizer_id != current_user_id:
        flash("You are not authorized to edit this tournament's settings.", "danger")
        # Return 403 Forbidden instead of redirecting to list_my_tournaments
        # This makes it clearer why access is denied if they somehow got the URL
        abort(403) 

    form = TournamentSettingsForm(obj=tournament if request.method == 'GET' else None)

    if request.method == 'GET':
        # Ensure form.format_ (with underscore) is populated correctly
        if tournament.format:
            form.format_.data = tournament.format # Assuming form field is named format_

    if form.validate_on_submit():
        tournament.name = form.name.data
        tournament.description = form.description.data
        tournament.event_date = form.event_date.data
        tournament.format = form.format_.data # Assuming form field is named format_
        tournament.status = form.status.data
        tournament.pairing_system = form.pairing_system.data
        tournament.max_players = form.max_players.data
        
        try:
            db.session.commit()
            flash('Tournament settings updated successfully!', 'success')
            # Redirect back to settings page to see changes
            return redirect(url_for('tournaments.tournament_settings', tournament_id=tournament.id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating tournament {tournament.id} settings for user {current_user_id}: {e}", exc_info=True)
            flash('Error updating tournament settings. Please try again.', 'danger')
    elif request.method == 'POST' and not form.validate_on_submit():
        # This ensures that if validation fails on POST, errors are shown
        flash('Please correct the errors highlighted below.', 'warning')


    user_for_layout, is_logged_in_for_layout = _get_page_context_for_session_user()

    return render_template(
        'tournaments/tournament_settings.html',
        title=f"Settings for '{tournament.name}'",
        form=form,
        tournament=tournament,
        is_logged_in=is_logged_in_for_layout,
        user=user_for_layout
    )